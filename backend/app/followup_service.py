import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import get_db
from app.models import Employee, FollowUpCall, EmployeeProfile, Interview, Analysis
from app.elevenlabs_service import ElevenLabsService
from app.ai_analyzer import AIAnalyzer
import logging

logger = logging.getLogger(__name__)

class FollowUpService:
    """Servicio para gestión de llamadas de seguimiento proactivas"""
    
    def __init__(self):
        self.elevenlabs = ElevenLabsService()
        self.ai_analyzer = AIAnalyzer()
    
    async def create_employee_profile(self, db: Session, employee_data: Dict) -> str:
        """Crea perfil de empleado con información personalizada"""
        
        profile = EmployeeProfile(
            employee_id=employee_data['employee_id'],
            previous_feedback=[],
            satisfaction_history=[],
            concerns_mentioned=[],
            personality_notes=employee_data.get('personality_notes', ''),
            communication_preferences=employee_data.get('communication_preferences', {}),
            sensitive_topics=employee_data.get('sensitive_topics', []),
            manager_name=employee_data.get('manager_name', ''),
            team_dynamics=employee_data.get('team_dynamics', ''),
            recent_projects=employee_data.get('recent_projects', [])
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        return profile.employee_id
    
    async def identify_at_risk_employees(self, db: Session) -> List[Dict]:
        """Identifica empleados en riesgo de rotación para llamadas proactivas"""
        
        at_risk_employees = []
        
        # Empleados nuevos (30-90 días) para onboarding check
        new_employees = db.query(Employee).filter(
            and_(
                Employee.hire_date >= datetime.utcnow() - timedelta(days=90),
                Employee.hire_date <= datetime.utcnow() - timedelta(days=30),
                Employee.status == 'active'
            )
        ).all()
        
        for emp in new_employees:
            at_risk_employees.append({
                'employee_id': emp.employee_id,
                'name': emp.name,
                'department': emp.department,
                'risk_level': 'medium',
                'reason': 'New employee onboarding check',
                'phone': emp.phone,
                'preferred_contact_time': emp.preferred_contact_time,
                'tenure_months': (datetime.utcnow() - emp.hire_date).days // 30
            })
        
        return at_risk_employees
    
    async def schedule_proactive_calls(self, db: Session, call_type: str = "retention_check") -> Dict:
        """Programa llamadas proactivas para empleados identificados"""
        
        at_risk_employees = await self.identify_at_risk_employees(db)
        
        if not at_risk_employees:
            return {"message": "No employees identified for proactive calls", "scheduled": 0}
        
        scheduled_calls = []
        
        for employee in at_risk_employees:
            try:
                # Verificar si ya tiene una llamada programada reciente
                existing_call = db.query(FollowUpCall).filter(
                    and_(
                        FollowUpCall.employee_id == employee['employee_id'],
                        FollowUpCall.scheduled_date >= datetime.utcnow() - timedelta(days=30),
                        FollowUpCall.call_status.in_(['scheduled', 'completed'])
                    )
                ).first()
                
                if existing_call:
                    continue  # Skip si ya tiene llamada reciente
                
                # Obtener perfil del empleado para personalización
                profile = db.query(EmployeeProfile).filter(
                    EmployeeProfile.employee_id == employee['employee_id']
                ).first()
                
                # Enriquecer datos del empleado
                employee_data = {
                    **employee,
                    'manager_name': profile.manager_name if profile else '',
                    'previous_concerns': profile.concerns_mentioned if profile else [],
                    'communication_style': profile.personality_notes if profile else ''
                }
                
                # Crear agente específico en ElevenLabs
                agent_id = await self.elevenlabs.create_agent_for_followup(call_type, employee_data)
                
                # Calcular hora óptima para llamar
                preferred_time = self._calculate_optimal_call_time(employee['preferred_contact_time'])
                
                # Crear registro de llamada programada
                followup_call = FollowUpCall(
                    employee_id=employee['employee_id'],
                    call_type=call_type,
                    scheduled_date=preferred_time,
                    agent_id=agent_id,
                    call_status='scheduled'
                )
                
                db.add(followup_call)
                scheduled_calls.append({
                    'employee_id': employee['employee_id'],
                    'name': employee['name'],
                    'scheduled_time': preferred_time.isoformat(),
                    'risk_level': employee['risk_level']
                })
                
            except Exception as e:
                logger.error(f"Error scheduling call for {employee['employee_id']}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            "message": f"Scheduled {len(scheduled_calls)} proactive calls",
            "scheduled": len(scheduled_calls),
            "calls": scheduled_calls
        }
    
    async def execute_scheduled_calls(self, db: Session) -> Dict:
        """Ejecuta las llamadas programadas que están listas"""
        
        # Obtener llamadas programadas para ejecutar (en las próximas 2 horas)
        upcoming_calls = db.query(FollowUpCall).filter(
            and_(
                FollowUpCall.call_status == 'scheduled',
                FollowUpCall.scheduled_date <= datetime.utcnow() + timedelta(hours=2),
                FollowUpCall.scheduled_date >= datetime.utcnow() - timedelta(minutes=30)
            )
        ).all()
        
        executed_calls = []
        
        for call in upcoming_calls:
            try:
                # Obtener datos del empleado
                employee = db.query(Employee).filter(
                    Employee.employee_id == call.employee_id
                ).first()
                
                if not employee or employee.status != 'active':
                    call.call_status = 'cancelled'
                    continue
                
                # Obtener perfil para personalización
                profile = db.query(EmployeeProfile).filter(
                    EmployeeProfile.employee_id == employee.employee_id
                ).first()
                
                employee_data = {
                    'employee_id': employee.employee_id,
                    'name': employee.name,
                    'department': employee.department,
                    'position': employee.position,
                    'phone': employee.phone,
                    'manager_name': profile.manager_name if profile else '',
                    'tenure_months': (datetime.utcnow() - employee.hire_date).days // 30,
                    'hire_date': employee.hire_date
                }
                
                # Ejecutar llamada con ElevenLabs
                call_result = await self.elevenlabs.make_outbound_call(
                    employee.phone,
                    call.agent_id,
                    employee_data
                )
                
                # Actualizar registro
                call.conversation_id = call_result.get('conversation_id')
                call.call_status = 'in_progress'
                
                executed_calls.append({
                    'employee_id': employee.employee_id,
                    'name': employee.name,
                    'conversation_id': call.conversation_id,
                    'status': 'initiated'
                })
                
                # Pequeña pausa entre llamadas
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error executing call for {call.employee_id}: {str(e)}")
                call.call_status = 'failed'
                continue
        
        db.commit()
        
        return {
            "message": f"Executed {len(executed_calls)} calls",
            "executed": len(executed_calls),
            "calls": executed_calls
        }
    
    async def process_followup_webhook(self, db: Session, webhook_data: Dict) -> Dict:
        """Procesa webhook de ElevenLabs para llamadas de seguimiento"""
        
        conversation_id = webhook_data['data']['conversation_id']
        
        # Buscar la llamada de seguimiento
        followup_call = db.query(FollowUpCall).filter(
            FollowUpCall.conversation_id == conversation_id
        ).first()
        
        if not followup_call:
            return {"error": "Follow-up call not found"}
        
        # Actualizar datos de la llamada
        call_data = webhook_data['data']
        analysis = call_data.get('analysis', {})
        
        followup_call.completed_date = datetime.utcnow()
        followup_call.call_status = 'completed'
        followup_call.call_duration_seconds = call_data['metadata']['call_duration_secs']
        followup_call.call_successful = analysis.get('call_successful') == 'success'
        followup_call.elevenlabs_cost = call_data['metadata'].get('cost', 0)
        
        # Extraer transcript
        transcript_parts = []
        for turn in call_data.get('transcript', []):
            transcript_parts.append(f"{turn['role']}: {turn['message']}")
        followup_call.transcript = "\n".join(transcript_parts)
        
        # Analizar resultados específicos del tipo de llamada
        data_collection = analysis.get('data_collection_results', {})
        
        if followup_call.call_type == 'retention_check':
            # Analizar riesgo de retención
            retention_risk = data_collection.get('retention_risk', {}).get('value', 'unknown')
            followup_call.retention_risk_level = retention_risk
            
            # Determinar si necesita seguimiento humano
            satisfaction = data_collection.get('satisfaction_level', {}).get('value', '')
            concerns = data_collection.get('concerns', {}).get('value', [])
            
            followup_call.needs_human_followup = (
                retention_risk == 'high' or 
                satisfaction in ['dissatisfied', 'very_dissatisfied'] or
                len(concerns) > 2
            )
            
        elif followup_call.call_type == 'exit_interview':
            # Procesar entrevista de salida
            primary_reason = data_collection.get('primary_reason', {}).get('value', '')
            satisfaction_score = data_collection.get('satisfaction_score', {}).get('value', 0)
            recommendations = data_collection.get('recommendations', {}).get('value', [])
            
            # Crear análisis usando OpenAI
            analysis_result = self.ai_analyzer.analyze_interview(
                followup_call.transcript,
                {"employee_id": followup_call.employee_id}
            )
            
            # Crear registro de Interview y Analysis en la base de datos
            interview = Interview(
                employee_name=db.query(Employee).filter(
                    Employee.employee_id == followup_call.employee_id
                ).first().name,
                employee_id=followup_call.employee_id,
                phone_number=db.query(Employee).filter(
                    Employee.employee_id == followup_call.employee_id
                ).first().phone,
                conversation_id=conversation_id,
                transcript=followup_call.transcript,
                call_duration=followup_call.call_duration_seconds,
                interview_type="exit_followup"
            )
            db.add(interview)
            db.flush()
            
            analysis_record = Analysis(
                interview_id=interview.id,
                sentiment_score=analysis_result.get('sentiment_score', 3),
                satisfaction_score=satisfaction_score or analysis_result.get('satisfaction_score', 3),
                retention_risk=analysis_result.get('retention_risk', 'medium'),
                primary_reasons=analysis_result.get('primary_reasons', [primary_reason] if primary_reason else []),
                recommendations=recommendations or analysis_result.get('recommendations', []),
                key_insights=analysis_result.get('key_insights', []),
                department_issues=analysis_result.get('department_issues', []),
                executive_summary=analysis_result.get('executive_summary', ''),
                detailed_analysis=analysis_result.get('detailed_analysis', ''),
                ai_model_used=analysis_result.get('ai_model_used', 'gpt-4o-mini'),
                processing_time_seconds=analysis_result.get('processing_time_seconds', 0)
            )
            db.add(analysis_record)
        
        # Actualizar perfil del empleado con nueva información
        profile = db.query(EmployeeProfile).filter(
            EmployeeProfile.employee_id == followup_call.employee_id
        ).first()
        
        if profile:
            # Agregar nuevas preocupaciones
            if 'concerns' in data_collection:
                new_concerns = data_collection['concerns'].get('value', [])
                if new_concerns:
                    existing_concerns = profile.concerns_mentioned or []
                    profile.concerns_mentioned = list(set(existing_concerns + new_concerns))
            
            # Actualizar historial de satisfacción
            if 'satisfaction_level' in data_collection or 'satisfaction_score' in data_collection:
                satisfaction_history = profile.satisfaction_history or []
                satisfaction_entry = {
                    'date': datetime.utcnow().isoformat(),
                    'level': data_collection.get('satisfaction_level', {}).get('value'),
                    'score': data_collection.get('satisfaction_score', {}).get('value'),
                    'call_type': followup_call.call_type
                }
                satisfaction_history.append(satisfaction_entry)
                profile.satisfaction_history = satisfaction_history[-10:]  # Mantener últimos 10
        
        db.commit()
        
        return {
            "message": "Follow-up call processed successfully",
            "call_id": followup_call.id,
            "retention_risk": followup_call.retention_risk_level,
            "needs_followup": followup_call.needs_human_followup
        }
    
    def _calculate_optimal_call_time(self, preferred_time: str) -> datetime:
        """Calcula la hora óptima para realizar la llamada"""
        now = datetime.utcnow()
        
        # Mapear preferencias a horas específicas
        time_mappings = {
            'morning': 9,    # 9 AM
            'afternoon': 14, # 2 PM  
            'evening': 17    # 5 PM
        }
        
        target_hour = time_mappings.get(preferred_time, 14)
        
        # Programar para el siguiente día hábil
        target_date = now + timedelta(days=1)
        
        # Evitar fines de semana
        while target_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            target_date += timedelta(days=1)
        
        return target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    
    async def get_followup_analytics(self, db: Session) -> Dict:
        """Obtiene analytics de las llamadas de seguimiento"""
        
        # Estadísticas generales
        total_calls = db.query(FollowUpCall).count()
        completed_calls = db.query(FollowUpCall).filter(
            FollowUpCall.call_status == 'completed'
        ).count()
        
        successful_calls = db.query(FollowUpCall).filter(
            FollowUpCall.call_successful == True
        ).count()
        
        # Riesgo de retención por nivel
        retention_risk_stats = db.query(FollowUpCall.retention_risk_level).filter(
            FollowUpCall.retention_risk_level.isnot(None)
        ).all()
        
        risk_distribution = {}
        for (risk_level,) in retention_risk_stats:
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Llamadas que necesitan seguimiento humano
        human_followup_needed = db.query(FollowUpCall).filter(
            FollowUpCall.needs_human_followup == True
        ).count()
        
        return {
            "total_calls": total_calls,
            "completed_calls": completed_calls,
            "success_rate": (successful_calls / completed_calls * 100) if completed_calls > 0 else 0,
            "retention_risk_distribution": risk_distribution,
            "human_followup_needed": human_followup_needed,
            "completion_rate": (completed_calls / total_calls * 100) if total_calls > 0 else 0
        } 