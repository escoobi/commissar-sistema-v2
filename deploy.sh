#!/bin/bash
# =====================================================
# Script de Deploy Automático - Sistema de Comissão v2.0
# Ambiente: Ubuntu/Debian Linux
# =====================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        DEPLOY AUTOMÁTICO - SISTEMA DE COMISSÃO v2.0           ║"
echo "║           Sistema de Processamento de Comissões               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
APP_DIR="/opt/comissao-app"
REPO_URL="https://github.com/escoobi/commissar-sistema-v2.git"
USER="comissao"
GROUP="comissao"

echo -e "${BLUE}📋 PRÉ-REQUISITOS${NC}"
echo ""
echo "Este script vai:"
echo "  1. Clonar repositório do GitHub"
echo "  2. Criar usuário para a aplicação"
echo "  3. Instalar dependências Python"
echo "  4. Configurar virtualenv"
echo "  5. Configurar arquivo .env"
echo "  6. Criar serviço systemd"
echo "  7. Configurar Nginx reverse proxy"
echo ""

# Checar se está rodando como root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Este script deve ser executado como root${NC}"
   echo "Execute: sudo bash deploy.sh"
   exit 1
fi

# 1. Atualizar sistema
echo -e "${BLUE}🔄 Atualizando sistema...${NC}"
apt update && apt upgrade -y

# 2. Instalar dependências do sistema
echo -e "${BLUE}📦 Instalando dependências do sistema...${NC}"
apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    nginx \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

# 3. Criar usuário da aplicação
echo -e "${BLUE}👤 Criando usuário da aplicação...${NC}"
if ! id "$USER" &>/dev/null; then
    useradd -m -s /bin/bash -d /home/$USER $USER
    echo -e "${GREEN}✅ Usuário $USER criado${NC}"
else
    echo -e "${YELLOW}⚠️  Usuário $USER já existe${NC}"
fi

# 4. Clonar repositório
echo -e "${BLUE}📥 Clonando repositório...${NC}"
if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}⚠️  Diretório $APP_DIR já existe${NC}"
    read -p "Deseja sobrescrever? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf $APP_DIR
        git clone $REPO_URL $APP_DIR
    fi
else
    git clone $REPO_URL $APP_DIR
fi

# 5. Configurar permissões
echo -e "${BLUE}🔐 Configurando permissões...${NC}"
chown -R $USER:$GROUP $APP_DIR
chmod -R 755 $APP_DIR

# 6. Criar virtualenv
echo -e "${BLUE}🐍 Criando virtualenv...${NC}"
su - $USER -c "cd $APP_DIR && python3.11 -m venv venv"

# 7. Instalar dependências Python
echo -e "${BLUE}📚 Instalando dependências Python...${NC}"
su - $USER -c "cd $APP_DIR && . venv/bin/activate && pip install --upgrade pip && pip install -r requirements-production.txt"

# 8. Criar arquivo .env
echo -e "${BLUE}⚙️  Criando arquivo .env...${NC}"
cat > $APP_DIR/.env << 'EOF'
FLASK_APP=run.py
FLASK_ENV=production
FLASK_DEBUG=False

# Substitua com seu MongoDB URI real
MONGO_URI=mongodb://localhost:27017/comissao_db
SECRET_KEY=gere-uma-chave-forte-com-32-caracteres-alfanumericos

UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS=csv,xlsx
MAX_CONTENT_LENGTH=16777216

LOG_LEVEL=INFO
FLASK_PORT=5000
WORKERS=4
EOF

chown $USER:$GROUP $APP_DIR/.env
chmod 600 $APP_DIR/.env
echo -e "${YELLOW}⚠️  ⚠️  EDITE O ARQUIVO .env COM SUAS CREDENCIAIS REAIS!${NC}"
echo "   sudo nano $APP_DIR/.env"

# 9. Criar diretórios
echo -e "${BLUE}📁 Criando diretórios necessários...${NC}"
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/uploads
mkdir -p $APP_DIR/backups
chown -R $USER:$GROUP $APP_DIR/logs $APP_DIR/uploads $APP_DIR/backups

# 10. Criar serviço systemd
echo -e "${BLUE}⚙️  Criando serviço systemd...${NC}"
cat > /etc/systemd/system/comissao.service << EOF
[Unit]
Description=Sistema de Comissão v2.0
After=network.target mongodb.service
Wants=mongodb.service

[Service]
Type=notify
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 4 \\
    --worker-class sync \\
    --bind 0.0.0.0:5000 \\
    --timeout 120 \\
    --access-logfile $APP_DIR/logs/access.log \\
    --error-logfile $APP_DIR/logs/error.log \\
    run:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable comissao
echo -e "${GREEN}✅ Serviço systemd criado${NC}"

# 11. Criar configuração Nginx
echo -e "${BLUE}🌐 Configurando Nginx...${NC}"
cat > /etc/nginx/sites-available/comissao << 'EOF'
server {
    listen 80;
    server_name _;

    # Redirecionar para HTTPS (remova esta seção se não usar SSL)
    # return 301 https://$server_name$request_uri;

    # Logs
    access_log /var/log/nginx/comissao_access.log;
    error_log /var/log/nginx/comissao_error.log;

    # Proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Upload limite
    client_max_body_size 16M;
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/comissao /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx
echo -e "${GREEN}✅ Nginx configurado${NC}"

# 12. Iniciar serviço
echo -e "${BLUE}🚀 Iniciando serviço...${NC}"
systemctl start comissao

# 13. Verificar status
echo ""
echo -e "${BLUE}📊 VERIFICANDO STATUS${NC}"
echo ""
systemctl status comissao --no-pager
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✅ DEPLOY CONCLUÍDO COM SUCESSO! ✅                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}⚠️  PRÓXIMAS AÇÕES:${NC}"
echo ""
echo "1️⃣  Editar arquivo .env com credenciais reais:"
echo "   ${BLUE}sudo nano $APP_DIR/.env${NC}"
echo ""
echo "2️⃣  Reiniciar serviço após editar .env:"
echo "   ${BLUE}sudo systemctl restart comissao${NC}"
echo ""
echo "3️⃣  Verificar logs:"
echo "   ${BLUE}tail -f $APP_DIR/logs/error.log${NC}"
echo ""
echo "4️⃣  Acessar aplicação:"
echo "   ${BLUE}http://seu-servidor-ip${NC}"
echo ""
echo "5️⃣  Configurar SSL/HTTPS (recomendado):"
echo "   ${BLUE}sudo apt install certbot python3-certbot-nginx${NC}"
echo "   ${BLUE}sudo certbot certonly --nginx -d seu-dominio.com${NC}"
echo ""
echo "📖 Mais informações em: $APP_DIR/DEPLOYMENT_GUIDE.md"
echo ""
