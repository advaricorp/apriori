# 🎤 Apriori - Sistema de Análisis de Entrevistas de Salida

> **Sistema completo con IA, frontend React, backend FastAPI, base de datos PostgreSQL y multitenancy**

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
[![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)](https://apriori.enkisys.com)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 **Características Principales**

### 🎯 **Sistema Completo de Análisis**
- **🤖 Análisis con IA**: Procesamiento inteligente usando OpenAI GPT-4o mini
- **📊 Dashboard en Tiempo Real**: Métricas y visualizaciones interactivas
- **🔄 Webhooks Automáticos**: Integración directa con ElevenLabs
- **👥 Multitenancy**: Soporte para múltiples organizaciones
- **🔐 Autenticación JWT**: Sistema seguro de usuarios y roles

### 🏗️ **Arquitectura Moderna**
- **Frontend**: React 18 + Material-UI + React Query
- **Backend**: FastAPI + PostgreSQL + Redis (opcional)
- **IA**: OpenAI GPT-4o mini (análisis económico y efectivo)
- **Infraestructura**: Docker + Docker Compose + Nginx
- **Despliegue**: Google Cloud Platform con Load Balancer

### 💰 **Análisis Económico de IA**
- **GPT-4o mini**: Solo **$0.37 USD** por 500 análisis
- **94% más barato** que modelos premium
- **Excelente calidad** para análisis de texto en español

## 📋 **Tabla de Contenidos**

- [Instalación Rápida](#-instalación-rápida)
- [Configuración](#-configuración)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [Webhook URL](#-webhook-url)
- [Características Técnicas](#-características-técnicas)

## 🚀 **Instalación Rápida**

### **Opción 1: Docker Compose (Recomendado)**

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd apriori

# 2. Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env con tus API keys

# 3. Ejecutar con Docker
docker-compose up -d

# 4. Verificar que está funcionando
curl http://localhost:4200/health
```

### **Opción 2: Desarrollo Local**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (nueva terminal)
cd frontend
npm install
npm start

# Base de datos
# Usar PostgreSQL local o Docker
```

## ⚙️ **Configuración**

### **Variables de Entorno Principales**

```bash
# API Keys (REQUERIDAS)
OPENAI_API_KEY=sk-your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Base de Datos
DATABASE_URL=postgresql://apriori_user:password@postgres:5432/apriori_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-chars

# Webhooks
ELEVENLABS_WEBHOOK_SECRET=your-webhook-secret
```

### **Configuración de ElevenLabs**

**URL del Webhook:**
```
https://apriori.enkisys.com/webhook/elevenlabs
```

**Métodos de Verificación:**
- HMAC Signature Verification ✅
- IP Whitelisting ✅
- Request Logging ✅

## 📁 **Estructura del Proyecto**

```
apriori/
├── 📂 backend/                 # FastAPI Backend
│   ├── 📂 app/
│   │   ├── main.py            # Aplicación principal
│   │   ├── models.py          # Modelos SQLAlchemy
│   │   ├── auth.py            # Autenticación JWT
│   │   ├── ai_analyzer.py     # Análisis con OpenAI
│   │   ├── elevenlabs_service.py # Integración ElevenLabs
│   │   └── config.py          # Configuración
│   ├── Dockerfile
│   ├── requirements.txt
│   └── init.sql               # Inicialización DB
├── 📂 frontend/               # React Frontend
│   ├── 📂 src/
│   │   ├── 📂 components/     # Componentes reutilizables
│   │   ├── 📂 pages/          # Páginas principales
│   │   ├── 📂 contexts/       # Context (Auth, etc.)
│   │   └── App.js             # App principal
│   ├── package.json
│   └── Dockerfile
├── 📂 nginx/                  # Reverse Proxy
│   └── nginx.conf
├── docker-compose.yml         # Orquestación
├── setup-gcloud.sh           # Setup Google Cloud
└── README.md
```

## 🔌 **API Endpoints**

### **Autenticación**
```http
POST /auth/login              # Iniciar sesión
POST /auth/register           # Registrar usuario
GET  /me                      # Información del usuario
```

### **Webhooks**
```http
POST /webhook/elevenlabs      # Webhook principal (Puerto 4200)
POST /webhook/elevenlabs-followup # Webhook seguimiento
```

### **Dashboard y Datos**
```http
GET  /api/dashboard/stats     # Estadísticas del dashboard
GET  /api/interviews          # Lista de entrevistas
GET  /api/interviews/{id}     # Detalle de entrevista
GET  /api/employees           # Lista de empleados
```

### **Documentación**
```http
GET  /docs                    # Swagger UI
GET  /redoc                   # ReDoc
GET  /health                  # Health check
```

## 🌐 **Deployment en Google Cloud**

### **1. Configuración Automática**

```bash
# Ejecutar script de configuración
./setup-gcloud.sh

# Configurar variables
# Editar PROJECT_ID en setup-gcloud.sh
```

### **2. Configuración Manual**

```bash
# Abrir puerto 4200
gcloud compute firewall-rules create apriori-app-port \
    --allow tcp:4200 \
    --source-ranges 0.0.0.0/0 \
    --description "Puerto para aplicación Apriori"

# Abrir puertos adicionales
gcloud compute firewall-rules create apriori-web-ports \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Puertos web para Apriori"
```

### **3. Load Balancer (Alternativa a AWS ALB)**

Google Cloud proporciona **Cloud Load Balancing** que incluye:
- ✅ **Certificados SSL administrados automáticamente**
- ✅ **Balanceador de carga global**
- ✅ **Health checks automáticos**
- ✅ **CDN integrado**
- ✅ **DDoS protection**

```bash
# El script setup-gcloud.sh configura automáticamente:
# - Global Load Balancer
# - Certificado SSL para apriori.enkisys.com
# - Health checks
# - Forwarding rules HTTP/HTTPS
```

## 📡 **Webhook URL**

### **URL para ElevenLabs**
```
https://apriori.enkisys.com/webhook/elevenlabs
```

### **Configuración del Agente ElevenLabs**
```json
{
  "webhook_url": "https://apriori.enkisys.com/webhook/elevenlabs",
  "webhook_method": "POST",
  "webhook_headers": {
    "Content-Type": "application/json",
    "X-ElevenLabs-Signature": "tu-firma-webhook"
  }
}
```

## 🔧 **Características Técnicas**

### **Backend (FastAPI)**
- ⚡ **Asíncrono**: Máximo rendimiento
- 🔐 **JWT Authentication**: Seguridad robusta
- 👥 **Multitenancy**: Organizaciones separadas
- 📊 **PostgreSQL**: Base de datos robusta
- 🤖 **OpenAI GPT-4o mini**: IA económica y efectiva

### **Frontend (React)**
- ⚛️ **React 18**: Última versión
- 🎨 **Material-UI**: Diseño moderno
- 🔄 **React Query**: Gestión de estado del servidor
- 🍞 **React Hot Toast**: Notificaciones elegantes
- 📱 **Responsive**: Adaptable a móviles

### **Base de Datos**
- 🐘 **PostgreSQL 15**: Rendimiento y confiabilidad
- 🔄 **Migraciones automáticas**: Alembic
- 📈 **Índices optimizados**: Consultas rápidas
- 🔒 **Conexiones seguras**: SSL/TLS

### **Infraestructura**
- 🐳 **Docker**: Contenedores para todo
- 🔄 **Docker Compose**: Orquestación local
- 🌐 **Nginx**: Reverse proxy optimizado
- ☁️ **Google Cloud**: Producción escalable

## 💡 **Casos de Uso**

### **1. Empresa de Seguridad (IPS)**
- Análisis automático de entrevistas de salida
- Identificación de patrones de rotación
- Métricas de satisfacción por departamento
- Seguimiento proactivo de empleados en riesgo

### **2. Consultoría HR**
- **Multitenancy**: Múltiples clientes
- Dashboards personalizados por cliente
- Análisis comparativos entre organizaciones
- Reportes ejecutivos automatizados

### **3. Empresa Grande (500+ empleados)**
- Análisis masivo de entrevistas
- Integración con sistemas HRIS
- Predicción de rotación con IA
- Automatización de procesos HR

## 🚨 **Troubleshooting**

### **Problemas Comunes**

**1. Error de conexión a base de datos**
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps postgres

# Ver logs
docker-compose logs postgres
```

**2. Frontend no se conecta al backend**
```bash
# Verificar proxy en package.json
"proxy": "http://backend:8000"

# O configurar REACT_APP_API_URL
REACT_APP_API_URL=http://localhost:8000
```

**3. Webhook no recibe datos**
```bash
# Verificar firewall
curl -X POST https://apriori.enkisys.com/webhook/elevenlabs

# Ver logs de nginx
docker-compose logs nginx
```

## 📊 **Monitoreo y Métricas**

### **Health Checks**
```bash
# Sistema general
curl https://apriori.enkisys.com/health

# Base de datos
curl https://apriori.enkisys.com/api/dashboard/stats

# Webhook
curl -X POST https://apriori.enkisys.com/webhook/elevenlabs \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### **Logs**
```bash
# Ver todos los logs
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend
```

## 🔐 **Seguridad**

### **Medidas Implementadas**
- 🔐 **JWT con expiración automática**
- 🔒 **HTTPS obligatorio en producción**
- 🛡️ **CORS configurado correctamente**
- 📝 **Logging de todas las requests**
- 🔑 **Verificación HMAC de webhooks**
- 💾 **Sanitización de inputs**
- 👥 **Control de acceso basado en roles**

## 📈 **Costos de Operación**

### **OpenAI GPT-4o mini**
- **500 análisis**: $0.37 USD/mes
- **1,000 análisis**: $0.74 USD/mes
- **5,000 análisis**: $3.70 USD/mes

### **Google Cloud (estimado)**
- **Compute Engine**: $20-50/mes
- **Load Balancer**: $18/mes
- **Cloud SQL**: $25-100/mes
- **Total**: ~$60-170/mes

### **ElevenLabs**
- Según plan de llamadas elegido
- Integración incluida sin costos adicionales

## 🤝 **Contribuir**

```bash
# 1. Fork del repositorio
# 2. Crear rama de feature
git checkout -b feature/nueva-funcionalidad

# 3. Hacer cambios y commit
git commit -m "feat: agregar nueva funcionalidad"

# 4. Push y crear Pull Request
git push origin feature/nueva-funcionalidad
```

## 📞 **Soporte**

- **Documentación**: [https://apriori.enkisys.com/docs](https://apriori.enkisys.com/docs)
- **Issues**: Crear issue en GitHub
- **Email**: soporte@enkisys.com

---

## 🎉 **¡Listo para Producción!**

El sistema Apriori está **completamente configurado** y listo para:

✅ **Recibir webhooks de ElevenLabs**  
✅ **Procesar análisis con IA**  
✅ **Mostrar dashboard en tiempo real**  
✅ **Soportar múltiples organizaciones**  
✅ **Escalar automáticamente**  

**URL del Webhook:** `https://apriori.enkisys.com/webhook/elevenlabs`  
**Dashboard:** `https://apriori.enkisys.com`  
**API Docs:** `https://apriori.enkisys.com/docs`

---

*Desarrollado con ❤️ para optimizar procesos de RRHH con Inteligencia Artificial*
