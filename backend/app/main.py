from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import asyncio

from app.config import get_settings
from app.database import get_db, create_tables
from app.models import *
from app.auth import *
from app.ai_analyzer import AIAnalyzer
from app.elevenlabs_service import ElevenLabsService
from app.followup_service import FollowUpService
from pydantic import BaseModel, EmailStr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Sistema de análisis de entrevistas de salida con IA y llamadas proactivas",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_analyzer = AIAnalyzer()
elevenlabs_service = ElevenLabsService()
followup_service = FollowUpService()

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info("🚀 Apriori Backend started successfully!")

# Pydantic models for API
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    organization_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict
    organization: dict

class InterviewResponse(BaseModel):
    id: int
    transcript: str
    status: str
    created_at: datetime
    analysis: Optional[dict] = None

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication routes
@app.post("/auth/login", response_model=Token)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get JWT token"""
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
        
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        },
        organization={
            "id": user.organization.id,
            "name": user.organization.name,
            "slug": user.organization.slug
        }
    )

@app.post("/auth/register", response_model=Token)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new user and organization"""
    # Check if organization exists or create new one
    org_name = request.organization_name or f"{request.username}'s Organization"
    org_slug = org_name.lower().replace(" ", "-").replace("'", "")
    
    organization = db.query(Organization).filter(Organization.slug == org_slug).first()
    if not organization:
        organization = Organization(
            name=org_name,
            slug=org_slug,
            domain=f"{org_slug}.apriori.enkisys.com",
            is_active=True
        )
        db.add(organization)
        db.commit()
        db.refresh(organization)
    
    # Create user
    user = create_user(
        db=db,
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
        organization_id=organization.id,
        role="admin"  # First user is admin
    )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        },
        organization={
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug
        }
    )

# Protected routes
@app.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "last_login": current_user.last_login
        },
        "organization": {
            "id": current_user.organization.id,
            "name": current_user.organization.name,
            "slug": current_user.organization.slug
        }
    }

