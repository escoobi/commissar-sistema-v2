#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplicação Flask para Sistema de Processamento de Comissão
Honda Rondo Motos v2.0 (Python/MongoDB/Pandas)
"""

import os
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

from app import create_app

# Cria a aplicação
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'False') == 'True'
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║     Sistema de Processamento de Comissão v2.0              ║
    ║     Honda Rondo Motos - Python/Flask/MongoDB               ║
    ╚════════════════════════════════════════════════════════════╝
    
    🚀 Iniciando aplicação...
    📍 http://localhost:{port}
    🔧 Debug: {debug}
    """)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
