import json
import time
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from app.config import get_settings

settings = get_settings()

class AIAnalyzer:
    """Analizador de IA para entrevistas de salida usando OpenAI GPT-4o mini"""
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            # Usar GPT-4o mini - excelente balance precio/calidad para análisis de texto
            self.model = "gpt-4o-mini"
        else:
            raise ValueError("OpenAI API key is required")
    
    def analyze_interview(self, transcript: str, employee_data: Dict = None) -> Dict:
        """
        Analiza el transcript de una entrevista de salida y extrae métricas e insights
        """
        start_time = time.time()
        
        # Prompt especializado para entrevistas de salida de IPS
        prompt = self._build_analysis_prompt(transcript, employee_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto analista de recursos humanos especializado en entrevistas de salida. Responde ÚNICAMENTE con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Baja temperatura para respuestas más consistentes
                max_tokens=2000
            )
            
            result = self._parse_ai_response(response.choices[0].message.content)
            
            processing_time = time.time() - start_time
            result['processing_time_seconds'] = processing_time
            result['ai_model_used'] = self.model
            
            return result
            
        except Exception as e:
            print(f"Error analyzing interview: {e}")
            return self._get_fallback_analysis(transcript)
    
    def _build_analysis_prompt(self, transcript: str, employee_data: Dict = None) -> str:
        """Construye el prompt para el análisis de IA"""
        
        employee_context = ""
        if employee_data:
            employee_context = f"""
Información del empleado:
- Departamento: {employee_data.get('department', 'No especificado')}
- Posición: {employee_data.get('position', 'No especificada')}  
- Tiempo en la empresa: {employee_data.get('tenure_months', 'No especificado')} meses
"""
        
        prompt = f"""
Eres un experto analista de recursos humanos especializado en entrevistas de salida para IPS (empresa de seguridad).

{employee_context}

TRANSCRIPT DE LA ENTREVISTA:
{transcript}

PREGUNTAS CLAVE QUE SE EVALÚAN EN IPS:
1. ¿Cuál es la razón principal por la que dejaste IPS?
2. ¿Recibiste apoyo de tu jefe y compañeros?, ¿Te sentiste valorado?
3. ¿Consideras que tuviste oportunidades de desarrollo y crecimiento en IPS?
4. ¿Qué podemos hacer para mejorar?

ANÁLISIS REQUERIDO:
Analiza el transcript y proporciona un análisis completo en formato JSON con la siguiente estructura:

{{
    "executive_summary": "Resumen ejecutivo de 2-3 párrafos para management",
    "detailed_summary": "Análisis detallado completo de la entrevista",
    "sentiment_score": float entre -1 y 1 (-1=muy negativo, 0=neutral, 1=muy positivo),
    "satisfaction_score": float entre 0 y 10 (satisfacción general del empleado),
    "retention_risk": float entre 0 y 1 (probabilidad de que otros empleados similares se vayan),
    "primary_reason": "Razón principal de salida en una frase",
    "secondary_reasons": ["lista", "de", "razones", "secundarias"],
    "answers_structured": {{
        "razon_principal": "respuesta específica",
        "apoyo_valoracion": "respuesta sobre apoyo y valoración",
        "desarrollo_crecimiento": "respuesta sobre oportunidades",
        "sugerencias_mejora": "sugerencias del empleado"
    }},
    "recommendations": [
        "Recomendación específica 1",
        "Recomendación específica 2"
    ],
    "action_items": [
        "Acción concreta 1 para implementar inmediatamente",
        "Acción concreta 2"
    ],
    "confidence_score": float entre 0 y 1 (confianza en el análisis),
    "key_quotes": ["Citas importantes del empleado"],
    "red_flags": ["Señales de alerta para la organización"],
    "positive_feedback": ["Aspectos positivos mencionados"]
}}

IMPORTANTE: 
- Responde ÚNICAMENTE con el JSON válido, sin texto adicional
- Asegúrate de que todos los valores numéricos estén entre los rangos especificados
- Identifica patrones que puedan indicar problemas sistémicos
- Proporciona recomendaciones accionables y específicas para IPS
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parsea la respuesta de la IA y la convierte a diccionario"""
        try:
            # Limpia la respuesta para extraer solo el JSON
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            result = json.loads(response_text)
            
            # Validaciones y valores por defecto
            result['sentiment_score'] = max(-1, min(1, result.get('sentiment_score', 0)))
            result['satisfaction_score'] = max(0, min(10, result.get('satisfaction_score', 5)))
            result['retention_risk'] = max(0, min(1, result.get('retention_risk', 0.5)))
            result['confidence_score'] = max(0, min(1, result.get('confidence_score', 0.7)))
            
            return result
            
        except json.JSONDecodeError:
            print(f"Error parsing AI response: {response_text}")
            return self._get_fallback_analysis("")
    
    def _get_fallback_analysis(self, transcript: str) -> Dict:
        """Análisis básico de respaldo en caso de error"""
        return {
            "executive_summary": "Análisis no disponible debido a error en procesamiento",
            "detailed_summary": f"Transcript original: {transcript[:500]}...",
            "sentiment_score": 0.0,
            "satisfaction_score": 5.0,
            "retention_risk": 0.5,
            "primary_reason": "No determinado",
            "secondary_reasons": [],
            "answers_structured": {
                "razon_principal": "No disponible",
                "apoyo_valoracion": "No disponible", 
                "desarrollo_crecimiento": "No disponible",
                "sugerencias_mejora": "No disponible"
            },
            "recommendations": ["Revisar transcript manualmente"],
            "action_items": ["Análisis manual requerido"],
            "confidence_score": 0.1,
            "key_quotes": [],
            "red_flags": ["Error en procesamiento automático"],
            "positive_feedback": [],
            "ai_model_used": "fallback",
            "processing_time_seconds": 0.1
        }

    def generate_aggregate_insights(self, analyses: List[Dict]) -> Dict:
        """Genera insights agregados de múltiples análisis"""
        if not analyses:
            return {}
        
        # Métricas agregadas
        total_interviews = len(analyses)
        avg_satisfaction = sum(a.get('satisfaction_score', 0) for a in analyses) / total_interviews
        avg_sentiment = sum(a.get('sentiment_score', 0) for a in analyses) / total_interviews
        avg_retention_risk = sum(a.get('retention_risk', 0) for a in analyses) / total_interviews
        
        # Razones principales más comunes
        reasons = [a.get('primary_reason', '') for a in analyses if a.get('primary_reason')]
        reason_counts = {}
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Distribución de riesgo de retención
        risk_distribution = {
            'bajo': len([a for a in analyses if a.get('retention_risk', 0) < 0.3]),
            'medio': len([a for a in analyses if 0.3 <= a.get('retention_risk', 0) < 0.7]),
            'alto': len([a for a in analyses if a.get('retention_risk', 0) >= 0.7])
        }
        
        return {
            'total_interviews': total_interviews,
            'avg_satisfaction': round(avg_satisfaction, 2),
            'avg_sentiment': round(avg_sentiment, 2),
            'avg_retention_risk': round(avg_retention_risk, 2),
            'top_reasons': top_reasons,
            'risk_distribution': risk_distribution,
            'generated_at': time.time()
        } 