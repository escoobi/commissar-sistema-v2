# -*- coding: utf-8 -*-
"""
Verificador de dependências
"""

import logging

logger = logging.getLogger(__name__)

def verificar_reportlab():
    """Verifica se ReportLab está disponível"""
    try:
        import reportlab
        version = reportlab.Version
        logger.info(f"ReportLab {version} disponível")
        return True, version
    except ImportError as e:
        logger.error(f"ReportLab não disponível: {str(e)}")
        return False, None

def verificar_pillow():
    """Verifica se Pillow está disponível (dependência do ReportLab)"""
    try:
        import PIL
        version = PIL.__version__
        logger.info(f"Pillow {version} disponível")
        return True, version
    except ImportError as e:
        logger.error(f"Pillow não disponível: {str(e)}")
        return False, None

# Verifica na inicialização
if __name__ == "__main__":
    reportlab_ok, reportlab_version = verificar_reportlab()
    pillow_ok, pillow_version = verificar_pillow()
    
    print(f"ReportLab: {reportlab_ok} ({reportlab_version})")
    print(f"Pillow: {pillow_ok} ({pillow_version})")
