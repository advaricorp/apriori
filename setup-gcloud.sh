#!/bin/bash

# Setup script para Google Cloud Platform
# Configuración de firewall y deployment para Apriori

set -e

echo "🚀 Configurando Google Cloud para Apriori..."

# Variables
PROJECT_ID="your-project-id"
INSTANCE_NAME="apriori-server"
ZONE="us-central1-a"
STATIC_IP="35.208.175.9"
DOMAIN="apriori.enkisys.com"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que gcloud esté instalado
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI no está instalado. Instala Google Cloud SDK primero."
    exit 1
fi

# Configurar proyecto
print_status "Configurando proyecto de Google Cloud..."
gcloud config set project $PROJECT_ID

# Abrir puertos en el firewall
print_status "Configurando reglas de firewall..."

# Puerto 4200 para la aplicación
gcloud compute firewall-rules create apriori-app-port \
    --allow tcp:4200 \
    --source-ranges 0.0.0.0/0 \
    --description "Puerto para aplicación Apriori" \
    --quiet || print_warning "Regla apriori-app-port ya existe"

# Puerto 80 para HTTP
gcloud compute firewall-rules create apriori-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "HTTP para Apriori" \
    --quiet || print_warning "Regla apriori-http ya existe"

# Puerto 443 para HTTPS
gcloud compute firewall-rules create apriori-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "HTTPS para Apriori" \
    --quiet || print_warning "Regla apriori-https ya existe"

# Puerto 8000 para backend API (opcional, para desarrollo)
gcloud compute firewall-rules create apriori-backend \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Backend API para Apriori" \
    --quiet || print_warning "Regla apriori-backend ya existe"

print_success "Reglas de firewall configuradas correctamente"

# Verificar IP estática
print_status "Verificando IP estática..."
if gcloud compute addresses describe apriori-static-ip --region=us-central1 &> /dev/null; then
    print_success "IP estática ya existe: $STATIC_IP"
else
    print_status "Creando IP estática..."
    gcloud compute addresses create apriori-static-ip \
        --region=us-central1 \
        --description="IP estática para Apriori"
    print_success "IP estática creada"
fi

# Configurar Load Balancer (alternativa a ALB de AWS)
print_status "Configurando Load Balancer..."

# Crear health check
gcloud compute health-checks create http apriori-health-check \
    --port 4200 \
    --request-path /health \
    --description "Health check para Apriori" \
    --quiet || print_warning "Health check ya existe"

# Crear backend service
gcloud compute backend-services create apriori-backend-service \
    --protocol HTTP \
    --health-checks apriori-health-check \
    --global \
    --description "Backend service para Apriori" \
    --quiet || print_warning "Backend service ya existe"

# Crear URL map
gcloud compute url-maps create apriori-url-map \
    --default-service apriori-backend-service \
    --description "URL map para Apriori" \
    --quiet || print_warning "URL map ya existe"

# Crear HTTPS proxy (para SSL)
print_status "Configurando HTTPS proxy..."

# Crear certificado SSL administrado por Google
gcloud compute ssl-certificates create apriori-ssl-cert \
    --domains $DOMAIN \
    --description "Certificado SSL para Apriori" \
    --quiet || print_warning "Certificado SSL ya existe"

# Crear HTTPS proxy
gcloud compute target-https-proxies create apriori-https-proxy \
    --url-map apriori-url-map \
    --ssl-certificates apriori-ssl-cert \
    --description "HTTPS proxy para Apriori" \
    --quiet || print_warning "HTTPS proxy ya existe"

# Crear forwarding rule global para HTTPS
gcloud compute forwarding-rules create apriori-https-forwarding-rule \
    --address $STATIC_IP \
    --global \
    --target-https-proxy apriori-https-proxy \
    --ports 443 \
    --description "HTTPS forwarding rule para Apriori" \
    --quiet || print_warning "HTTPS forwarding rule ya existe"

# Crear forwarding rule para HTTP (redirect a HTTPS)
gcloud compute target-http-proxies create apriori-http-proxy \
    --url-map apriori-url-map \
    --description "HTTP proxy para Apriori" \
    --quiet || print_warning "HTTP proxy ya existe"

gcloud compute forwarding-rules create apriori-http-forwarding-rule \
    --address $STATIC_IP \
    --global \
    --target-http-proxy apriori-http-proxy \
    --ports 80 \
    --description "HTTP forwarding rule para Apriori" \
    --quiet || print_warning "HTTP forwarding rule ya existe"

print_success "Load Balancer configurado correctamente"

# Mostrar información de configuración
echo ""
echo "=========================================="
echo "🎉 CONFIGURACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "📋 Información del deployment:"
echo "   IP Estática: $STATIC_IP"
echo "   Dominio: $DOMAIN"
echo "   Puerto aplicación: 4200"
echo "   Puerto backend: 8000"
echo ""
echo "🌐 URLs importantes:"
echo "   Aplicación: https://$DOMAIN"
echo "   API Backend: https://$DOMAIN/api/"
echo "   Webhook ElevenLabs: https://$DOMAIN/webhook/elevenlabs"
echo "   Documentación API: https://$DOMAIN/docs"
echo ""
echo "🔧 Para deployar la aplicación:"
echo "   1. Conectarse a la instancia:"
echo "      gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "   2. Clonar el repositorio y ejecutar:"
echo "      cd apriori"
echo "      docker-compose up -d"
echo ""
echo "🔐 Configuración SSL:"
echo "   - Certificado SSL administrado por Google Cloud"
echo "   - Renovación automática"
echo "   - HTTPS forzado automáticamente"
echo ""
echo "📡 Webhook URL para ElevenLabs:"
echo "   https://$DOMAIN/webhook/elevenlabs"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Asegúrate de configurar las variables de entorno"
echo "   - Actualiza el DNS para apuntar $DOMAIN a $STATIC_IP"
echo "   - Configura las API keys en .env"
echo ""
print_success "¡Setup de Google Cloud completado!"

# Crear script de deployment
cat > deploy.sh << 'EOF'
#!/bin/bash

# Script de deployment para Apriori
echo "🚀 Deploying Apriori..."

# Pull latest changes
git pull origin main

# Build and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose ps

echo "✅ Deployment completed!"
echo "🌐 Application available at: https://apriori.enkisys.com"
EOF

chmod +x deploy.sh
print_success "Script de deployment creado: ./deploy.sh" 