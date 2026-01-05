FROM python:3.11-slim

# Labels
LABEL maintainer="Sistema de Comissão v2.0"
LABEL description="Sistema de Processamento de Comissões - Flask/MongoDB"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements-production.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements-production.txt

# Copiar código
COPY . .

# Criar diretórios
RUN mkdir -p logs uploads

# Expor porta
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/saude')" || exit 1

# Comando para iniciar
CMD ["gunicorn", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "run:app"]
