# -*- coding: utf-8 -*-
"""
Serviço para gerar relatórios em PDF
"""

from datetime import datetime
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def gerar_pdf_comissoes(resumo_vendedor, nome_arquivo="comissoes.pdf"):
    """
    Gera PDF com resumo de comissões
    
    Args:
        resumo_vendedor: Lista de dicts com dados dos vendedores
        nome_arquivo: Nome do arquivo PDF a gerar
    
    Returns:
        BytesIO com conteúdo do PDF
    """
    import sys
    
    try:
        logger.info(f"[PDF_GEN] Iniciando geração de PDF...")
        logger.info(f"[PDF_GEN] Python: {sys.executable}")
        logger.info(f"[PDF_GEN] sys.path: {sys.path[:3]}...")  # Log primeiras 3 linhas
        
        # Importa reportlab aqui para garantir que está disponível
        logger.info("[PDF_GEN] Tentando importar reportlab...")
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        
        logger.info("[PDF_GEN] ReportLab importado com sucesso")
        
        # Cria buffer para PDF
        buffer = BytesIO()
        
        # Cria documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=6,
            alignment=1,  # TA_CENTER = 1
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=12,
            alignment=1  # TA_CENTER = 1
        )
        
        # Conteúdo do PDF
        elements = []
        
        # Título
        elements.append(Paragraph("RELATÓRIO DE COMISSÕES", title_style))
        elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Prepara dados para tabela
        data = [['Vendedor', 'Total Comissões', 'Quantidade', 'Média']]
        
        total_geral = 0
        quantidade_geral = 0
        
        # Estilo para texto nas células (permite quebra de linha)
        cell_style = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontSize=9,
            leading=11
        )
        
        for item in resumo_vendedor:
            nome = item.get('vendor_name', 'Desconhecido')
            total = float(item.get('total_comissoes', 0))
            qtd = int(item.get('quantidade_propostas', 0))
            media = total / qtd if qtd > 0 else 0
            
            total_geral += total
            quantidade_geral += qtd
            
            # Formata valores
            total_fmt = f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            media_fmt = f"R$ {media:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            # Cria Paragraph para o nome para permitir quebra de linha
            nome_paragraph = Paragraph(nome, cell_style)
            
            data.append([
                nome_paragraph,
                total_fmt,
                str(qtd),
                media_fmt
            ])
        
        # Linha de total
        total_geral_fmt = f"R$ {total_geral:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        data.append([
            'TOTAL',
            total_geral_fmt,
            str(quantidade_geral),
            ''
        ])
        
        # Cria tabela com coluna de vendedor mais larga
        table = Table(data, colWidths=[7.5*cm, 3.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinha texto ao topo
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(table)
        
        # Constrói PDF
        doc.build(elements)
        buffer.seek(0)
        
        logger.info("[PDF_GEN] PDF de comissões gerado com sucesso")
        return buffer
        
    except ImportError as e:
        # Se reportlab não estiver instalado ou houver erro de importação
        logger.error(f"[PDF_GEN] ImportError ao importar ReportLab: {str(e)}", exc_info=True)
        import sys
        logger.error(f"[PDF_GEN] Python: {sys.executable}")
        logger.error(f"[PDF_GEN] sys.path (primeiras 5 linhas): {sys.path[:5]}")
        # Tenta dar mais detalhes sobre o que falhou
        raise Exception(f"Erro ao importar ReportLab: {str(e)}. Verifique se ReportLab está instalado corretamente com: pip install reportlab")
    except Exception as e:
        # Qualquer outro erro
        logger.error(f"[PDF_GEN] Erro geral ao gerar PDF: {str(e)}", exc_info=True)
        raise Exception(f"Erro ao gerar PDF: {str(e)}")
