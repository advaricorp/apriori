from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
import uuid

Base = declarative_base()


class Organization(Base):
    """Tabla para multitenancy - cada organización es un tenant"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Settings específicos de la organización
    settings = Column(JSON, default={})
    
    # Relaciones
    users = relationship("User", back_populates="organization")
    interviews = relationship("Interview", back_populates="organization")
    employees = relationship("Employee", back_populates="organization")


class User(Base):
    """Usuarios del sistema con multitenancy"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Multitenancy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(String(50), default="user")  # admin, manager, user
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relaciones
    organization = relationship("Organization", back_populates="users")


class Interview(Base):
    """Modelo de entrevista de salida"""
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    # Datos de ElevenLabs
    conversation_id = Column(String, unique=True, index=True)
    agent_id = Column(String)
    transcript = Column(Text)
    duration_seconds = Column(Integer)
    audio_url = Column(String)
    
    # Metadatos
    employee_id = Column(String, index=True)
    department = Column(String)
    position = Column(String)
    tenure_months = Column(Integer)
    
    # Timestamps
    interview_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Estado de procesamiento
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, error

    # Multitenancy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Webhook info
    webhook_received_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_webhook_data = Column(JSON)
    
    # Relaciones
    organization = relationship("Organization", back_populates="interviews")
    employee = relationship("Employee", back_populates="interviews")
    analysis = relationship("Analysis", back_populates="interview", uselist=False)


class Analysis(Base):
    """Análisis de IA de la entrevista"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, index=True)
    
    # Resúmenes
    executive_summary = Column(Text)  # Para el frontend/management
    detailed_summary = Column(Text)   # Análisis completo
    
    # Métricas y scores
    sentiment_score = Column(Float)  # -1 a 1
    satisfaction_score = Column(Float)  # 0 a 10
    retention_risk = Column(Float)  # 0 a 1
    
    # Categorización automática
    primary_reason = Column(String)  # Razón principal de salida
    secondary_reasons = Column(JSON)  # Lista de razones secundarias
    
    # Respuestas a preguntas específicas
    answers_structured = Column(JSON)  # Respuestas estructuradas
    
    # Recomendaciones
    recommendations = Column(JSON)  # Lista de recomendaciones
    action_items = Column(JSON)  # Acciones específicas
    
    # Metadatos del análisis
    ai_model_used = Column(String)
    confidence_score = Column(Float)
    processing_time_seconds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Multitenancy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relaciones
    interview = relationship("Interview", back_populates="analysis")


# Pydantic models para API
class WebhookPayload(BaseModel):
    """Payload del webhook de ElevenLabs"""
    conversation_id: str
    agent_id: str
    transcript: str
    duration_seconds: int
    audio_url: Optional[str] = None
    metadata: Optional[dict] = None


class InterviewCreate(BaseModel):
    """Modelo para crear entrevista"""
    conversation_id: str
    agent_id: str
    transcript: str
    duration_seconds: int
    audio_url: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    tenure_months: Optional[int] = None


class InterviewResponse(BaseModel):
    """Respuesta de entrevista"""
    id: int
    conversation_id: str
    employee_id: Optional[str]
    department: Optional[str]
    position: Optional[str]
    interview_date: datetime
    is_processed: bool
    processing_status: str
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Respuesta de análisis"""
    id: int
    interview_id: int
    executive_summary: str
    sentiment_score: float
    satisfaction_score: float
    retention_risk: float
    primary_reason: str
    recommendations: list
    action_items: list
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    """Métricas para el dashboard"""
    total_interviews: int
    avg_satisfaction: float
    top_reasons: list
    retention_risk_distribution: dict
    monthly_trends: list
    department_breakdown: dict


