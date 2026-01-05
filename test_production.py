#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Teste Pré-Produção
Valida configurações e funcionalidades críticas
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Cores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
CHECK = '✅'
CROSS = '❌'
WARN = '⚠️'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_test(name, passed, message=""):
    status = f"{CHECK} {GREEN}PASSOU{RESET}" if passed else f"{CROSS} {RED}FALHOU{RESET}"
    msg = f" - {message}" if message else ""
    print(f"  {status} {name}{msg}")
    return passed

def print_warning(text):
    print(f"  {WARN} {YELLOW}{text}{RESET}")

# =====================================================
# TESTES PRÉ-PRODUÇÃO
# =====================================================

print_header("🚀 TESTES PRÉ-PRODUÇÃO - SISTEMA DE COMISSÃO v2.0")

all_passed = True

# =====================================================
# 1. Verificar Variáveis de Ambiente
# =====================================================

print(f"{BLUE}1️⃣  VARIÁVEIS DE AMBIENTE{RESET}\n")

load_dotenv('.env')

required_vars = {
    'FLASK_APP': 'run.py',
    'FLASK_ENV': 'production',
    'FLASK_DEBUG': 'False',
    'MONGO_URI': 'mongodb://...',
    'SECRET_KEY': 'chave-segura',
    'LOG_LEVEL': 'INFO',
}

for var, expected in required_vars.items():
    value = os.getenv(var, 'NÃO DEFINIDO')
    
    # Validações específicas
    if var == 'FLASK_DEBUG':
        passed = value == 'False'
        msg = f"Valor: {value}"
    elif var == 'FLASK_ENV':
        passed = value == 'production'
        msg = f"Valor: {value}"
    elif var == 'SECRET_KEY':
        passed = len(value) >= 32 and value != 'seu-secret-key-aqui'
        msg = f"Comprimento: {len(value)} caracteres"
    elif var == 'MONGO_URI':
        passed = 'mongodb' in value and 'comissao_db' in value
        msg = f"Acessível"
    else:
        passed = value != 'NÃO DEFINIDO' and value != expected
        msg = f"Definido"
    
    all_passed &= print_test(f"{var}", passed, msg)

# =====================================================
# 2. Verificar Estrutura de Diretórios
# =====================================================

print(f"\n{BLUE}2️⃣  ESTRUTURA DE DIRETÓRIOS{RESET}\n")

required_dirs = [
    'app',
    'logs',
    'uploads',
    'docs'
]

for dir_name in required_dirs:
    dir_path = Path(dir_name)
    exists = dir_path.exists()
    all_passed &= print_test(f"Diretório: {dir_name}/", exists)
    
    if exists and dir_name in ['logs', 'uploads']:
        # Verificar permissões
        try:
            test_file = dir_path / '.write_test'
            test_file.touch()
            test_file.unlink()
            print_test(f"  ↳ Permissão de escrita", True)
        except:
            print_test(f"  ↳ Permissão de escrita", False)
            all_passed = False

# =====================================================
# 3. Verificar Dependências
# =====================================================

print(f"\n{BLUE}3️⃣  DEPENDÊNCIAS PYTHON{RESET}\n")

required_packages = {
    'flask': 'Flask',
    'pymongo': 'PyMongo',
    'pandas': 'Pandas',
    'dotenv': 'python-dotenv',
    'werkzeug': 'Werkzeug',
}

for module, name in required_packages.items():
    try:
        __import__(module)
        all_passed &= print_test(f"{name}", True, "Instalado")
    except ImportError:
        all_passed &= print_test(f"{name}", False, "NÃO INSTALADO")

# =====================================================
# 4. Verificar Banco de Dados
# =====================================================

print(f"\n{BLUE}4️⃣  CONECTIVIDADE MONGODB{RESET}\n")

try:
    from pymongo import MongoClient, __version__
    
    mongo_uri = os.getenv('MONGO_URI')
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    # Testar conexão
    client.admin.command('ping')
    all_passed &= print_test("Conexão MongoDB", True, "Banco acessível")
    
    # Verificar banco de dados
    db = client['comissao_db']
    collections = db.list_collection_names()
    print_test("Coleções encontradas", len(collections) > 0, f"{len(collections)} coleções")
    
    # Listar coleções
    for col in collections:
        count = db[col].count_documents({})
        print(f"    ↳ {col}: {count} documentos")
    
    client.close()
    
