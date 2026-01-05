# 🚀 Guia de Deployment para Produção
## Sistema de Comissão 2.0 - Honda Rondo Motos

---

## 📋 Checklist Pré-Produção

### ✅ Validação de Código
- [x] Testes passando
- [x] Documentação completa
- [x] Sem arquivos de teste
- [x] Sem logs desnecessários
- [x] Banco de dados limpo (verificado)

### ✅ Segurança
- [ ] SECRET_KEY alterada para valor único e seguro
- [ ] MONGO_URI verificada (não deve ter credenciais padrão)
- [ ] CORS_ORIGINS configurado corretamente
- [ ] FLASK_DEBUG=False em produção
- [ ] SSL/HTTPS ativado no servidor

### ✅ Performance
- [ ] Índices de MongoDB criados
- [ ] Cache configurado
- [ ] Compressão de resposta habilitada
- [ ] Rate limiting ativado

### ✅ Backup
- [ ] Backup do banco de dados agendado
- [ ] Plano de recuperação de desastre definido
- [ ] Logs centralizados configurados

---

## 🔧 Passo a Passo de Deployment

### 1. Preparar Servidor (Linux/Ubuntu)

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Instalar MongoDB (se não estiver na nuvem)
sudo apt install mongodb -y
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Criar usuário para a aplicação
sudo useradd -m -s /bin/bash comissao
sudo su - comissao
```

### 2. Clonar/Copiar Aplicação

```bash
# Criar diretório
cd /opt
sudo mkdir comissao-app
sudo chown comissao:comissao comissao-app
cd comissao-app

# Copiar arquivos (via Git ou SCP)
# git clone seu-repositorio .
# OU copiar manualmente
```

### 3. Configurar Ambiente Python

```bash
# Criar virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Adicionar pacotes para produção
pip install gunicorn
pip install python-dotenv
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de produção
cp .env.production .env

# Editar com valores reais
nano .env

# Pontos críticos a atualizar:
# - SECRET_KEY (gerar novo)
# - MONGO_URI (apontar para BD de produção)
# - FLASK_PORT (porta real)
# - WORKERS (número de workers do Gunicorn)
```

### 5. Gerar SECRET_KEY Seguro

```bash
# Comando para gerar chave forte
python3 -c "import os; print('SECRET_KEY=' + os.urandom(32).hex())"

# Copiar resultado e colar em .env
```

### 6. Testar Localmente

```bash
# Ativar venv
source venv/bin/activate

# Testar com gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 run:app

# Verificar em outro terminal
curl http://localhost:5000/api/saude
# Deve retornar: {"status":"ok"}
```

### 7. Configurar Systemd Service

Criar `/etc/systemd/system/comissao.service`:

```ini
[Unit]
Description=Sistema de Comissão v2.0
After=network.target mongodb.service

[Service]
Type=notify
User=comissao
WorkingDirectory=/opt/comissao-app
Environment="PATH=/opt/comissao-app/venv/bin"
ExecStart=/opt/comissao-app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --access-logfile /opt/comissao-app/logs/access.log \
    --error-logfile /opt/comissao-app/logs/error.log \
    run:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable comissao
sudo systemctl start comissao
sudo systemctl status comissao
```

### 8. Configurar Nginx (Reverse Proxy)

Criar `/etc/nginx/sites-available/comissao`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    # SSL (usar Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

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
```

Ativar:
```bash
sudo ln -s /etc/nginx/sites-available/comissao /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Configurar SSL com Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot certonly --nginx -d seu-dominio.com
```

### 10. Configurar Backup Automático

Criar `/opt/comissao-app/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/comissao-app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/comissao_db_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

# Dump MongoDB
mongodump --out /tmp/comissao_backup_$DATE

# Comprimir
tar -czf $BACKUP_FILE -C /tmp comissao_backup_$DATE

# Remover temp
rm -rf /tmp/comissao_backup_$DATE

# Manter últimos 30 dias
find $BACKUP_DIR -mtime +30 -delete

echo "Backup criado: $BACKUP_FILE"
```

Adicionar ao crontab:
```bash
# Backup diariamente às 2:00 da manhã
0 2 * * * /opt/comissao-app/backup.sh >> /opt/comissao-app/logs/backup.log 2>&1
```

---

## 📊 Monitoramento

### Verificar Status

```bash
# Serviço
sudo systemctl status comissao

# Logs
tail -f /opt/comissao-app/logs/error.log
tail -f /opt/comissao-app/logs/access.log

# Processo
ps aux | grep gunicorn

# Conexões
netstat -tuln | grep 5000
```

### Health Check

```bash
# Endpoint de saúde
curl https://seu-dominio.com/api/saude

# Resposta esperada:
# {"status":"ok"}
```

---

## 🚨 Troubleshooting

### Aplicação não inicia
```bash
# Verificar logs
journalctl -u comissao -n 50

# Testar venv
source /opt/comissao-app/venv/bin/activate
python run.py
```

### Banco de dados não conecta
```bash
# Verificar MongoDB
sudo systemctl status mongodb
mongo --eval "db.adminCommand('ping')"

# Testar conexão
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017/'))"
```

### Port já em uso
```bash
# Encontrar processo
lsof -i :5000

# Matar processo
kill -9 <PID>
```

### Permissões
```bash
# Fixar permissões
sudo chown -R comissao:comissao /opt/comissao-app
sudo chmod 755 /opt/comissao-app
sudo chmod 755 /opt/comissao-app/logs
```

---

## 📈 Checklist Pós-Produção

- [ ] Serviço iniciando automaticamente após reboot
- [ ] Logs sendo gerados corretamente
- [ ] Backup automático funcionando
- [ ] SSL/HTTPS ativo
- [ ] Rate limiting ativo
- [ ] Monitoramento configurado
- [ ] Alertas de erro configurados
- [ ] Documentação de runbook atualizada
- [ ] Equipe treinada
- [ ] Plano de rollback definido

---

## 🔄 Rollback (Se Necessário)

```bash
# Voltar versão anterior
cd /opt/comissao-app
git checkout <commit-anterior>
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart comissao
```

---

## 📞 Suporte

Em caso de problemas:
1. Verificar logs: `/opt/comissao-app/logs/`
2. Testar health check: `curl https://seu-dominio.com/api/saude`
3. Consultar documentação: `DOCUMENTACAO.md`
4. Contatar administrador de sistemas

---

**Versão:** 1.0  
**Data:** 2026-01-05  
**Status:** Pronto para Produção ✅
