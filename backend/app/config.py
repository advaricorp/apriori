import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # ElevenLabs
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_webhook_secret: Optional[str] = None
    
    # Database
    database_url: str = "postgresql://apriori_user:apriori_secure_password_2024@localhost:5432/apriori_db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # JWT
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # App
    app_name: str = "Apriori - Exit Interview Analyzer"
    environment: str = "development"
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:4200",
        "https://apriori.enkisys.com",
        "https://enkisys.com"
    ]
    
    # File uploads
    upload_max_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 