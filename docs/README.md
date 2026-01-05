# 🎉 Sistema de Processamento de Comissão v2.0

**Python/Flask/MongoDB/Pandas/Bulma CSS**

Uma refatoração completa do sistema original de processamento de comissões para a Honda Rondo Motos, agora com tecnologia moderna em Python.

## ✨ Características

- ✅ **Python 3.9+** — Backend moderno e escalável
- ✅ **Flask** — Framework web leve e poderoso
- ✅ **MongoDB** — Banco de dados NoSQL flexível
- ✅ **Pandas** — Processamento eficiente de dados CSV/XLSX
- ✅ **Bulma CSS** — Interface responsiva e moderna
- ✅ **RESTful API** — Endpoints bem estruturados
- ✅ **Logging** — Rastreabilidade completa
- ✅ **Testes** — Cobertura de funcionalidades críticas

## 📦 Instalação

### 1. Pré-requisitos
- Python 3.9+
- MongoDB 4.4+
- pip (gerenciador de pacotes Python)

### 2. Clonar/Baixar o projeto
```bash
cd seu-projeto-comissao
```

### 3. Criar ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar dependências
```bash
pip install -r requirements.txt
```

### 5. Configurar variáveis de ambiente
```bash
# Copiar .env.example para .env
cp .env.example .env

# Editar .env com suas configurações
# MONGO_URI=mongodb://localhost:27017/comissao_db
# FLASK_ENV=development
# FLASK_DEBUG=True
```

### 6. Criar pasta de uploads
```bash
mkdir uploads
mkdir logs
```

## 🚀 Como Executar

### Iniciação rápida
```bash
python run.py
```

A aplicação será acessível em: **http://localhost:5000**

### Com Flask CLI
```bash
flask run
```

### Com configurações customizadas
```bash
FLASK_ENV=production FLASK_DEBUG=False python run.py
```

## 📁 Estrutura do Projeto

```
sas-comissao/
├── app/
│   ├── __init__.py              # Factory da aplicação
│   ├── config.py                # Configurações
│   ├── routes.py                # Rotas (blueprints)
│   ├── models/
│   │   └── __init__.py          # Modelos de dados (MongoDB)
│   ├── services/
│   │   └── __init__.py          # Serviços de negócio
│   ├── utils/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │       └── main.js          # JavaScript principal
│   └── templates/
│       ├── base.html            # Template base (Bulma)
│       ├── index.html           # Página inicial
│       ├── processar.html       # Upload de arquivos
│       ├── relatorios.html      # Relatórios
│       └── vendedores.html      # Listagem de vendedores
├── tests/
│   └── test_app.py              # Testes unitários
├── uploads/                      # Pasta para arquivos enviados
├── logs/                         # Logs da aplicação
├── requirements.txt             # Dependências Python
├── run.py                       # Ponto de entrada
├── .env.example                 # Variáveis de ambiente (exemplo)
├── .gitignore                   # Git ignore
└── README.md                    # Este arquivo
```

## 🔧 Configuração do MongoDB

### Instalação (Windows)
1. Baixar em: https://www.mongodb.com/try/download/community
2. Executar instalador
3. Iniciar serviço: `net start MongoDB`

### Instalação (Linux/Mac)
```bash
# Mac com Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Linux (Ubuntu)
sudo apt-get install -y mongodb
sudo systemctl start mongodb
```

### Verificar conexão
```bash
mongosh
# ou
mongo
```

## 📚 Endpoints da API

### Rotas principais
- `GET /` — Página inicial
- `GET /processar` — Página de upload
- `GET /relatorios` — Relatórios
- `GET /vendedores` — Lista de vendedores

### API REST
- `GET /api/comissoes` — Lista comissões (paginado)
- `GET /api/resumo/vendedor` — Resumo por vendedor
- `GET /api/resumo/cidade` — Resumo por cidade
- `POST /api/calcular-comissao` — Calcula comissão
- `POST /upload/saida` — Upload de arquivo saida.csv
- `POST /upload/proposta` — Upload de arquivo proposta.csv

## 📝 Exemplos de Uso

### Upload de arquivo via cURL
```bash
curl -X POST -F "arquivo=@saida.csv" http://localhost:5000/upload/saida
```

### Obter comissões via API
```bash
curl http://localhost:5000/api/comissoes?page=1&per_page=20
```

### Calcular comissão
```bash
curl -X POST http://localhost:5000/api/calcular-comissao \
  -H "Content-Type: application/json" \
  -d '{
    "proposta": {"id": "123", "valor_venda": 15000, "vendedor": "João"},
    "valor_meta": 15000,
    "alta_cilindrada": false
  }'
```

## 🧪 Testes

### Executar todos os testes
```bash
python -m pytest
```

### Executar testes específicos
```bash
python -m pytest tests/test_app.py -v
```

### Com cobertura
```bash
python -m pytest --cov=app tests/
```

## 📊 Regras de Negócio

### Cálculo de Comissão

**Alta CC:**
- ≥ 97% da meta: 1.2%
- < 97% da meta: 0.8%

**Outros Modelos:**
- ≥ 100% da meta: 2.0%
- 97% a 99.999% da meta: 1.6%
- 95% a 96.999% da meta: 1.2%
- ≤ 94.999% da meta: 1.0%

## 🔐 Segurança

- Valide sempre os uploads (tipo, tamanho)
- Use `.env` para variáveis sensíveis
- Configure `SECRET_KEY` forte em produção
- Implemente autenticação (future release)
- Use HTTPS em produção

## 📈 Performance

- MongoDB com índices em campos frequentes
- Cache de relatórios (future)
- Paginação em listas grandes
- Compressão Gzip habilitada

## 🐛 Troubleshooting

### MongoDB não conecta
```bash
# Verificar se MongoDB está rodando
mongosh
# Se não funcionar, reiniciar serviço
net start MongoDB  # Windows
sudo systemctl restart mongodb  # Linux
```

### Erro de permissão em uploads
```bash
# Criar pasta com permissões
mkdir -p uploads
chmod 755 uploads
```

### Porta 5000 já em uso
```bash
# Usar outra porta
FLASK_PORT=8000 python run.py
```

## 🚀 Deploy

### Heroku
```bash
heroku create sua-app
git push heroku main
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## 📝 Changelog

### v2.0.0 (24/12/2025)
- ✨ Refatoração completa para Python/Flask
- ✨ MongoDB em vez de Java/Servlets
- ✨ Pandas para processamento de dados
- ✨ Bulma CSS para interface moderna
- ✨ API REST estruturada
- ✨ Testes automatizados

## 📞 Suporte

Para problemas ou sugestões:
1. Verificar logs em `logs/comissao.log`
2. Verificar console de erros (F12 no browser)
3. Consultar documentação em `/docs` (future)

## 📄 Licença

Proprietary - Honda Rondo Motos 2025

## 👥 Autores

- **Desenvolvimento:** Tim Copilot
- **Baseado em:** Sistema original Java/Servlets
- **Tecnologia:** Python 3.9+ / Flask / MongoDB / Pandas / Bulma CSS

---

**Versão:** 2.0.0  
**Data:** 24 de dezembro de 2025  
**Status:** ✅ Produção  
**Python:** 3.9+
