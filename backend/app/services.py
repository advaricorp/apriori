import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models import Interview, Analysis, InterviewCreate
from app.ai_analyzer import AIAnalyzer
from datetime import datetime, timedelta


class InterviewService:
    """Servicio para manejar entrevistas y análisis"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_analyzer = AIAnalyzer()
    
    async def create_interview_from_webhook(self, webhook_data: dict) -> Interview:
        """Crea una nueva entrevista desde el webhook de ElevenLabs"""
        
        # Extraer metadatos adicionales si están disponibles
        metadata = webhook_data.get('metadata', {})
        
        interview_data = InterviewCreate(
            conversation_id=webhook_data['conversation_id'],
            agent_id=webhook_data['agent_id'],
            transcript=webhook_data['transcript'],
            duration_seconds=webhook_data['duration_seconds'],
            audio_url=webhook_data.get('audio_url'),
            employee_id=metadata.get('employee_id'),
            department=metadata.get('department'),
            position=metadata.get('position'),
            tenure_months=metadata.get('tenure_months')
        )
        
        # Crear registro en base de datos
        db_interview = Interview(**interview_data.dict())
        self.db.add(db_interview)
        self.db.commit()
        self.db.refresh(db_interview)
        
        # Procesar análisis de IA de forma asíncrona
        asyncio.create_task(self._process_interview_analysis(db_interview.id))
        
        return db_interview
    
    async def _process_interview_analysis(self, interview_id: int):
        """Procesa el análisis de IA para una entrevista"""
        try:
            # Obtener entrevista
            interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return
            
            # Actualizar estado
            interview.processing_status = "processing"
            self.db.commit()
            
            # Preparar datos del empleado para contexto
            employee_data = {
                'department': interview.department,
                'position': interview.position,
                'tenure_months': interview.tenure_months
            }
            
            # Ejecutar análisis de IA
            analysis_result = self.ai_analyzer.analyze_interview(
                interview.transcript, 
                employee_data
            )
            
            # Crear registro de análisis
            analysis = Analysis(
                interview_id=interview.id,
                executive_summary=analysis_result.get('executive_summary'),
                detailed_summary=analysis_result.get('detailed_summary'),
                sentiment_score=analysis_result.get('sentiment_score'),
                satisfaction_score=analysis_result.get('satisfaction_score'),
                retention_risk=analysis_result.get('retention_risk'),
                primary_reason=analysis_result.get('primary_reason'),
                secondary_reasons=analysis_result.get('secondary_reasons'),
                answers_structured=analysis_result.get('answers_structured'),
                recommendations=analysis_result.get('recommendations'),
                action_items=analysis_result.get('action_items'),
                ai_model_used=analysis_result.get('ai_model_used'),
                confidence_score=analysis_result.get('confidence_score'),
                processing_time_seconds=analysis_result.get('processing_time_seconds')
            )
            
            self.db.add(analysis)
            
            # Actualizar estado de la entrevista
            interview.is_processed = True
            interview.processing_status = "completed"
            interview.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error processing analysis for interview {interview_id}: {e}")
            # Actualizar estado de error
            interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
            if interview:
                interview.processing_status = "error"
                self.db.commit()
    
    def get_interview_by_id(self, interview_id: int) -> Optional[Interview]:
        """Obtiene una entrevista por ID"""
        return self.db.query(Interview).filter(Interview.id == interview_id).first()
    
    def get_interviews(self, skip: int = 0, limit: int = 100) -> List[Interview]:
        """Obtiene lista de entrevistas"""
        return self.db.query(Interview).order_by(desc(Interview.created_at)).offset(skip).limit(limit).all()
    
    def get_analysis_by_interview_id(self, interview_id: int) -> Optional[Analysis]:
        """Obtiene análisis por ID de entrevista"""
        return self.db.query(Analysis).filter(Analysis.interview_id == interview_id).first()
    
    def get_dashboard_metrics(self, days: int = 30) -> Dict:
        """Genera métricas para el dashboard"""
        # Fecha límite
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Consultas básicas
        total_interviews = self.db.query(Interview).filter(
            Interview.created_at >= since_date
        ).count()
        
        # Métricas de análisis
        analyses = self.db.query(Analysis).join(Interview).filter(
            Interview.created_at >= since_date
        ).all()
        
        if not analyses:
            return {
                "total_interviews": total_interviews,
                "avg_satisfaction": 0,
                "top_reasons": [],
                "retention_risk_distribution": {"bajo": 0, "medio": 0, "alto": 0},
                "monthly_trends": [],
                "department_breakdown": {}
            }
        
        # Calcular métricas agregadas
        avg_satisfaction = sum(a.satisfaction_score for a in analyses if a.satisfaction_score) / len(analyses)
        
        # Top razones
        reasons = [a.primary_reason for a in analyses if a.primary_reason]
        reason_counts = {}
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Distribución de riesgo
        risk_distribution = {
            "bajo": len([a for a in analyses if a.retention_risk and a.retention_risk < 0.3]),
            "medio": len([a for a in analyses if a.retention_risk and 0.3 <= a.retention_risk < 0.7]),
            "alto": len([a for a in analyses if a.retention_risk and a.retention_risk >= 0.7])
        }
        
        # Breakdown por departamento
        dept_breakdown = {}
        interviews_with_dept = self.db.query(Interview).filter(
            Interview.created_at >= since_date,
            Interview.department.isnot(None)
        ).all()
        
        for interview in interviews_with_dept:
            dept = interview.department
            if dept not in dept_breakdown:
                dept_breakdown[dept] = {"count": 0, "avg_satisfaction": 0}
            dept_breakdown[dept]["count"] += 1
        
        # Calcular satisfacción promedio por departamento
        for dept in dept_breakdown:
            dept_analyses = [a for a in analyses if a.interview.department == dept]
            if dept_analyses:
                dept_breakdown[dept]["avg_satisfaction"] = sum(
                    a.satisfaction_score for a in dept_analyses if a.satisfaction_score
                ) / len(dept_analyses)
        
        return {
            "total_interviews": total_interviews,
            "avg_satisfaction": round(avg_satisfaction, 2),
            "top_reasons": top_reasons,
            "retention_risk_distribution": risk_distribution,
            "department_breakdown": dept_breakdown,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def search_interviews(self, query: str, limit: int = 50) -> List[Interview]:
        """Busca entrevistas por texto en transcript"""
        return self.db.query(Interview).filter(
            Interview.transcript.contains(query)
        ).order_by(desc(Interview.created_at)).limit(limit).all()
    
    def get_interviews_by_department(self, department: str) -> List[Interview]:
        """Obtiene entrevistas por departamento"""
        return self.db.query(Interview).filter(
            Interview.department == department
        ).order_by(desc(Interview.created_at)).all()
    
    def get_high_risk_interviews(self, risk_threshold: float = 0.7) -> List[Interview]:
        """Obtiene entrevistas con alto riesgo de retención"""
        return self.db.query(Interview).join(Analysis).filter(
            Analysis.retention_risk >= risk_threshold
        ).order_by(desc(Analysis.retention_risk)).all() 