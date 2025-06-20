#!/bin/bash

echo "🎤 Configurando Sistema de Análisis de Entrevistas IPS"
echo "=================================================="

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️ Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo de configuración..."
    cp .env.example .env
    echo "📝 Por favor, edita el archivo .env con tus claves de API:"
    echo "   - GOOGLE_API_KEY (requerido para análisis de IA)"
    echo "   - ELEVENLABS_WEBHOOK_SECRET (opcional, para seguridad)"
fi

echo ""
echo "✅ Configuración completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Editar .env con tus claves de API"
echo "2. Ejecutar: source venv/bin/activate"
echo "3. Ejecutar: python run.py"
echo ""
echo "🌐 La aplicación estará disponible en: http://localhost:8000"
echo "📖 Documentación en: http://localhost:8000/docs" 