# ✅ Checklist Pré-Deployment

## 🔐 Segurança

- [ ] **SECRET_KEY alterado**
  - Gerar novo com: `python -c "import os; print(os.urandom(32).hex())"`
  - Adicionar em `.env.production`
  
- [ ] **Credenciais de banco de dados**
  - MONGO_URI não contém valores padrão/teste
  - URI aponta para produção
  - Senha/usuário seguros no MongoDB
  
- [ ] **CORS configurado**
  - `CORS_ORIGINS` definido para domínios específicos
  - Não usar `*` em produção
  
- [ ] **Debug desativado**
  - `FLASK_DEBUG=False`
  - `FLASK_ENV=production`
  
- [ ] **HTTPS/SSL ativo**
  - Certificado válido instalado
  - Redirecionamento HTTP → HTTPS configurado

---

## 🗄️ Banco de Dados

- [ ] **MongoDB acessível**
  - Teste: `mongo --eval "db.adminCommand('ping')"`
  
- [ ] **Índices criados**
  ```javascript
  // Executar no MongoDB
  db.propostas.createIndex({ "vendedor": 1 })
  db.propostas.createIndex({ "data_criacao": -1 })
  db.vendedores.createIndex({ "nome": 1 })
  ```
  
- [ ] **Backup agendado**
  - Script cron configurado
  - Diretório de backup criado
  - Permissões corretas
  
- [ ] **Dados de produção carregados**
  - Estrutura de coleções OK
  - Não há dados de teste

---

## 🧪 Testes

- [ ] **API testada**
  ```bash
  curl http://localhost:5000/api/saude
  # Esperado: {"status":"ok"}
  ```
  
- [ ] **Endpoints principais testados**
  - [ ] GET /api/resumo/vendedor
  - [ ] POST /api/processar-comissoes
  - [ ] GET /api/relatorio/vendedor/{id}
  
- [ ] **Upload de arquivos funciona**
  - [ ] CSV processado corretamente
  - [ ] Limite de tamanho OK
  
- [ ] **Cálculo HP12C verificado**
  - [ ] Fórmula PV = PMT / [(1 - (1 + i)^-n) / i] funciona
  - [ ] Resultados batendo com testes

---

## 📦 Dependências

- [ ] **requirements-production.txt atualizado**
  - Versões pinadas
  - Sem pacotes de desenvolvimento
  
- [ ] **Virtual environment testado**
  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements-production.txt
  python run.py
  ```

---

## 📝 Configuração

- [ ] **.env.production preparado**
  - [ ] FLASK_APP=run.py
  - [ ] FLASK_ENV=production
  - [ ] FLASK_DEBUG=False
  - [ ] SECRET_KEY (gerado novo)
  - [ ] MONGO_URI (produção)
  - [ ] UPLOAD_FOLDER (caminho correto)
  - [ ] LOG_LEVEL=INFO
  - [ ] FLASK_PORT=5000
  - [ ] WORKERS=4
  
- [ ] **Diretórios criados**
  - [ ] /uploads (permissões 755)
  - [ ] /logs (permissões 755)
  - [ ] /backups (permissões 700)

---

## 🚀 Servidor

- [ ] **Gunicorn testado**
  ```bash
  gunicorn --workers 4 --bind 0.0.0.0:5000 run:app
  ```
  
- [ ] **Nginx configurado (se aplicável)**
  - [ ] Reverse proxy apontando para Flask
  - [ ] SSL configurado
  - [ ] Compressão ativada
  
- [ ] **Systemd service criado**
  - [ ] Arquivo `/etc/systemd/system/comissao.service`
  - [ ] Service iniciando com boot
  - [ ] Restart automático configurado

---

## 📊 Logs e Monitoramento

- [ ] **Logs configurados**
  - [ ] Diretório: `/opt/comissao-app/logs`
  - [ ] Rotação configurada
  - [ ] Nível: INFO em produção
  
- [ ] **Health check endpoint funciona**
  ```bash
  curl https://seu-dominio.com/api/saude
  ```
  
- [ ] **Monitoramento ativo**
  - [ ] Alertas configurados
  - [ ] CPU/Memória sob controle
  - [ ] Disco com espaço

---

## 📄 Documentação

- [ ] **Documentação de produção**
  - [ ] README.md atualizado
  - [ ] DEPLOYMENT_GUIDE.md consultado
  - [ ] Runbook preparado para equipe de ops
  
- [ ] **Credenciais documentadas (seguro)**
  - [ ] Admin password manager configurado
  - [ ] Acesso restrito
  - [ ] Rotação de senhas agendada

---

## 🔄 Plano de Rollback

- [ ] **Git tags criadas**
  ```bash
  git tag -a v1.0-production -m "Production release"
  ```
  
- [ ] **Backup pré-produção**
  - [ ] MongoDB dump feito
  - [ ] Armazenado seguramente
  
- [ ] **Procedimento de rollback documentado**
  - [ ] Passos claros
  - [ ] Tempo estimado
  - [ ] Responsável definido

---

## 👥 Equipe

- [ ] **Desenvolvedores informados**
  - [ ] Novos ambientes conhecidos
  - [ ] Processo de deploy claro
  
- [ ] **DevOps/SysAdmin preparado**
  - [ ] Acesso ao servidor
  - [ ] Documentação recebida
  - [ ] Contatos de emergência definidos
  
- [ ] **Stakeholders informados**
  - [ ] Data/hora do deployment comunicada
  - [ ] Plano de comunicação definido
  - [ ] Cronograma de testes definido

---

## 🎯 Acompanhamento Pós-Deploy (Primeiras 24h)

- [ ] **Monitorar logs continuamente**
- [ ] **Verificar performance**
- [ ] **Testar funcionalidades críticas**
- [ ] **Comunicar status às partes interessadas**
- [ ] **Estar pronto para rollback se necessário**

---

## ✨ Pronto para Produção?

**Sim** ✅ - Prosseguir com deployment  
**Não** ❌ - Resolver pontos pendentes antes

---

**Data do Checklist:** 2026-01-05  
**Responsável:** ________________  
**Data Assinatura:** ________________  
