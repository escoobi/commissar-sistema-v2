# 🐳 Deploy Docker - Sistema de Comissão v2.0

## Guia Completo para Debian/Ubuntu com Docker

---

## 📋 Pré-Requisitos

- ✅ Servidor Debian/Ubuntu 20.04+
- ✅ SSH acesso como `root` ou com `sudo`
- ✅ Conexão à internet
- ✅ Mínimo 2GB RAM livre
- ✅ Mínimo 5GB espaço em disco

---

## 🚀 Instalação Rápida (1 passo)

### Opção 1: Download e Execução Direta

```bash
# Fazer login no servidor
ssh root@seu-servidor-ip

# Dar permissão e executar script
curl -fsSL https://github.com/escoobi/commissar-sistema-v2/raw/master/deploy-docker.sh | sudo bash
```

### Opção 2: Manual Step-by-Step

```bash
# 1. Atualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# 2. Instalar Docker
sudo apt-get install -y docker.io docker-compose git curl

# 3. Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# 4. Criar diretório e clonar
mkdir -p /opt/comissao-app
cd /opt/comissao-app
git clone https://github.com/escoobi/commissar-sistema-v2.git .

# 5. Executar script de deploy
sudo bash deploy-docker.sh
```

---

## 📝 Configuração Manual (se preferir)

### Passo 1: Criar arquivo `.env`

```bash
cd /opt/comissao-app
nano .env
```

Conteúdo:
```
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=seu-secret-key-aleatorio-com-60-chars
MONGO_PASSWORD=sua-senha-mongodb-forte
LOG_LEVEL=INFO
WORKERS=4
```

### Passo 2: Subir os containers

```bash
docker-compose up -d
```

### Passo 3: Verificar status

```bash
docker-compose ps
```

Esperado:
```
NAME                    STATUS
comissao-app           Up (healthy)
comissao-mongodb       Up (healthy)
comissao-nginx         Up
```

---

## 🔧 Estrutura Docker

### Serviços

| Serviço | Imagem | Porta | Função |
|---------|--------|-------|--------|
| **app** | Python 3.11 | 5000 | Flask + Gunicorn |
| **mongodb** | MongoDB 7.0 | 27017 | Database |
| **nginx** | Nginx Alpine | 80/443 | Reverse Proxy |

### Volumes

```
mongodb_data/       → Dados do MongoDB
mongodb_config/     → Configurações MongoDB
logs/              → Logs da aplicação
uploads/           → Uploads de usuários
```

### Network

- Rede interna: `comissao-network`
- Isolado do host (exceto portas mapeadas)

---

## 📊 Monitoramento

### Ver logs em tempo real

```bash
# Logs da aplicação
docker-compose logs -f app

# Logs do MongoDB
docker-compose logs -f mongodb

# Logs do Nginx
docker-compose logs -f nginx

# Todos os logs
docker-compose logs -f
```

### Verificar saúde

```bash
# Status dos containers
docker-compose ps

# Verificar endpoint de saúde
curl http://localhost:5000/api/saude

# Verificar MongoDB
docker exec comissao-mongodb mongosh --quiet --eval "db.adminCommand('ping')"
```

---

## 🔄 Comandos Principais

### Iniciar/Parar

```bash
# Iniciar tudo
docker-compose up -d

# Parar tudo (mantém dados)
docker-compose down

# Parar e remover volumes (⚠️ PERDA DE DADOS)
docker-compose down -v

# Reiniciar serviços
docker-compose restart
```

### Atualizações

```bash
# Atualizar código
cd /opt/comissao-app
git pull origin master

# Reconstruir imagem
docker-compose build --no-cache

# Aplicar mudanças
docker-compose up -d --remove-orphans
```

### Backup

```bash
# Backup do MongoDB
docker exec comissao-mongodb mongodump --out /backup --authSource admin -u admin -p $MONGO_PASSWORD

# Copiar para host
docker cp comissao-mongodb:/backup ./backup

# Backup dos uploads
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
```

### Restaurar

```bash
# Restaurar dados
docker cp ./backup comissao-mongodb:/
docker exec comissao-mongodb mongorestore /backup --authSource admin -u admin -p $MONGO_PASSWORD
```

---

## 🌐 Acesso Remoto

### Pelo IP do servidor

```
http://seu-servidor-ip:5000
http://seu-servidor-ip/api/saude
```

### Com domínio (Nginx)

Edit `/opt/comissao-app/nginx.conf`:

