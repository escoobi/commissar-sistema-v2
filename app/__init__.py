# -*- coding: utf-8 -*-
"""
Fábrica de aplicação Flask
"""

import os
import logging
import sys
from flask import Flask
from flask_pymongo import PyMongo
from logging.handlers import RotatingFileHandler

# Instância do MongoDB
mongo = PyMongo()

def _check_dependencies():
    """Verifica dependências críticas na inicialização"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Verificação de dependências na inicialização")
    logger.info("=" * 60)
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    
    # Teste ReportLab
    try:
        import reportlab
        logger.info(f"✓ ReportLab disponível: {reportlab.Version}")
    except ImportError as e:
        logger.error(f"✗ ReportLab NÃO disponível: {e}")
    except Exception as e:
        logger.error(f"✗ Erro ao verificar ReportLab: {e}")
    
    # Teste Pillow
    try:
        import PIL
        logger.info(f"✓ Pillow disponível: {PIL.__version__}")
    except ImportError as e:
        logger.error(f"✗ Pillow NÃO disponível: {e}")
    except Exception as e:
        logger.error(f"✗ Erro ao verificar Pillow: {e}")
    
    # Teste Pandas
    try:
        import pandas
        logger.info(f"✓ Pandas disponível: {pandas.__version__}")
    except ImportError as e:
        logger.error(f"✗ Pandas NÃO disponível: {e}")
    
    logger.info("=" * 60)

def create_app(config_name='development'):
    """Cria e configura a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Verifica dependências críticas (comentado - pode travar em inicializações)
    # _check_dependencies()
    
    # Configurações
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/comissao_db')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './uploads')
    
    # Criar pasta de uploads se não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Inicializa MongoDB
    mongo.init_app(app)
    
    # Desabilita cache para modo desenvolvimento
    @app.after_request
    def disable_cache(response):
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.cache_control.max_age = 0
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # Setup de logging
    _setup_logging(app)
    
    # Registra blueprints
    _register_blueprints(app)
    
    # Registra tratamento de erros
    _register_error_handlers(app)
    
    # Registra CLI commands
    _register_cli_commands(app)
    
    return app


def _setup_logging(app):
    """Configura logging da aplicação"""
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/comissao.log',
        maxBytes=10240000,
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Sistema de Comissão iniciado')


def _register_blueprints(app):
    """Registra blueprints (rotas)"""
    
    from app.routes import main_bp, api_bp, upload_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(upload_bp, url_prefix='/upload')


def _register_error_handlers(app):
    """Registra tratamento de erros"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Página não encontrada'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Erro interno: {error}')
        return {'error': 'Erro interno do servidor'}, 500


def _register_cli_commands(app):
    """Registra comandos CLI"""
    
    @app.cli.command()
    def init_db():
        """Inicializa o banco de dados"""
        print("Inicializando banco de dados...")
        # Aqui você pode criar índices, coleções iniciais, etc
        print("✓ Banco de dados inicializado")
