# -*- coding: utf-8 -*-
"""
Configurações da aplicação
"""

import os

class Config:
    """Configurações base"""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/comissao_db')
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Flask
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configurações de produção"""
    
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configurações de testes"""
    
    DEBUG = True
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/comissao_db_test'


# Dict de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