```nginx
server_name seu-dominio.com.br www.seu-dominio.com.br;

# Redirecionar HTTP para HTTPS
if ($scheme != "https") {
    return 301 https://$server_name$request_uri;
}

listen 443 ssl;
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

Depois reiniciar:
```bash
docker-compose restart nginx
```

---

## 🔐 SSL/HTTPS com Let's Encrypt

### Opção 1: Certbot com Docker

```bash
# Instalar Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Gerar certificado
sudo certbot certonly --standalone -d seu-dominio.com.br

# Copiar para container
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/fullchain.pem /opt/comissao-app/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/seu-dominio.com.br/privkey.pem /opt/comissao-app/nginx/ssl/key.pem

# Permissões
sudo chmod 644 /opt/comissao-app/nginx/ssl/*
```

### Opção 2: Auto-renewal

```bash
# Criar script
sudo nano /usr/local/bin/renew-ssl.sh
```

```bash
#!/bin/bash
certbot renew --quiet
cp /etc/letsencrypt/live/seu-dominio.com.br/fullchain.pem /opt/comissao-app/nginx/ssl/cert.pem
cp /etc/letsencrypt/live/seu-dominio.com.br/privkey.pem /opt/comissao-app/nginx/ssl/key.pem
docker-compose -f /opt/comissao-app/docker-compose.yml restart nginx
```

```bash
# Agendar renovação automática
sudo chmod +x /usr/local/bin/renew-ssl.sh
sudo crontab -e
# Adicionar: 0 0 * * * /usr/local/bin/renew-ssl.sh
```

---

## 🛠️ Troubleshooting

### Container não inicia

```bash
# Ver erro
docker-compose logs app

# Verificar arquivo .env
cat .env

# Verificar permissões
ls -la /opt/comissao-app/
```

### Erro de conexão com MongoDB

```bash
# Verificar MongoDB
docker-compose logs mongodb

# Testar conexão
docker exec comissao-app mongosh "mongodb://admin:senha@mongodb:27017/comissao_db"

# Verificar senha em .env
grep MONGO_PASSWORD .env
```

### Porta já em uso

```bash
# Ver quem está usando porta 5000
sudo lsof -i :5000

# Mudar porta em docker-compose.yml
# Alterar: ports: - "8000:5000"
docker-compose up -d
```

### Performance lenta

```bash
# Ver uso de recursos
docker stats

# Aumentar workers em .env
WORKERS=8

# Reiniciar
docker-compose restart app
```

---

## 📈 Escalabilidade

### Aumentar capacidade

```bash
# Aumentar workers
# Editar .env:
WORKERS=8  # de 4 para 8

# Aumentar memória MongoDB
# Editar docker-compose.yml:
mem_limit: 2g

docker-compose restart
```

### Load Balancer (nginx)

```nginx
upstream app {
    server app1:5000;
    server app2:5000;
    server app3:5000;
    least_conn;  # balanceamento por conexões
}
```

---

## 🔔 Alertas e Notificações

### Health check automático

```bash
# Script de monitoramento
nano /usr/local/bin/monitor-comissao.sh
```

```bash
#!/bin/bash
while true; do
    if ! curl -s http://localhost:5000/api/saude > /dev/null; then
        echo "ALERTA: Aplicação indisponível!" 
        # Enviar email/Slack/etc
        docker-compose restart app
    fi
    sleep 60
done
```

---

## 📊 Logs e Relatórios

### Exportar logs

```bash
# Logs dos últimos 7 dias
docker logs --since 7d comissao-app > app-logs-7d.txt

# Buscar erros
docker logs comissao-app | grep ERROR

# Filtrar por tempo
docker logs --until 1h --since 2h comissao-app
```

---

## 🗑️ Limpeza

### Remover containers antigos

```bash
# Listar containers parados
docker container ls -a

# Remover
docker container prune -f

# Remover imagens não usadas
docker image prune -a -f

# Remover volumes órfãos
docker volume prune -f
```

---

## 📞 Suporte e Documentação

- **GitHub**: https://github.com/escoobi/commissar-sistema-v2
- **Issues**: Report bugs em Issues
- **Logs**: `/opt/comissao-app/logs/`
- **Config**: `/opt/comissao-app/.env`

---

## ✅ Checklist Pós-Deploy

- [ ] Aplicação acessível em `http://server-ip:5000`
- [ ] MongoDB conectado e funcional
- [ ] Endpoint `/api/saude` retorna status
- [ ] Logs sem erros: `docker-compose logs app`
- [ ] Arquivo `.env` configurado corretamente
- [ ] Backup automático agendado
- [ ] SSL/HTTPS configurado (se usar domínio)
- [ ] Firewall liberado para portas 80 e 443
- [ ] Monitoramento ativo

---

**Criado em**: 2026-01-05  
**Última atualização**: 2026-01-05  
**Versão**: 2.0
