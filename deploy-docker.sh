#!/bin/bash

#############################################
# Deploy Script - Sistema de Comissão v2.0
# Plataforma: Debian/Ubuntu com Docker
# Autor: Sistema de Comissão
# Data: 2026-01-05
#############################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
APP_NAME="comissao-app"
REPO_URL="https://github.com/escoobi/commissar-sistema-v2.git"
APP_DIR="/opt/comissao-app"
DOCKER_COMPOSE_FILE="$APP_DIR/docker-compose.yml"
ENV_FILE="$APP_DIR/.env"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Deploy Docker - Sistema de Comissão v2.0         ║${NC}"
echo -e "${BLUE}║              Debian/Ubuntu                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Função para exibir mensagens
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 1. Verificar se é root
log_info "Verificando permissões..."
if [ "$EUID" -ne 0 ]; then
   log_error "Este script precisa ser executado como root!"
   echo "Execute: sudo bash deploy-docker.sh"
   exit 1
fi
log_success "Permissões OK"
echo ""

# 2. Verificar dependências
log_info "Verificando dependências..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 não está instalado"
        return 1
    fi
    return 0
}

DEPS_OK=true

if ! check_command docker; then
    log_warning "Docker não instalado. Instalando..."
    apt-get update
    apt-get install -y docker.io
    DEPS_OK=true
else
    log_success "Docker ✓"
fi

if ! check_command docker-compose; then
    log_warning "Docker Compose não instalado. Instalando..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    DEPS_OK=true
else
    log_success "Docker Compose ✓"
fi

if ! check_command git; then
    log_warning "Git não instalado. Instalando..."
    apt-get install -y git
fi
log_success "Git ✓"

if ! check_command curl; then
    apt-get install -y curl
fi
log_success "Curl ✓"

log_success "Todas as dependências OK"
echo ""

# 3. Criar diretório da aplicação
log_info "Preparando diretórios..."
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    log_success "Diretório criado: $APP_DIR"
else
    log_warning "Diretório já existe: $APP_DIR"
fi

cd "$APP_DIR"
log_success "Diretório: $(pwd)"
echo ""

# 4. Clone/Pull do GitHub
log_info "Atualizando código do GitHub..."
if [ -d "$APP_DIR/.git" ]; then
    log_info "Repositório já existe. Fazendo pull..."
    git pull origin master || git pull origin main
else
    log_info "Clonando repositório..."
    git clone "$REPO_URL" .
fi
log_success "Código atualizado"
echo ""

# 5. Criar arquivo .env
log_info "Configurando variáveis de ambiente..."

# Gerar SECRET_KEY forte
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
MONGO_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << EOF
# Configuração de Produção - Sistema de Comissão v2.0
# Gerado automaticamente em $(date)

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$SECRET_KEY

# MongoDB Configuration
MONGO_PASSWORD=$MONGO_PASSWORD
MONGO_URI=mongodb://admin:$MONGO_PASSWORD@mongodb:27017/comissao_db?authSource=admin

# Application Configuration
LOG_LEVEL=INFO
WORKERS=4
MAX_CONTENT_LENGTH=16777216

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Performance
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300
EOF
    log_success "Arquivo .env criado"
    log_warning "⚠️  IMPORTANTE: Revise o arquivo .env com suas configurações reais"
    log_warning "   Especialmente: SECRET_KEY e MONGO_PASSWORD"
else
    log_warning "Arquivo .env já existe. Pulando..."
fi
echo ""

# 6. Criar diretórios de volumes
log_info "Criando diretórios de logs e uploads..."
mkdir -p logs uploads nginx/ssl
chmod 755 logs uploads nginx
log_success "Diretórios criados"
echo ""

# 7. Configurar Nginx (básico)
log_info "Configurando Nginx..."

if [ ! -f "$APP_DIR/nginx.conf" ]; then
    cat > "$APP_DIR/nginx.conf" << 'NGINX_EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 16M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json;

    upstream app {
        server app:5000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /static/ {
            alias /app/static/;
            expires 30d;
        }

        location /api/saude {
            proxy_pass http://app/api/saude;
            access_log off;
        }
    }
}
NGINX_EOF
    log_success "Nginx configurado"
fi
echo ""

# 8. Build e start dos containers
log_info "Construindo imagens Docker..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
log_success "Imagens construídas"
echo ""

log_info "Iniciando containers..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
log_success "Containers iniciados"
echo ""

# 9. Verificar saúde dos containers
log_info "Aguardando containers ficarem saudáveis..."
sleep 5

log_info "Status dos containers:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps
echo ""

# 10. Testes básicos
log_info "Executando testes de saúde..."

# Teste MongoDB
if docker exec comissao-mongodb mongosh --quiet --eval "db.adminCommand('ping')" &>/dev/null; then
    log_success "MongoDB ✓"
else
    log_error "MongoDB ✗ - Verifique os logs"
fi

# Teste Flask App
sleep 2
if curl -s http://localhost:5000/api/saude > /dev/null; then
    log_success "Flask App ✓"
else
    log_error "Flask App ✗ - Verifique os logs"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Deploy Concluído com Sucesso! ✓              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 Informações do Deploy:${NC}"
echo "   Diretório: $APP_DIR"
echo "   Arquivo config: $ENV_FILE"
echo "   Docker Compose: $DOCKER_COMPOSE_FILE"
echo ""

echo -e "${BLUE}🌐 URLs:${NC}"
echo "   Aplicação: http://$(hostname -I | awk '{print $1}'):5000"
echo "   API Saúde: http://$(hostname -I | awk '{print $1}'):5000/api/saude"
echo "   Nginx: http://$(hostname -I | awk '{print $1}'):80"
echo ""

echo -e "${BLUE}📋 Comandos Úteis:${NC}"
echo "   Ver logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f app"
echo "   Parar: docker-compose -f $DOCKER_COMPOSE_FILE down"
echo "   Reiniciar: docker-compose -f $DOCKER_COMPOSE_FILE restart"
echo "   Status: docker-compose -f $DOCKER_COMPOSE_FILE ps"
echo ""

echo -e "${YELLOW}⚠️  Próximos Passos:${NC}"
echo "   1. Edite o arquivo .env com suas configurações reais"
echo "   2. Configure SSL/HTTPS (veja documentação)"
echo "   3. Configure backup de dados"
echo "   4. Configure monitoring/alertas"
echo ""

log_success "Deploy finalizado em: $(date)"
