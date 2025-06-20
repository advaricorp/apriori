import asyncio
import json
import time
import hmac
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from app.config import get_settings

settings = get_settings()

class ElevenLabsService:
    """Servicio para integración con ElevenLabs Conversational AI"""
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.webhook_secret = settings.elevenlabs_webhook_secret
        
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
    
    async def create_agent_for_followup(self, call_type: str, employee_data: Dict) -> str:
        """Crea un agente específico para el tipo de llamada de seguimiento"""
        
        agent_configs = {
            "exit_interview": {
                "name": "Entrevista de Salida IPS",
                "prompt": self._get_exit_interview_prompt(employee_data),
                "first_message": f"Hola {employee_data.get('name', '')}, soy Sofía de Recursos Humanos de IPS. Te llamo para realizar tu entrevista de salida como parte de nuestro proceso estándar. ¿Tienes unos minutos para conversar?",
                "evaluation_criteria": [
                    {
                        "name": "interview_completed",
                        "prompt": "Evalúa si se completaron todas las preguntas de la entrevista de salida"
                    },
                    {
                        "name": "sentiment_analysis", 
                        "prompt": "Analiza el sentimiento general del empleado durante la conversación"
                    }
                ],
                "data_collection": [
                    {
                        "identifier": "primary_reason",
                        "data_type": "String",
                        "description": "Razón principal por la que deja la empresa"
                    },
                    {
                        "identifier": "satisfaction_score",
                        "data_type": "Number", 
                        "description": "Score de satisfacción del 1-10 basado en las respuestas"
                    },
                    {
                        "identifier": "recommendations",
                        "data_type": "Array",
                        "description": "Lista de recomendaciones específicas del empleado"
                    }
                ]
            },
            "retention_check": {
                "name": "Consulta de Bienestar IPS",
                "prompt": self._get_retention_check_prompt(employee_data),
                "first_message": f"Hola {employee_data.get('name', '')}, soy Sofía de Recursos Humanos. Te llamo para saber cómo te sientes en tu trabajo y si hay algo en lo que podamos ayudarte. ¿Tienes unos minutos?",
                "evaluation_criteria": [
                    {
                        "name": "retention_risk",
                        "prompt": "Evalúa el riesgo de que el empleado considere dejar la empresa"
                    }
                ],
                "data_collection": [
                    {
                        "identifier": "satisfaction_level",
                        "data_type": "String",
                        "description": "Nivel de satisfacción: very_satisfied, satisfied, neutral, dissatisfied, very_dissatisfied"
                    },
                    {
                        "identifier": "concerns",
                        "data_type": "Array",
                        "description": "Lista de preocupaciones o problemas mencionados"
                    },
                    {
                        "identifier": "retention_risk",
                        "data_type": "String", 
                        "description": "Riesgo de rotación: low, medium, high"
                    }
                ]
            }
        }
        
        config = agent_configs.get(call_type, agent_configs["retention_check"])
        
        # Crear agente usando la API de ElevenLabs
        agent_data = {
            "name": config["name"],
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": config["prompt"]
                    },
                    "first_message": config["first_message"],
                    "language": "es"
                },
                "tts": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Voz por defecto
                }
            },
            "analysis": {
                "evaluation_criteria": config["evaluation_criteria"],
                "data_collection": config["data_collection"]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/convai/agents",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=agent_data
            )
            
            if response.status_code == 201:
                agent = response.json()
                return agent["agent_id"]
            else:
                raise Exception(f"Error creating agent: {response.text}")
    
    async def make_outbound_call(self, phone_number: str, agent_id: str, employee_data: Dict) -> Dict:
        """Realiza una llamada saliente usando ElevenLabs + Twilio"""
        
        call_data = {
            "agent_id": agent_id,
            "customer_phone_number": phone_number,
            "dynamic_variables": {
                "employee_name": employee_data.get('name', ''),
                "employee_department": employee_data.get('department', ''),
                "employee_position": employee_data.get('position', ''),
                "employee_tenure": str(employee_data.get('tenure_months', 0)),
                "manager_name": employee_data.get('manager_name', ''),
                "hire_date": employee_data.get('hire_date', '').strftime('%Y-%m-%d') if employee_data.get('hire_date') else ''
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/convai/phone/outbound-calls",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=call_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error making call: {response.text}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verifica la firma HMAC del webhook de ElevenLabs"""
        if not self.webhook_secret or not signature:
            return True  # Si no hay secret configurado, permitir
        
        try:
            # Extraer timestamp y hash de la firma
            elements = signature.split(',')
            timestamp = elements[0].split('=')[1]
            received_hash = elements[1].split('=')[1]
            
            # Validar timestamp (max 30 minutos)
            current_time = int(time.time())
            if abs(current_time - int(timestamp)) > 1800:
                return False
            
            # Calcular hash esperado
            payload_to_sign = f"{timestamp}.{payload.decode('utf-8')}"
            expected_hash = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload_to_sign.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(received_hash, expected_hash)
        except Exception:
            return False
    
    def _get_exit_interview_prompt(self, employee_data: Dict) -> str:
        """Genera prompt personalizado para entrevista de salida"""
        return f"""
Eres Sofía, una especialista en Recursos Humanos de IPS (empresa de seguridad). Tu trabajo es realizar entrevistas de salida profesionales y empáticas.

INFORMACIÓN DEL EMPLEADO:
- Nombre: {employee_data.get('name', 'N/A')}
- Departamento: {employee_data.get('department', 'N/A')}
- Posición: {employee_data.get('position', 'N/A')}
- Tiempo en la empresa: {employee_data.get('tenure_months', 0)} meses
- Manager: {employee_data.get('manager_name', 'N/A')}

OBJETIVO: Realizar una entrevista de salida completa y profesional.

PREGUNTAS OBLIGATORIAS que debes hacer:
1. ¿Cuál es la razón principal por la que dejaste IPS?
2. ¿Recibiste apoyo de tu jefe y compañeros? ¿Te sentiste valorado?
3. ¿Consideras que tuviste oportunidades de desarrollo y crecimiento en IPS?
4. ¿Qué podemos hacer para mejorar?

INSTRUCCIONES:
- Sé empática y profesional
- Haz las preguntas de forma natural, no como un cuestionario
- Escucha activamente y haz preguntas de seguimiento
- Toma nota de patrones y problemas sistémicos
- Agradece la honestidad del empleado
- Mantén un tono constructivo

IMPORTANTE: 
- No interrumpas mientras el empleado habla
- Si menciona problemas serios (acoso, discriminación), toma nota detallada
- Termina agradeciendo y deseándole éxito futuro
"""

    def _get_retention_check_prompt(self, employee_data: Dict) -> str:
        """Genera prompt personalizado para verificación de retención"""
        return f"""
Eres Sofía, especialista en Bienestar Laboral de IPS. Tu misión es detectar empleados en riesgo de rotación y ayudar proactivamente.

INFORMACIÓN DEL EMPLEADO:
- Nombre: {employee_data.get('name', 'N/A')}
- Departamento: {employee_data.get('department', 'N/A')}
- Posición: {employee_data.get('position', 'N/A')}
- Tiempo en la empresa: {employee_data.get('tenure_months', 0)} meses
- Manager: {employee_data.get('manager_name', 'N/A')}

OBJETIVO: Identificar problemas antes de que el empleado considere irse.

ÁREAS A EXPLORAR:
1. Satisfacción general con el trabajo
2. Relación con el supervisor y equipo
3. Carga de trabajo y balance vida-trabajo
4. Oportunidades de crecimiento
5. Reconocimiento y compensación
6. Ambiente laboral

SEÑALES DE ALERTA:
- Menciona buscar otros trabajos
- Se queja de la carga de trabajo
- Problemas con el supervisor
- Falta de reconocimiento
- Problemas familiares que afecten el trabajo

INSTRUCCIONES:
- Sé genuinamente interesada en su bienestar
- Haz preguntas abiertas
- Ofrece soluciones o escalación cuando sea apropiado
- No prometas cosas que no puedes cumplir
- Si detectas riesgo alto, sugiere reunión con RH

IMPORTANTE:
- Esta NO es una evaluación de desempeño
- Es una conversación de apoyo y mejora
- Mantén confidencialidad
- Documenta problemas sistémicos
"""

    async def get_conversation_data(self, conversation_id: str) -> Dict:
        """Obtiene datos completos de una conversación"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/convai/conversations/{conversation_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error getting conversation: {response.text}")

    async def schedule_batch_calls(self, employees: List[Dict], call_type: str) -> List[Dict]:
        """Programa llamadas en lote para múltiples empleados"""
        results = []
        
        for employee in employees:
            try:
                # Crear agente específico para este empleado
                agent_id = await self.create_agent_for_followup(call_type, employee)
                
                # Programar llamada
                call_result = await self.make_outbound_call(
                    employee['phone'], 
                    agent_id, 
                    employee
                )
                
                results.append({
                    "employee_id": employee['employee_id'],
                    "status": "scheduled",
                    "conversation_id": call_result.get('conversation_id'),
                    "agent_id": agent_id
                })
                
                # Pequeña pausa entre llamadas para no sobrecargar
                await asyncio.sleep(2)
                
            except Exception as e:
                results.append({
                    "employee_id": employee['employee_id'],
                    "status": "error",
                    "error": str(e)
                })
        
        return results 