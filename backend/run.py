#!/usr/bin/env python3
"""
Sistema de Análisis de Entrevistas IPS
Aplicación para procesar webhooks de ElevenLabs y generar análisis con IA
"""

import uvicorn
from app.main import app
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    print("🎤 Iniciando Sistema de Análisis de Entrevistas IPS...")
    print(f"🌐 Host: {settings.host}")
    print(f"🔌 Puerto: {settings.port}")
    print(f"🔧 Debug: {settings.debug}")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 