except Exception as e:
    all_passed = False
    print_test("Conexão MongoDB", False, str(e)[:50])

# =====================================================
# 5. Verificar Aplicação Flask
# =====================================================

print(f"\n{BLUE}5️⃣  APLICAÇÃO FLASK{RESET}\n")

try:
    from app import create_app
    
    app = create_app('production')
    all_passed &= print_test("App criada com sucesso", True)
    
    # Verificar rotas
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        print_test("Rotas definidas", len(routes) > 5, f"{len(routes)} endpoints")
        
        # Verificar endpoint crítico
        with app.test_client() as client:
            try:
                response = client.get('/api/saude')
                if response.status_code == 200:
                    data = response.get_json()
                    all_passed &= print_test("Endpoint /api/saude", True, "Status 200")
                else:
                    all_passed &= print_test("Endpoint /api/saude", False, f"Status {response.status_code}")
            except Exception as e:
                all_passed &= print_test("Endpoint /api/saude", False, str(e)[:40])

except Exception as e:
    all_passed = False
    print_test("Aplicação Flask", False, str(e)[:50])

# =====================================================
# 6. Verificar Arquivos de Configuração
# =====================================================

print(f"\n{BLUE}6️⃣  ARQUIVOS DE CONFIGURAÇÃO{RESET}\n")

required_files = {
    'run.py': 'Entrada da aplicação',
    'requirements.txt': 'Dependências',
    '.env': 'Variáveis de ambiente',
    'app/__init__.py': 'Módulo Flask',
}

for file, desc in required_files.items():
    file_path = Path(file)
    exists = file_path.exists()
    all_passed &= print_test(f"{file}", exists, desc)

# =====================================================
# 7. Verificar Documentação
# =====================================================

print(f"\n{BLUE}7️⃣  DOCUMENTAÇÃO{RESET}\n")

doc_files = {
    'README.md': 'Documentação principal',
    'DOCUMENTACAO.md': 'Referência técnica',
    'DEPLOYMENT_GUIDE.md': 'Guia de produção',
    'PRE_DEPLOYMENT_CHECKLIST.md': 'Checklist',
}

for file, desc in doc_files.items():
    file_path = Path(file)
    exists = file_path.exists()
    if exists:
        size = file_path.stat().st_size / 1024  # KB
        msg = f"{desc} ({size:.1f} KB)"
    else:
        msg = desc
    all_passed &= print_test(f"{file}", exists, msg)

# =====================================================
# 8. Verificar Segurança
# =====================================================

print(f"\n{BLUE}8️⃣  SEGURANÇA{RESET}\n")

secret_key = os.getenv('SECRET_KEY', '')
debug_mode = os.getenv('FLASK_DEBUG', 'True') == 'False'
env_prod = os.getenv('FLASK_ENV', '') == 'production'

security_ok = True
security_ok &= print_test("FLASK_DEBUG desativado", debug_mode)
security_ok &= print_test("FLASK_ENV=production", env_prod)
security_ok &= print_test("SECRET_KEY segura", len(secret_key) >= 32, f"Comprimento: {len(secret_key)}")

all_passed &= security_ok

# =====================================================
# RESUMO FINAL
# =====================================================

print(f"\n{BLUE}{'='*60}{RESET}")

if all_passed:
    print(f"{GREEN}✅ TODOS OS TESTES PASSARAM - PRONTO PARA PRODUÇÃO!{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    print("📋 Próximos passos:\n")
    print("  1. Revisar PRE_DEPLOYMENT_CHECKLIST.md")
    print("  2. Executar: pip install -r requirements-production.txt")
    print("  3. Testar com Gunicorn: gunicorn --workers 4 --bind 0.0.0.0:5000 run:app")
    print("  4. Configurar Nginx/Systemd (ver DEPLOYMENT_GUIDE.md)")
    print("  5. Realizar testes de carga e funcionalidade")
    print("  6. Deploy!\n")
    
    sys.exit(0)
else:
    print(f"{RED}❌ ALGUNS TESTES FALHARAM - REVISAR ANTES DE PRODUÇÃO{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    print("🔧 Ações necessárias:\n")
    print("  1. Revisar os testes que falharam acima")
    print("  2. Consultar DEPLOYMENT_GUIDE.md para instruções")
    print("  3. Repetir este teste após correções")
    print("  4. Não fazer deploy até todos os testes passarem\n")
    
    sys.exit(1)
