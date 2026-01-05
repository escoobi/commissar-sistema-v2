# -*- coding: utf-8 -*-
"""
Rotas da aplicação
"""

from flask import Blueprint, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
from app import mongo
from app.services import ComissaoService, CSVProcessadorService, RelatorioService, VendedorService, MotoService, FormaRecebimentoService, ValorPresenteService
from app.models import PropostaModel, ComissaoModel, VendedorModel, MotoModel, FormaRecebimentoModel
from app.utils.pdf_generator import gerar_pdf_comissoes


logger = logging.getLogger(__name__)

# Blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)
upload_bp = Blueprint('upload', __name__)


# ========== ROTAS PRINCIPAIS ==========

@main_bp.route('/limpar', methods=['POST'])
def limpar_dados():
    """Limpa os dados do MongoDB"""
    
    try:
        mongo.db.saida.delete_many({})
        mongo.db.propostas.delete_many({})
        
        logger.info("Dados limpos com sucesso")
        
        return jsonify({'status': 'sucesso', 'mensagem': 'Dados limpos'})
        
    except Exception as e:
        logger.error(f"Erro ao limpar dados: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@main_bp.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')


@main_bp.route('/vendedores')
def vendedores():
    """Lista de vendedores (admin)"""
    return render_template('vendedores_admin.html')


@main_bp.route('/motos')
def motos():
    """Lista de motos (admin)"""
    return render_template('motos_admin.html')


@main_bp.route('/processar')
def processar():
    """Página de processamento"""
    return render_template('processar.html')


@main_bp.route('/relatorios')
def relatorios():
    """Página de relatórios"""
    return render_template('relatorios.html')


# ========== ROTAS API ==========

@api_bp.route('/comissoes', methods=['GET'])
def get_comissoes():
    """Lista comissões"""
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Busca de propostas que têm os dados mais completos
        collection = mongo.db.propostas
        total = collection.count_documents({})
        
        skip = (page - 1) * per_page
        comissoes = list(collection.find({}).skip(skip).limit(per_page))
        
        # Converte ObjectId para string e calcula comissão
        for c in comissoes:
            if '_id' in c:
                c['_id'] = str(c['_id'])
            # Calcula comissão básica (assumindo 100% de meta, buscando do banco)
            valor = float(c.get('proposal_value', 0))
            modelo = str(c.get('model', 'Outro')).upper()
            eh_ac = 'AC' in modelo
            aliquota = ComissaoService._obter_aliquota_banco(mongo.db, 100, eh_ac)
            c['comissao'] = round(valor * aliquota, 2)
            c['aliquota'] = aliquota * 100
        
        return jsonify({
            'status': 'sucesso',
            'dados': comissoes,
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar comissões: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/vendedores', methods=['GET'])
def listar_vendedores():
    """Lista todos os vendedores"""
    try:
        status = request.args.get('status', 'ativo')
        vendedores = VendedorService.listar_vendedores(status)
        return jsonify({'status': 'sucesso', 'dados': vendedores})
    except Exception as e:
        logger.error(f"Erro ao listar vendedores: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/vendedores', methods=['POST'])
def criar_vendedor():
    """Cria um novo vendedor - DESABILITADO
    
    Vendedores são criados automaticamente via upload de saida.csv
    """
    return jsonify({'status': 'erro', 'mensagem': 'Vendedores só podem ser criados via upload de saida.csv'}), 403


@api_bp.route('/vendedores/<vendor_id>', methods=['GET'])
def obter_vendedor(vendor_id):
    """Obtém um vendedor por ID"""
    try:
        vendedor = VendedorService.obter_vendedor(vendor_id)
        if not vendedor:
            return jsonify({'status': 'erro', 'mensagem': 'Vendedor não encontrado'}), 404
        
        return jsonify({'status': 'sucesso', 'dados': vendedor})
    except Exception as e:
        logger.error(f"Erro ao obter vendedor: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/vendedores/<vendor_id>', methods=['PUT'])
def atualizar_vendedor(vendor_id):
    """Atualiza um vendedor"""
    try:
        dados = request.json
        resultado = VendedorService.atualizar_vendedor(vendor_id, dados)
        
        if 'erro' in resultado:
            return jsonify({'status': 'erro', 'mensagem': resultado['erro']}), 400
        
        return jsonify({'status': 'sucesso', 'dados': resultado})
    except Exception as e:
        logger.error(f"Erro ao atualizar vendedor: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/vendedores/<vendor_id>', methods=['DELETE'])
def deletar_vendedor(vendor_id):
    """Deleta um vendedor"""
    try:
        resultado = VendedorService.deletar_vendedor(vendor_id)
        
        if 'erro' in resultado:
            return jsonify({'status': 'erro', 'mensagem': resultado['erro']}), 400
        
        return jsonify({'status': 'sucesso', 'dados': resultado})
    except Exception as e:
        logger.error(f"Erro ao deletar vendedor: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


# ========== ENDPOINTS DE MOTOS ==========

@api_bp.route('/motos', methods=['GET'])
def listar_motos():
    """Lista todas as motos"""
    try:
        status = request.args.get('status', 'ativo')
        motos = MotoService.listar_motos(status)
        return jsonify({'status': 'sucesso', 'dados': motos})
    except Exception as e:
        logger.error(f"Erro ao listar motos: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/motos', methods=['POST'])
def criar_moto():
    """Cria uma nova moto"""
    try:
        dados = request.json
        resultado = MotoService.criar_moto(dados)
        
        if 'erro' in resultado:
            return jsonify({'status': 'erro', 'mensagem': resultado['erro']}), 400
        
        return jsonify({'status': 'sucesso', 'dados': resultado}), 201
    except Exception as e:
        logger.error(f"Erro ao criar moto: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/motos/<moto_id>', methods=['GET'])
def obter_moto(moto_id):
    """Obtém uma moto por ID"""
    try:
        moto = MotoService.obter_moto(moto_id)
        if not moto:
            return jsonify({'status': 'erro', 'mensagem': 'Moto não encontrada'}), 404
        
        return jsonify({'status': 'sucesso', 'dados': moto})
    except Exception as e:
        logger.error(f"Erro ao obter moto: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/motos/<moto_id>', methods=['PUT'])
def atualizar_moto(moto_id):
    """Atualiza uma moto"""
    try:
        dados = request.json
        resultado = MotoService.atualizar_moto(moto_id, dados)
        
        if 'erro' in resultado:
            return jsonify({'status': 'erro', 'mensagem': resultado['erro']}), 400
        
        return jsonify({'status': 'sucesso', 'dados': resultado})
    except Exception as e:
        logger.error(f"Erro ao atualizar moto: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/motos/<moto_id>', methods=['DELETE'])
def deletar_moto(moto_id):
    """Deleta uma moto"""
    try:
        resultado = MotoService.deletar_moto(moto_id)
        
        if 'erro' in resultado:
            return jsonify({'status': 'erro', 'mensagem': resultado['erro']}), 400
        
        return jsonify({'status': 'sucesso', 'dados': resultado})
    except Exception as e:
        logger.error(f"Erro ao deletar moto: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/resumo/vendedor', methods=['GET'])
def resumo_vendedor():
    """Resumo de comissões por vendedor"""
    
    try:
        resumo = RelatorioService.resumo_comissoes()
        return jsonify({'status': 'sucesso', 'dados': resumo})
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo por vendedor: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/comissoes/processar', methods=['POST'])
def processar_comissoes():
    """Processa comissões, salva no banco e gera PDF"""
    
    try:
        logger.info("[COMISSOES] Iniciando processamento de comissões...")
        
        # Gera resumo das comissões
        resumo = RelatorioService.resumo_comissoes()
        logger.info(f"[COMISSOES] Resumo gerado com {len(resumo)} vendedores")
        
        if not resumo:
            return jsonify({'status': 'erro', 'mensagem': 'Nenhuma comissão para processar'}), 400
        
        # Salva as comissões no banco de dados
        comissoes_collection = mongo.db.comissoes
        
        # Remove comissões antigas (para garantir que não há duplicatas)
        comissoes_collection.delete_many({})
        logger.info("[COMISSOES] Comissões antigas removidas")
        
        # Insere as novas comissões
        documentos = []
        for item in resumo:
            doc = {
                'vendedor': item.get('vendor_name'),
                'total_vendas': float(item.get('total_vendas', 0)),
                'total_comissoes': float(item.get('total_comissoes', 0)),
                'quantidade_propostas': int(item.get('quantidade_propostas', 0)),
                'media_comissao': float(item.get('total_comissoes', 0)) / int(item.get('quantidade_propostas', 1)) if item.get('quantidade_propostas', 0) > 0 else 0,
                'eh_interno': item.get('eh_interno', False),
                'data_processamento': datetime.now()
            }
            documentos.append(doc)
        
        if documentos:
            comissoes_collection.insert_many(documentos)
            logger.info(f"[COMISSOES] {len(documentos)} comissões inseridas no banco")
        
        # Gera PDF
        logger.info("[COMISSOES] Iniciando geração de PDF...")
        try:
            pdf_buffer = gerar_pdf_comissoes(resumo)
            pdf_data = pdf_buffer.getvalue()
            logger.info(f"[COMISSOES] PDF gerado com sucesso: {len(pdf_data)} bytes")
            
            # Cria resposta com headers corretos para download de PDF
            response = Response(
                pdf_data,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': 'attachment; filename="comissoes.pdf"',
                    'Content-Length': len(pdf_data)
                }
            )
            logger.info("[COMISSOES] Retornando PDF ao cliente")
            return response
        except Exception as e:
            # Se houver erro ao gerar PDF, retorna sucesso mas avisa
            logger.error(f"[COMISSOES] Erro ao gerar PDF: {str(e)}", exc_info=True)
            import traceback
            tb = traceback.format_exc()
            logger.error(f"[COMISSOES] Traceback: {tb}")
            return jsonify({
                'status': 'sucesso_sem_pdf',
                'mensagem': f'Comissões salvas com sucesso, mas PDF não foi gerado. Erro: {str(e)}',
                'dados': resumo
            }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar comissões: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/vendedor/vendas', methods=['GET'])
def vendedor_vendas():
    """Retorna todas as vendas de um vendedor específico"""
    
    try:
        nome_vendedor = request.args.get('nome', '')
        
        if not nome_vendedor:
            return jsonify({'status': 'erro', 'mensagem': 'Nome do vendedor não informado'}), 400
        
        # Busca propostas do vendedor
        saida_col = mongo.db.saida
        proposta_col = mongo.db.propostas
        vendedor_col = mongo.db.vendedores
        
        # VALIDAÇÃO: Busca informações do vendedor NO BANCO DE DADOS
        vendedor_info = vendedor_col.find_one({'nome': nome_vendedor})
        
        # Se vendedor não existe no banco, retorna erro
        if not vendedor_info:
            return jsonify({
                'status': 'erro',
                'mensagem': f'Vendedor "{nome_vendedor}" não encontrado no banco de dados. Faça upload do arquivo saida.csv primeiro.'
            }), 404
        
        eh_interno = vendedor_info.get('interno', False)
        
        # Encontra todos os clientes (Pessoa) que esse vendedor vendeu
        clientes_do_vendedor = set()
        for doc in saida_col.find({'Vendedor': nome_vendedor}):
            pessoa = doc.get('Pessoa', '').strip()
            if pessoa:
                clientes_do_vendedor.add(pessoa)
        
        # Se não encontrou clientes, retorna vazio
        if not clientes_do_vendedor:
            return jsonify({'status': 'sucesso', 'dados': []})
        
        # Busca propostas desses clientes
        vendas = list(proposta_col.find({'Pessoa': {'$in': list(clientes_do_vendedor)}}))
        
        # Cria mapa de Pedido -> Valor Tabela (da saida)
        valor_tabela_map = {}
        for doc in saida_col.find({'Vendedor': nome_vendedor}):
            pedido = doc.get('Pedido', '')
            valor_tabela = RelatorioService._converter_valor(doc.get('Valor Tabela', 0))
            if pedido and valor_tabela > 0:
                # Converte para string para correspondência consistente
                valor_tabela_map[str(pedido)] = valor_tabela
        
        # Agrupa propostas por Pedido + Doc Fiscal (pois pode haver mesmo pedido com notas diferentes)
        propostas_por_pedido = {}
        for venda in vendas:
            pedido = venda.get('Nº Pedido', '') or venda.get('N° Pedido', '') or venda.get('Pedido', '')
            doc_fiscal = venda.get('Doc Fiscal', '').strip()
            if not pedido:
                continue
            
            # Converte pedido para string para uso consistente como chave
            pedido = str(pedido)
            
            # Cria chave única com pedido + doc_fiscal para evitar misturar vendas diferentes
            chave_pedido = f"{pedido}|{doc_fiscal}" if doc_fiscal else pedido
            
            valor = RelatorioService._converter_valor(venda.get('Valor Total', 0))
            
            # NÃO filtra valores negativos aqui - será feito após agrupar por pedido
            if chave_pedido not in propostas_por_pedido:
                propostas_por_pedido[chave_pedido] = {
                    'valor_total': 0,
                    'propostas': [],
                    'pedido': pedido  # Guarda o pedido para referência
                }
            
            propostas_por_pedido[chave_pedido]['valor_total'] += valor
            propostas_por_pedido[chave_pedido]['propostas'].append(venda)
        
        # FILTRO: Ignora pedidos cuja soma total é negativa
        propostas_por_pedido_filtrado = {}
        for chave_pedido, dados in propostas_por_pedido.items():
            valor_total = dados['valor_total']
            
            if valor_total < 0:
                continue
            
            propostas_por_pedido_filtrado[chave_pedido] = dados
        
        # Processa as vendas e calcula comissões com Meta % correta
        vendas_processadas = []
        avisos_globais = set()  # Set para evitar avisos duplicados
        
        for chave_pedido, dados in propostas_por_pedido_filtrado.items():
            pedido = dados.get('pedido', chave_pedido.split('|')[0])
            valor_tabela = valor_tabela_map.get(pedido, 0)
            valor_total_pedido = dados['valor_total']
            
            # Se não encontrou valor_tabela pelo pedido, tenta buscar pela moto
            if valor_tabela == 0 and dados['propostas']:
                modelo = dados['propostas'][0].get('Modelo', '').upper().strip()
                
                if modelo:
                    # Tenta buscar de várias formas pelo campo 'nome'
                    moto = mongo.db.motos.find_one({'nome': {'$regex': f'^{modelo}$', '$options': 'i'}})
                    
                    if not moto:
                        # Tenta busca parcial
                        moto = mongo.db.motos.find_one({'nome': {'$regex': modelo, '$options': 'i'}})
                    
                    if moto:
                        valor_tabela = RelatorioService._converter_valor(moto.get('valor_tabela', 0))
            
            # NOVO: Soma todos os valores presentes das formas de pagamento (PRIMEIRO)
            valor_venda_total_pedido = 0
            detalhes_formas = []  # Lista para rastrear cada forma e seu valor VP
            
            for venda in dados['propostas']:
                venda['_id'] = str(venda.get('_id', ''))
                modelo = venda.get('Modelo', '').upper()
                valor = RelatorioService._converter_valor(venda.get('Valor Total', 0))
                numero_parcelas = int(venda.get('Nº Parcela', 1)) if venda.get('Nº Parcela') else 1
                forma_recebimento = venda.get('Forma Recebimento', '').strip()
                
                # Calcular valor presente para cada forma de pagamento
                valor_venda_forma = valor
                aplicou_taxa = False
                
                # Busca a forma de recebimento no banco para aplicar taxa de juros
                if forma_recebimento and numero_parcelas >= 2:
                    forma_doc = mongo.db.formas_recebimento.find_one({
                        'nome': forma_recebimento,
                        'status': 'ativo'
                    })
                    
                    if forma_doc and forma_doc.get('aplicar_vp') and forma_doc.get('taxa_juros', 0) > 0:
                        taxa_juros = forma_doc.get('taxa_juros', 0) / 100  # Converte de % para decimal
                        # Aplica HP12C inversa para trazer ao valor presente
                        valor_venda_forma = ValorPresenteService.calcular_valor_com_juro_simples(
                            valor,
                            numero_parcelas,
                            taxa_juros
                        )
                        aplicou_taxa = True
                
                # Acumula o valor presente desta forma
                valor_venda_total_pedido += valor_venda_forma
                
                # Rastreia detalhes de cada forma
                detalhes_formas.append({
                    'venda': venda,
                    'valor_original': valor,
                    'valor_venda_forma': valor_venda_forma,
                    'aplicou_taxa': aplicou_taxa
                })
            
            # Calcula Meta % usando o valor VP TOTAL (não o valor original)
            if valor_tabela > 0:
                percentual_meta = (valor_venda_total_pedido / valor_tabela * 100)
            else:
                # Se ainda não encontrou tabela, usa 100% (sem comparação)
                percentual_meta = 100.0
            
            # Calcula comissão apenas se houver valor VP válido
            if valor_venda_total_pedido > 0:
                # Calcula comissão uma única vez sobre o total de todas as formas
                eh_ac = 'AC' in dados['propostas'][0].get('Modelo', '').upper()
                aliquota, avisos = ComissaoService._obter_aliquota_banco(mongo.db, percentual_meta, eh_ac, eh_interno)
                comissao_total = round(valor_venda_total_pedido * aliquota, 2)
                
                # Coleta avisos
                for aviso in avisos:
                    avisos_globais.add(aviso)
                
                # Distribui a comissão entre as formas de pagamento (proporcional ao valor VP)
                for detalhe in detalhes_formas:
                    venda = detalhe['venda']
                    proporcao = detalhe['valor_venda_forma'] / valor_venda_total_pedido
                    comissao_proporcional = round(comissao_total * proporcao, 2)
                    
                    venda['comissao'] = comissao_proporcional
                    venda['aliquota'] = aliquota * 100
                    venda['percentual_meta'] = percentual_meta
                    venda['valor_venda'] = detalhe['valor_venda_forma']
                    venda['valor_tabela'] = valor_tabela
                    venda['pedido'] = pedido
                    vendas_processadas.append(venda)
            else:
                # Sem valor de venda, apenas adiciona com comissão zero (transações de ajuste)
                eh_ac = 'AC' in dados['propostas'][0].get('Modelo', '').upper()
                aliquota, _ = ComissaoService._obter_aliquota_banco(mongo.db, percentual_meta, eh_ac, eh_interno)
                
                for detalhe in detalhes_formas:
                    venda = detalhe['venda']
                    venda['comissao'] = 0
                    venda['aliquota'] = aliquota * 100
                    venda['percentual_meta'] = percentual_meta
                    venda['valor_venda'] = detalhe['valor_venda_forma']
                    venda['valor_tabela'] = valor_tabela
                    venda['pedido'] = pedido
                    vendas_processadas.append(venda)
        
        resposta = {
            'status': 'sucesso',
            'dados': vendas_processadas,
            'eh_interno': eh_interno
        }
        
        # Adicionar avisos se houver
        if avisos_globais:
            resposta['avisos'] = list(avisos_globais)
        
        return jsonify(resposta)
        
    except Exception as e:
        logger.error(f"Erro ao buscar vendas do vendedor: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/resumo/cidade', methods=['GET'])
def resumo_cidade():
    """Resumo de comissões por cidade"""
    
    try:
        resumo = RelatorioService.resumo_por_cidade()
        return jsonify({'status': 'sucesso', 'dados': resumo})
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo por cidade: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/calcular-comissao', methods=['POST'])
def calcular_comissao():
    """Calcula comissão para uma proposta"""
    
    try:
        dados = request.json
        
        resultado = ComissaoService.calcular_comissao(
            dados.get('proposta'),
            dados.get('valor_meta'),
            dados.get('alta_cilindrada', False)
        )
        
        return jsonify({'status': 'sucesso', 'dados': resultado})
        
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400


# ========== ROTAS DE UPLOAD ==========

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route('/saida', methods=['POST'])
def upload_saida():
    """Upload de arquivo saida.csv"""
    
    try:
        if 'arquivo' not in request.files:
            logger.warning("Nenhum arquivo no request")
            return jsonify({'status': 'erro', 'mensagem': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['arquivo']
        logger.info(f"Arquivo recebido: {file.filename}")
        
        if file.filename == '':
            logger.warning("Arquivo vazio")
            return jsonify({'status': 'erro', 'mensagem': 'Arquivo vazio'}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"Arquivo não permitido: {file.filename}")
            return jsonify({'status': 'erro', 'mensagem': 'Tipo de arquivo não permitido'}), 400
        
        filename = secure_filename(file.filename)
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        logger.info(f"Arquivo salvo em: {filepath}")
        
        # Processa arquivo
        resultado = CSVProcessadorService.processar_saida(filepath)
        dados = resultado['dados']
        vendedores_info = resultado['vendedores']
        motos_info = resultado['motos']
        
        # Limpa dados antigos antes de inserir novos uploads
        mongo.db.saida.delete_many({})
        mongo.db.comissoes.delete_many({})
        
        # Salva no MongoDB
        if dados:
            mongo.db.saida.insert_many(dados)
        
        # Monta mensagem de feedback
        mensagens = []
        if vendedores_info['novo_count'] > 0:
            mensagens.append(f"{vendedores_info['novo_count']} vendedor(es) novo(s) cadastrado(s)")
        if vendedores_info['duplicado_count'] > 0:
            mensagens.append(f"{vendedores_info['duplicado_count']} vendedor(es) já existente(s)")
        if motos_info['novo_count'] > 0:
            mensagens.append(f"{motos_info['novo_count']} moto(s) nova(s) cadastrada(s)")
        if motos_info['duplicado_count'] > 0:
            mensagens.append(f"{motos_info['duplicado_count']} moto(s) já existente(s)")
        
        mensagem_completa = f"{len(dados)} linhas processadas. " + " | ".join(mensagens) if mensagens else f"{len(dados)} linhas processadas"
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': mensagem_completa,
            'quantidade': len(dados),
            'vendedores': vendedores_info,
            'motos': motos_info
        })
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload saida.csv: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@upload_bp.route('/proposta', methods=['POST'])
def upload_proposta():
    """Upload de arquivo proposta.csv"""
    
    try:
        if 'arquivo' not in request.files:
            logger.warning("Nenhum arquivo no request")
            return jsonify({'status': 'erro', 'mensagem': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['arquivo']
        logger.info(f"Arquivo recebido: {file.filename}")
        
        if file.filename == '':
            logger.warning("Arquivo vazio")
            return jsonify({'status': 'erro', 'mensagem': 'Arquivo vazio'}), 400
        
        if not allowed_file(file.filename):
            logger.warning(f"Arquivo não permitido: {file.filename}")
            return jsonify({'status': 'erro', 'mensagem': 'Tipo de arquivo não permitido'}), 400
        
        filename = secure_filename(file.filename)
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        logger.info(f"Arquivo salvo em: {filepath}")
        
        # Processa arquivo
        resultado = CSVProcessadorService.processar_proposta(filepath)
        dados = resultado['dados']
        motos_info = resultado['motos']
        formas_info = resultado.get('formas', {'novo_count': 0, 'duplicado_count': 0, 'novos': [], 'duplicados': []})
        
        # Limpa dados antigos antes de inserir novos uploads
        mongo.db.propostas.delete_many({})
        mongo.db.comissoes.delete_many({})
        
        # Salva no MongoDB
        if dados:
            mongo.db.propostas.insert_many(dados)
        
        # Monta mensagem de feedback
        mensagens = []
        if motos_info['novo_count'] > 0:
            mensagens.append(f"{motos_info['novo_count']} moto(s) nova(s) cadastrada(s)")
        if motos_info['duplicado_count'] > 0:
            mensagens.append(f"{motos_info['duplicado_count']} moto(s) já existente(s)")
        if formas_info['novo_count'] > 0:
            mensagens.append(f"{formas_info['novo_count']} forma(s) de recebimento nova(s)")
        if formas_info['duplicado_count'] > 0:
            mensagens.append(f"{formas_info['duplicado_count']} forma(s) de recebimento existente(s)")
        
        mensagem_completa = f"{len(dados)} linhas processadas. " + " | ".join(mensagens) if mensagens else f"{len(dados)} linhas processadas"
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': mensagem_completa,
            'quantidade': len(dados),
            'motos': motos_info,
            'formas': formas_info
        })
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload proposta.csv: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


# ========== ROTAS DE PÁGINA ==========

@main_bp.route('/parametros')
def parametros_page():
    """Página de gerenciamento de parâmetros de alíquota"""
    return render_template('parametros.html')


@main_bp.route('/formas-recebimento')
def formas_recebimento_page():
    """Página de gerenciamento de formas de recebimento"""
    return render_template('formas_recebimento.html')


# ========== ENDPOINTS DE FORMAS DE RECEBIMENTO ==========

@api_bp.route('/formas-recebimento', methods=['GET'])
def listar_formas_recebimento():
    """Lista todas as formas de recebimento"""
    try:
        formas = FormaRecebimentoService.listar_formas(status=None)
        return jsonify({'status': 'sucesso', 'dados': formas})
    except Exception as e:
        logger.error(f"Erro ao listar formas de recebimento: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/formas-recebimento/<forma_id>', methods=['DELETE'])
def deletar_forma_recebimento(forma_id):
    """Deleta uma forma de recebimento"""
    try:
        resultado = FormaRecebimentoService.deletar_forma(forma_id)
        if resultado.get('sucesso'):
            return jsonify({'status': 'sucesso', 'mensagem': 'Forma de recebimento deletada'})
        else:
            return jsonify({'status': 'erro', 'mensagem': 'Forma não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao deletar forma de recebimento: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/formas-recebimento/<forma_id>/desativar', methods=['PUT'])
def desativar_forma_recebimento(forma_id):
    """Desativa uma forma de recebimento"""
    try:
        resultado = FormaRecebimentoService.desativar_forma(forma_id)
        if resultado.get('sucesso'):
            return jsonify({'status': 'sucesso', 'mensagem': 'Forma de recebimento desativada'})
        else:
            return jsonify({'status': 'erro', 'mensagem': 'Forma não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao desativar forma de recebimento: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/formas-recebimento/<forma_id>/aplicar-vp', methods=['PUT'])
def atualizar_aplicar_vp(forma_id):
    """Atualiza se a forma de recebimento aplica Valor Presente (VP)"""
    try:
        dados = request.get_json() or {}
        aplicar_vp = dados.get('aplicar_vp', False)
        taxa_juros = dados.get('taxa_juros', 0.0)
        tabela_progressiva_id = dados.get('tabela_progressiva_id', '')
        
        resultado = FormaRecebimentoService.atualizar_aplicar_vp(forma_id, aplicar_vp, taxa_juros, tabela_progressiva_id)
        if resultado.get('sucesso'):
            return jsonify({'status': 'sucesso', 'mensagem': 'Configuração atualizada', 'dados': resultado.get('forma')})
        else:
            return jsonify({'status': 'erro', 'mensagem': 'Forma não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao atualizar aplicar_vp: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


# ========== ENDPOINTS DE PARÂMETROS DE ALÍQUOTA ==========

@api_bp.route('/parametros/interno', methods=['GET'])
def listar_parametros_interno():
    """Lista parâmetros de alíquota para vendedores internos"""
    try:
        parametros = list(mongo.db.parametros_aliquota.find({'eh_interno': True}).sort('meta_min', 1))
        
        # Converter ObjectId para string
        for param in parametros:
            param['_id'] = str(param.get('_id', ''))
        
        return jsonify({'status': 'sucesso', 'dados': parametros})
    except Exception as e:
        logger.error(f"Erro ao listar parâmetros internos: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/externo', methods=['GET'])
def listar_parametros_externo():
    """Lista parâmetros de alíquota para vendedores externos"""
    try:
        parametros = list(mongo.db.parametros_aliquota.find({'eh_interno': False}).sort('meta_min', 1))
        
        # Converter ObjectId para string
        for param in parametros:
            param['_id'] = str(param.get('_id', ''))
        
        return jsonify({'status': 'sucesso', 'dados': parametros})
    except Exception as e:
        logger.error(f"Erro ao listar parâmetros externos: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/interno', methods=['POST'])
def criar_parametro_interno():
    """Cria um novo parâmetro de alíquota para vendedor interno"""
    try:
        dados = request.json
        
        # Validações
        if 'tipo_moto' not in dados or 'meta_min' not in dados or 'aliquota' not in dados:
            return jsonify({'status': 'erro', 'mensagem': 'Campos obrigatórios faltando'}), 400
        
        novo_parametro = {
            'eh_interno': True,
            'tipo_moto': dados.get('tipo_moto'),
            'meta_min': float(dados.get('meta_min')),
            'meta_max': float(dados.get('meta_max')) if dados.get('meta_max') else None,
            'aliquota': float(dados.get('aliquota')),
            'criado_em': datetime.now()
        }
        
        resultado = mongo.db.parametros_aliquota.insert_one(novo_parametro)
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': 'Parâmetro criado com sucesso',
            'id': str(resultado.inserted_id)
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar parâmetro interno: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/externo', methods=['POST'])
def criar_parametro_externo():
    """Cria um novo parâmetro de alíquota para vendedor externo"""
    try:
        dados = request.json
        
        # Validações
        if 'meta_min' not in dados or 'aliquota' not in dados:
            return jsonify({'status': 'erro', 'mensagem': 'Campos obrigatórios faltando'}), 400
        
        novo_parametro = {
            'eh_interno': False,
            'meta_min': float(dados.get('meta_min')),
            'meta_max': float(dados.get('meta_max')) if dados.get('meta_max') else None,
            'aliquota': float(dados.get('aliquota')),
            'criado_em': datetime.now()
        }
        
        resultado = mongo.db.parametros_aliquota.insert_one(novo_parametro)
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': 'Parâmetro criado com sucesso',
            'id': str(resultado.inserted_id)
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar parâmetro externo: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/interno/<param_id>', methods=['DELETE'])
def deletar_parametro_interno(param_id):
    """Deleta um parâmetro de alíquota interno"""
    try:
        from bson import ObjectId
        resultado = mongo.db.parametros_aliquota.delete_one({
            '_id': ObjectId(param_id),
            'eh_interno': True
        })
        
        if resultado.deleted_count == 0:
            return jsonify({'status': 'erro', 'mensagem': 'Parâmetro não encontrado'}), 404
        
        return jsonify({'status': 'sucesso', 'mensagem': 'Parâmetro deletado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao deletar parâmetro interno: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/externo/<param_id>', methods=['DELETE'])
def deletar_parametro_externo(param_id):
    """Deleta um parâmetro de alíquota externo"""
    try:
        from bson import ObjectId
        resultado = mongo.db.parametros_aliquota.delete_one({
            '_id': ObjectId(param_id),
            'eh_interno': False
        })
        
        if resultado.deleted_count == 0:
            return jsonify({'status': 'erro', 'mensagem': 'Parâmetro não encontrado'}), 404
        
        return jsonify({'status': 'sucesso', 'mensagem': 'Parâmetro deletado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao deletar parâmetro externo: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/interno/<param_id>', methods=['PUT'])
def atualizar_parametro_interno(param_id):
    """Atualiza um parâmetro de alíquota interno"""
    try:
        from bson import ObjectId
        dados = request.json
        
        atualizacao = {
            'meta_min': float(dados.get('meta_min')),
            'meta_max': float(dados.get('meta_max')) if dados.get('meta_max') else None,
            'aliquota': float(dados.get('aliquota'))
        }
        
        resultado = mongo.db.parametros_aliquota.update_one(
            {'_id': ObjectId(param_id), 'eh_interno': True},
            {'$set': atualizacao}
        )
        
        if resultado.matched_count == 0:
            return jsonify({'status': 'erro', 'mensagem': 'Parâmetro não encontrado'}), 404
        
        return jsonify({'status': 'sucesso', 'mensagem': 'Parâmetro atualizado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao atualizar parâmetro interno: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@api_bp.route('/parametros/externo/<param_id>', methods=['PUT'])
def atualizar_parametro_externo(param_id):
    """Atualiza um parâmetro de alíquota externo"""
    try:
        from bson import ObjectId
        dados = request.json
        
        atualizacao = {
            'meta_min': float(dados.get('meta_min')),
            'meta_max': float(dados.get('meta_max')) if dados.get('meta_max') else None,
            'aliquota': float(dados.get('aliquota'))
        }
        
        resultado = mongo.db.parametros_aliquota.update_one(
            {'_id': ObjectId(param_id), 'eh_interno': False},
            {'$set': atualizacao}
        )
        
        if resultado.matched_count == 0:
            return jsonify({'status': 'erro', 'mensagem': 'Parâmetro não encontrado'}), 404
        
        return jsonify({'status': 'sucesso', 'mensagem': 'Parâmetro atualizado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao deletar parâmetro externo: {str(e)}", exc_info=True)
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500