# Nuevos modelos para el sistema de seguimiento
class Employee(Base):
    """Modelo de empleado con información de contacto"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    phone = Column(String, index=True)  # Número de celular principal
    department = Column(String, index=True)
    position = Column(String)
    hire_date = Column(DateTime)
    manager_id = Column(String)
    
    # Estado del empleado
    status = Column(String, default="active")  # active, exit_interview_pending, exited
    exit_date = Column(DateTime, nullable=True)
    
    # Preferencias de contacto
    preferred_contact_time = Column(String)  # morning, afternoon, evening
    time_zone = Column(String, default="America/Mexico_City")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Multitenancy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relaciones
    organization = relationship("Organization", back_populates="employees")
    interviews = relationship("Interview", back_populates="employee")
    followup_calls = relationship("FollowUpCall", back_populates="employee")
    profiles = relationship("EmployeeProfile", back_populates="employee")


class FollowUpCall(Base):
    """Llamadas de seguimiento programadas y realizadas"""
    __tablename__ = "followup_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True)
    interview_id = Column(Integer, nullable=True)  # Puede ser null para llamadas preventivas
    
    # Información de la llamada
    call_type = Column(String)  # exit_interview, retention_check, 7_day_followup, 14_day_followup
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    
    # Datos de ElevenLabs
    conversation_id = Column(String, nullable=True)
    agent_id = Column(String)
    call_duration_seconds = Column(Integer, nullable=True)
    call_status = Column(String, default="scheduled")  # scheduled, completed, failed, cancelled
    
    # Resultados
    transcript = Column(Text, nullable=True)
    call_successful = Column(Boolean, default=False)
    needs_human_followup = Column(Boolean, default=False)
    retention_risk_level = Column(String, nullable=True)  # low, medium, high
    
    # Metadatos
    elevenlabs_cost = Column(Float, nullable=True)
    twilio_cost = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Multitenancy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relaciones
    employee = relationship("Employee", back_populates="followup_calls")
    organization = relationship("Organization")


class EmployeeProfile(Base):
    """Perfil detallado del empleado para personalización de llamadas"""
    __tablename__ = "employee_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True)
    
    # Historial de interacciones
    previous_feedback = Column(JSON)  # Feedback de entrevistas anteriores
    satisfaction_history = Column(JSON)  # Historial de satisfacción
    concerns_mentioned = Column(JSON)  # Preocupaciones mencionadas previamente
    
    # Información contextual para ElevenLabs
    personality_notes = Column(Text)  # Notas sobre personalidad/estilo de comunicación
    communication_preferences = Column(JSON)  # Preferencias de comunicación
    sensitive_topics = Column(JSON)  # Temas sensibles a evitar
    
    # Datos del manager/equipo
    manager_name = Column(String)
    team_dynamics = Column(Text)
    recent_projects = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Multitenancy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relaciones
    employee = relationship("Employee", back_populates="profiles")


# Modelos Pydantic para API
class EmployeeCreate(BaseModel):
    """Modelo para crear empleado"""
    employee_id: str
    name: str
    email: str
    phone: str
    department: str
    position: str
    hire_date: datetime
    manager_id: Optional[str] = None
    preferred_contact_time: Optional[str] = "afternoon"
    time_zone: str = "America/Mexico_City"


class EmployeeResponse(BaseModel):
    """Respuesta de empleado"""
    id: int
    employee_id: str
    name: str
    email: str
    phone: str
    department: str
    position: str
    status: str
    hire_date: datetime
    
    class Config:
        from_attributes = True


class FollowUpCallCreate(BaseModel):
    """Modelo para crear llamada de seguimiento"""
    employee_id: str
    call_type: str
    scheduled_date: datetime
    agent_id: str


class FollowUpCallResponse(BaseModel):
    """Respuesta de llamada de seguimiento"""
    id: int
    employee_id: str
    call_type: str
    scheduled_date: datetime
    call_status: str
    retention_risk_level: Optional[str]
    needs_human_followup: bool
    
    class Config:
        from_attributes = True


# Índices adicionales para performance
Index('idx_interviews_org_created', Interview.organization_id, Interview.created_at)
Index('idx_employees_org_active', Employee.organization_id, Employee.termination_date)
Index('idx_followup_org_scheduled', FollowUpCall.organization_id, FollowUpCall.scheduled_for)
Index('idx_users_org_active', User.organization_id, User.is_active) 