# ElevenLabs Webhook - Main webhook for exit interviews
@app.post("/webhook/elevenlabs")
async def elevenlabs_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Receive ElevenLabs webhook for exit interviews"""
    # Get raw body and headers
    body = await request.body()
    headers = dict(request.headers)
    
    # Log webhook
    webhook_log = WebhookLog(
        webhook_type="elevenlabs_exit",
        source_ip=request.client.host,
        user_agent=headers.get("user-agent", ""),
        payload=await request.json(),
        headers=headers,
        status="received"
    )
    db.add(webhook_log)
    db.commit()
    
    try:
        # Process webhook
        conversation_data = webhook_log.payload
        
        # Create interview record
        interview = Interview(
            elevenlabs_conversation_id=conversation_data.get("conversation_id"),
            phone_number=conversation_data.get("phone_number"),
            duration_seconds=conversation_data.get("duration_seconds"),
            transcript=conversation_data.get("transcript"),
            audio_url=conversation_data.get("audio_url"),
            status="received",
            raw_webhook_data=conversation_data,
            organization_id=1  # Default org for now, should resolve from webhook data
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        # Process analysis in background
        background_tasks.add_task(process_interview_analysis, interview.id)
        
        webhook_log.status = "processed"
        webhook_log.related_interview_id = interview.id
        webhook_log.processed_at = datetime.utcnow()
        db.commit()
        
        return {"status": "success", "interview_id": interview.id}
        
    except Exception as e:
        webhook_log.status = "error"
        webhook_log.error_message = str(e)
        db.commit()
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Error processing webhook")

async def process_interview_analysis(interview_id: int):
    """Background task to analyze interview"""
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return
        
        interview.status = "processing"
        db.commit()
        
        # Run AI analysis
        analysis_result = ai_analyzer.analyze_interview(interview.transcript)
        
        # Save analysis
        analysis = Analysis(
            interview_id=interview.id,
            executive_summary=analysis_result.get("executive_summary"),
            detailed_summary=analysis_result.get("detailed_summary"),
            sentiment_score=analysis_result.get("sentiment_score"),
            satisfaction_score=analysis_result.get("satisfaction_score"),
            retention_risk=analysis_result.get("retention_risk"),
            confidence_score=analysis_result.get("confidence_score"),
            primary_reason=analysis_result.get("primary_reason"),
            secondary_reasons=analysis_result.get("secondary_reasons"),
            recommendations=analysis_result.get("recommendations"),
            action_items=analysis_result.get("action_items"),
            answers_structured=analysis_result.get("answers_structured"),
            key_quotes=analysis_result.get("key_quotes"),
            red_flags=analysis_result.get("red_flags"),
            positive_feedback=analysis_result.get("positive_feedback"),
            ai_model_used=analysis_result.get("ai_model_used"),
            processing_time_seconds=analysis_result.get("processing_time_seconds")
        )
        db.add(analysis)
        
        interview.status = "completed"
        db.commit()
        
        logger.info(f"Interview {interview_id} analyzed successfully")
        
    except Exception as e:
        interview.status = "error"
        db.commit()
        logger.error(f"Error analyzing interview {interview_id}: {e}")
    finally:
        db.close()

# Dashboard routes
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    org_id = current_user.organization_id
    
    # Basic counts
    total_interviews = db.query(Interview).filter(Interview.organization_id == org_id).count()
    total_employees = db.query(Employee).filter(Employee.organization_id == org_id).count()
    total_followups = db.query(FollowUpCall).filter(FollowUpCall.organization_id == org_id).count()
    
    # Recent interviews (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_interviews = db.query(Interview).filter(
        Interview.organization_id == org_id,
        Interview.created_at >= thirty_days_ago
    ).count()
    
    # Average scores
    analyses = db.query(Analysis).join(Interview).filter(
        Interview.organization_id == org_id
    ).all()
    
    avg_satisfaction = sum(a.satisfaction_score for a in analyses if a.satisfaction_score) / len(analyses) if analyses else 0
    avg_retention_risk = sum(a.retention_risk for a in analyses if a.retention_risk) / len(analyses) if analyses else 0
    
    return {
        "total_interviews": total_interviews,
        "total_employees": total_employees,
        "total_followups": total_followups,
        "recent_interviews": recent_interviews,
        "avg_satisfaction": round(avg_satisfaction, 2),
        "avg_retention_risk": round(avg_retention_risk, 2)
    }

@app.get("/api/interviews", response_model=List[InterviewResponse])
async def get_interviews(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interviews for current organization"""
    interviews = db.query(Interview).filter(
        Interview.organization_id == current_user.organization_id
    ).offset(skip).limit(limit).all()
    
    result = []
    for interview in interviews:
        analysis_data = None
        if interview.analysis:
            analysis_data = {
                "satisfaction_score": interview.analysis.satisfaction_score,
                "sentiment_score": interview.analysis.sentiment_score,
                "retention_risk": interview.analysis.retention_risk,
                "primary_reason": interview.analysis.primary_reason
            }
        
        result.append(InterviewResponse(
            id=interview.id,
            transcript=interview.transcript[:500] + "..." if interview.transcript and len(interview.transcript) > 500 else interview.transcript or "",
            status=interview.status,
            created_at=interview.created_at,
            analysis=analysis_data
        ))
    
    return result

@app.get("/api/interviews/{interview_id}")
async def get_interview_detail(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed interview information"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
        return {
        "interview": {
            "id": interview.id,
            "transcript": interview.transcript,
            "duration_seconds": interview.duration_seconds,
            "status": interview.status,
            "created_at": interview.created_at,
            "phone_number": interview.phone_number,
            "audio_url": interview.audio_url
        },
        "analysis": interview.analysis.__dict__ if interview.analysis else None,
        "employee": interview.employee.__dict__ if interview.employee else None
    }

# Test routes for development
@app.post("/api/test/create-sample-data")
async def create_sample_data(
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Create sample data for testing"""
    org_id = current_user.organization_id
    
    # Create sample employees
        sample_employees = [
            {
            "full_name": "Juan Pérez",
            "email": "juan.perez@ips.com",
                "department": "Seguridad",
            "position": "Guardia Senior",
            "manager_name": "María González"
            },
            {
            "full_name": "Ana López",
            "email": "ana.lopez@ips.com",
                "department": "Administración",
            "position": "Coordinadora",
            "manager_name": "Carlos Ruiz"
            }
        ]
        
        for emp_data in sample_employees:
        employee = Employee(
            organization_id=org_id,
            **emp_data,
            hire_date=datetime.utcnow() - timedelta(days=365),
            tenure_months=12
        )
                db.add(employee)
        
        db.commit()
        
    return {"message": "Sample data created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 