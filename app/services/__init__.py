# -*- coding: utf-8 -*-
"""
Serviços de negócio
"""

import pandas as pd
from decimal import Decimal
from datetime import datetime
from app import mongo
from app.models import ComissaoModel, PropostaModel, VendedorModel, MotoModel, FormaRecebimentoModel

class ValorPresenteService:
    """Serviço para cálculo de Valor Presente (VP) de parcelas
    
    Converte valor futuro (parcelado) para valor presente usando taxa de juros.
    Utilizado para calcular desconto em vendas no cartão, cheque, consórcio, etc.
    
    Fórmula: VP = Σ(P / (1+i)^x) onde:
    - P = valor da parcela
    - i = taxa de juros (ex: 0.02 para 2%)
    - x = número da parcela (1 a n)
    """
    
    @staticmethod
    def calcular_valor_presente(valor_parcela, numero_parcelas, taxa_juros):
        """Calcula o Valor Presente de uma série de parcelas
        
        Args:
            valor_parcela (float): Valor de cada parcela
            numero_parcelas (int): Número total de parcelas
            taxa_juros (float): Taxa de juros por período (ex: 0.02 para 2%)
            
        Returns:
            float: Valor Presente total (valor presente de todas as parcelas)
            
        Exemplo:
            >>> ValorPresenteService.calcular_valor_presente(100, 12, 0.02)
            1054.88  # VP de 12 parcelas de R$100 a 2% ao mês
        """
        try:
            if not valor_parcela or numero_parcelas <= 0 or taxa_juros < 0:
                return 0.0
            
            vp_total = 0.0
            
            # Calcula VP para cada parcela
            for x in range(1, numero_parcelas + 1):
                # VP_parcela = valor_parcela / (1 + taxa)^x
                vp_parcela = valor_parcela / ((1 + taxa_juros) ** x)
                vp_total += vp_parcela
            
            return round(vp_total, 2)
            
        except Exception as e:
            import logging
            logging.error(f"Erro ao calcular valor presente: {str(e)}", exc_info=True)
            return 0.0
    
    @staticmethod
    def calcular_valor_presente_com_coeficientes(valor_parcela, numero_parcelas, coeficientes):
        """Calcula VP usando coeficientes progressivos por parcela
        
        Utilizado quando há tabela de taxas progressivas cadastrada para a forma/parcelas.
        Cada parcela pode ter um desconto diferente.
        
        Args:
            valor_parcela (float): Valor de cada parcela
            numero_parcelas (int): Número total de parcelas
            coeficientes (list): Lista de coeficientes (%) para cada parcela
                Ex: [0, 0.5151, 0.3468, ..., 0.1113]
                
        Returns:
            float: Valor Presente total
            
        Exemplo:
            >>> coefs = [0, 0.5151, 0.3468, 0.2626, 0.2122, 0.1785, 0.1545, 0.1385, 0.1225, 0.1113]
            >>> ValorPresenteService.calcular_valor_presente_com_coeficientes(2000, 10, coefs)
            19847.35  # VP com descontos progressivos
        """
        try:
            if not valor_parcela or numero_parcelas <= 0 or not coeficientes:
                return 0.0
            
            # Valida que temos coeficientes para todas as parcelas
            if len(coeficientes) != numero_parcelas:
                return 0.0
            
            vp_total = 0.0
            
            # Calcula VP para cada parcela com seu coeficiente
            for i, coef in enumerate(coeficientes, 1):
                # Converte coeficiente de percentual para decimal (0.5151% = 0.005151)
                desconto_decimal = coef / 100
                # Aplica desconto: valor_parcela * (1 - desconto)
                vp_parcela = valor_parcela * (1 - desconto_decimal)
                vp_total += vp_parcela
            
            return round(vp_total, 2)
            
        except Exception as e:
            import logging
            logging.error(f"Erro ao calcular VP com coeficientes: {str(e)}", exc_info=True)
            return 0.0
    
    @staticmethod
    def calcular_desconto_percentual(valor_tabela, valor_parcela, numero_parcelas, taxa_juros):
        """Calcula o percentual de desconto aplicado pelas parcelas
        
        Args:
            valor_tabela (float): Valor de tabela (à vista)
            valor_parcela (float): Valor de cada parcela
            numero_parcelas (int): Número de parcelas
            taxa_juros (float): Taxa de juros
            
        Returns:
            dict: {
                'valor_presente': float,
                'desconto_absoluto': float,
                'desconto_percentual': float,
                'desconto_percentual_formatado': str
            }
            
        Exemplo:
            >>> resultado = ValorPresenteService.calcular_desconto_percentual(10000, 500, 24, 0.015)
            >>> resultado['desconto_percentual']
            8.5  # 8.5% de desconto
        """
        try:
            if not valor_tabela or valor_tabela <= 0:
                return {
                    'valor_presente': 0.0,
                    'desconto_absoluto': 0.0,
                    'desconto_percentual': 0.0,
                    'desconto_percentual_formatado': '0.00%'
                }
            
            # Calcula valor presente
            vp_total = ValorPresenteService.calcular_valor_presente(valor_parcela, numero_parcelas, taxa_juros)
            
            # Calcula diferença (desconto)
            desconto_absoluto = valor_tabela - vp_total
            
            # Calcula percentual de desconto
            if valor_tabela > 0:
                desconto_percentual = (desconto_absoluto / valor_tabela) * 100
            else:
                desconto_percentual = 0.0
            
            return {
                'valor_presente': round(vp_total, 2),
                'desconto_absoluto': round(desconto_absoluto, 2),
                'desconto_percentual': round(desconto_percentual, 2),
                'desconto_percentual_formatado': f'{desconto_percentual:.2f}%'
            }
            
        except Exception as e:
            import logging
            logging.error(f"Erro ao calcular desconto percentual: {str(e)}", exc_info=True)
            return {
                'valor_presente': 0.0,
                'desconto_absoluto': 0.0,
                'desconto_percentual': 0.0,
                'desconto_percentual_formatado': '0.00%'
            }
    
    @staticmethod
    def detectar_taxa_padrao(forma_recebimento):
        """Retorna a taxa padrão de juros baseada na forma de recebimento.
        
        Lê do banco de dados os campos 'aplicar_vp' e 'taxa_juros' da forma.
        Se não encontrar, usa valores padrão hardcoded.
        
        Args:
            forma_recebimento (str): Forma de recebimento (CARTÃO, CHEQUE, etc.)
            
        Returns:
            dict: {'aplicar_vp': bool, 'taxa_juros': float}
        """
        try:
            # Tenta buscar do banco de dados
            col = mongo.db.formas_recebimento
            forma_doc = col.find_one({
                'nome': forma_recebimento.strip(),
                'status': 'ativo'
            })
            
            if forma_doc:
                return {
                    'aplicar_vp': forma_doc.get('aplicar_vp', False),
                    'taxa_juros': forma_doc.get('taxa_juros', 0.0)
                }
        except Exception as e:
            import logging
            logging.debug(f"Erro ao buscar taxa do banco de dados: {str(e)}")
        
        # FALLBACK: Valores padrão hardcoded (para compatibilidade)
        forma_upper = str(forma_recebimento).upper().strip()
        
        if 'CARTÃO' in forma_upper:
            return {'aplicar_vp': True, 'taxa_juros': 0.015}  # 1.5% ao mês
        elif 'CHEQUE' in forma_upper:
            return {'aplicar_vp': True, 'taxa_juros': 0.020}  # 2.0% ao mês
        else:
            return {'aplicar_vp': False, 'taxa_juros': 0.0}  # À vista
    
    @staticmethod
    def calcular_valor_com_juro_simples(valor_total, numero_parcelas, taxa_juros):
        """Calcula valor presente usando fórmula de PV (HP12C inversa).
        
        Lógica (HP12C com PMT como entrada):
        1. Calcula PMT (parcela): PMT = valor_total / numero_parcelas
        2. Aplica fórmula HP12C inversa: PV = PMT * [((1+i)^n - 1) / (i * (1+i)^n)]
        3. Retorna o valor presente para cálculo de comissão
        
        Args:
            valor_total (float): Valor original/parcela total (ex: 8000)
            numero_parcelas (int): Número de parcelas (n) - ex: 10
            taxa_juros (float): Taxa de juros por período (i) - ex: 0.0159 para 1.59%
            
        Returns:
            float: Valor presente (PV) para cálculo de comissão
            
        Exemplo:
            >>> # 8.000,00 em 10x CARTÃO a 1,59% mês
            >>> ValorPresenteService.calcular_valor_com_juro_simples(8000, 10, 0.0159)
            7408.99  # Valor presente trazido ao presente
            
        Cálculo HP12C:
            f CLEAR FIN
            g END
            10       n
            1.59     i
            800.00   PMT (= 8000 / 10)
            0        FV
            PV       = 7408.99
            
        Fórmula:
            PV = PMT * [((1+i)^n - 1) / (i * (1+i)^n)]
        """
        try:
            if not valor_total or numero_parcelas <= 0 or taxa_juros < 0:
                return valor_total
            
            # Se só 1 parcela, não aplica juro
            if numero_parcelas == 1:
                return valor_total
            
            # PASSO 1: Calcula PMT (parcela)
            pmt = valor_total / numero_parcelas
            
            # PASSO 2: Aplica fórmula HP12C inversa: PV = PMT * [((1+i)^n - 1) / (i * (1+i)^n)]
            taxa_mais_1 = 1 + taxa_juros
            potencia_n = taxa_mais_1 ** numero_parcelas
            
            numerador = potencia_n - 1
            denominador = taxa_juros * potencia_n
            
            if denominador == 0:
                return valor_total
            
            # Calcula PV (valor presente)
            pv = pmt * (numerador / denominador)
            
            return round(pv, 2)
            
        except Exception as e:
            import logging
            logging.error(f"Erro ao calcular valor com juro simples: {str(e)}", exc_info=True)
            return valor_total

class VendedorService:
    """Serviço para gerenciar vendedores"""
    
    @staticmethod
    def criar_vendedor(dados):
        """Cria um novo vendedor"""
        try:
            # Verifica se já existe
            col = mongo.db.vendedores
            existente = col.find_one({'nome': dados.get('nome')})
            
            if existente:
                return {'erro': 'Vendedor já existe'}
            
            vendedor = VendedorModel.create(dados)
            col.insert_one(vendedor)
            
            return {'sucesso': True, 'id': str(vendedor['_id'])}
        except Exception as e:
            import logging
            logging.error(f"Erro ao criar vendedor: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def listar_vendedores(status='ativo'):
        """Lista vendedores ativos"""
        try:
            col = mongo.db.vendedores
            query = {'status': status} if status else {}
            vendedores = list(col.find(query).sort('nome', 1))
            
            # Converte ObjectId para string
            for v in vendedores:
                v['_id'] = str(v['_id'])
            
            return vendedores
        except Exception as e:
            import logging
            logging.error(f"Erro ao listar vendedores: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def obter_vendedor(vendor_id):
        """Obtém um vendedor por ID"""
        try:
            from bson import ObjectId
            col = mongo.db.vendedores
            vendedor = col.find_one({'_id': ObjectId(vendor_id)})
            
            if vendedor:
                vendedor['_id'] = str(vendedor['_id'])
            
            return vendedor
        except Exception as e:
            import logging
            logging.error(f"Erro ao obter vendedor: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def atualizar_vendedor(vendor_id, dados):
        """Atualiza um vendedor"""
        try:
            from bson import ObjectId
            col = mongo.db.vendedores
            
            dados['data_atualizacao'] = datetime.now()
            
            result = col.update_one(
                {'_id': ObjectId(vendor_id)},
                {'$set': dados}
            )
            
            return {'sucesso': result.modified_count > 0}
        except Exception as e:
            import logging
            logging.error(f"Erro ao atualizar vendedor: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def deletar_vendedor(vendor_id):
        """Deleta um vendedor (soft delete - marca como inativo)"""
        try:
            from bson import ObjectId
            col = mongo.db.vendedores
            
            result = col.update_one(
                {'_id': ObjectId(vendor_id)},
                {'$set': {'status': 'inativo', 'data_atualizacao': datetime.now()}}
            )
            
            return {'sucesso': result.modified_count > 0}
        except Exception as e:
            import logging
            logging.error(f"Erro ao deletar vendedor: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def garantir_vendedor(nome_vendedor, cidade=''):
        """Garante que o vendedor existe no banco. Se não existir, cria automaticamente.
        
        Args:
            nome_vendedor (str): Nome do vendedor
            cidade (str): Cidade do vendedor (opcional)
            
        Returns:
            dict: {'existe': True/False, 'criado': True/False, 'vendedor': {}}
        """
        try:
            if not nome_vendedor or nome_vendedor.lower() == 'desconhecido':
                return {'existe': False, 'criado': False, 'vendedor': None}
            
            col = mongo.db.vendedores
            nome_vendedor = nome_vendedor.strip()
            
            # Verifica se já existe
            existente = col.find_one({'nome': nome_vendedor})
            
            if existente:
                return {'existe': True, 'criado': False, 'vendedor': existente}
            
            # Não existe, cria automaticamente
            vendedor = VendedorModel.create({
                'nome': nome_vendedor,
                'cidade': cidade.strip() if cidade else '',
                'status': 'ativo'
            })
            col.insert_one(vendedor)
            
            return {'existe': False, 'criado': True, 'vendedor': vendedor}
        except Exception as e:
            import logging
            logging.error(f"Erro ao garantir vendedor {nome_vendedor}: {str(e)}", exc_info=True)
            return {'existe': False, 'criado': False, 'vendedor': None}
    
    @staticmethod
    def sincronizar_vendedores(vendedores_dados):
        """Sincroniza vendedores do upload (cria os que faltam, atualiza cidades)
        
        vendedores_dados: dict com {'nome': cidade} ou lista de nomes (retrocompatibilidade)
        
        Retorna: dict com status, novo_count, duplicado_count, atualizados, duplicados
        """
        try:
            col = mongo.db.vendedores
            novo_count = 0
            duplicado_count = 0
            novos = []
            duplicados = []
            
            # Se for lista, converte em dict (retrocompatibilidade)
            if isinstance(vendedores_dados, list):
                vendedores_dados = {nome: '' for nome in vendedores_dados}
            
            for nome, cidade in vendedores_dados.items():
                if not nome or nome == 'Desconhecido':
                    continue
                
                nome = nome.strip()
                cidade = cidade.strip() if cidade else ''
                
                # Verifica se já existe (CASE-INSENSITIVE para evitar duplicatas)
                existente = col.find_one({'nome': {'$regex': f'^{nome}$', '$options': 'i'}})
                
                if not existente:
                    # Cria novo vendedor
                    vendedor = VendedorModel.create({
                        'nome': nome,
                        'cidade': cidade,
                        'status': 'ativo'
                    })
                    col.insert_one(vendedor)
                    novo_count += 1
                    novos.append(nome)
                else:
                    # Vendedor já existe
                    duplicado_count += 1
                    duplicados.append(nome)
                    # Se temos cidade e é diferente, atualiza
                    if cidade and existente.get('cidade', '') != cidade:
                        col.update_one(
                            {'_id': existente['_id']},
                            {'$set': {'cidade': cidade, 'data_atualizacao': __import__('datetime').datetime.now()}}
                        )
            
            return {
                'sucesso': True,
                'novo_count': novo_count,
                'duplicado_count': duplicado_count,
                'novos': novos,
                'duplicados': duplicados
            }
        except Exception as e:
            import logging
            logging.error(f"Erro ao sincronizar vendedores: {str(e)}", exc_info=True)
            return {'erro': str(e)}

class MotoService:
    """Serviço para gerenciar motocicletas"""
    
    @staticmethod
    def criar_moto(dados):
        """Cria uma nova moto"""
        try:
            col = mongo.db.motos
            existente = col.find_one({'nome': dados.get('nome')})
            
            if existente:
                return {'erro': 'Moto já existe'}
            
            moto = MotoModel.create(dados)
            col.insert_one(moto)
            
            return {'sucesso': True, 'id': str(moto['_id'])}
        except Exception as e:
            import logging
            logging.error(f"Erro ao criar moto: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def listar_motos(status='ativo'):
        """Lista todas as motos"""
        try:
            col = mongo.db.motos
            motos = list(col.find({'status': status}))
            
            # Converte ObjectId para string
            for moto in motos:
                moto['_id'] = str(moto['_id'])
            
            return motos
        except Exception as e:
            import logging
            logging.error(f"Erro ao listar motos: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def obter_moto(moto_id):
        """Obtém uma moto por ID"""
        try:
            from bson import ObjectId
            col = mongo.db.motos
            moto = col.find_one({'_id': ObjectId(moto_id)})
            
            if moto:
                moto['_id'] = str(moto['_id'])
            
            return moto
        except Exception as e:
            import logging
            logging.error(f"Erro ao obter moto: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def atualizar_moto(moto_id, dados):
        """Atualiza uma moto"""
        try:
            from bson import ObjectId
            col = mongo.db.motos
            
            dados['data_atualizacao'] = datetime.now()
            resultado = col.update_one(
                {'_id': ObjectId(moto_id)},
                {'$set': dados}
            )
            
            if resultado.matched_count == 0:
                return {'erro': 'Moto não encontrada'}
            
            return {'sucesso': True}
        except Exception as e:
            import logging
            logging.error(f"Erro ao atualizar moto: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def deletar_moto(moto_id):
        """Deleta (inativa) uma moto"""
        try:
            from bson import ObjectId
            col = mongo.db.motos
            
            resultado = col.update_one(
                {'_id': ObjectId(moto_id)},
                {'$set': {'status': 'inativo', 'data_atualizacao': datetime.now()}}
            )
            
            if resultado.matched_count == 0:
                return {'erro': 'Moto não encontrada'}
            
            return {'sucesso': True}
        except Exception as e:
            import logging
            logging.error(f"Erro ao deletar moto: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def garantir_moto(nome_moto, alta_cc=False):
        """Garante que a moto existe no banco. Se não existir, cria automaticamente.
        
        Args:
            nome_moto (str): Nome da moto
            alta_cc (bool): Se é alta cilindrada
            
        Returns:
            dict: {'existe': True/False, 'criado': True/False, 'moto': {}}
        """
        try:
            if not nome_moto or nome_moto.lower() == 'desconhecida':
                return {'existe': False, 'criado': False, 'moto': None}
            
            col = mongo.db.motos
            nome_moto = nome_moto.strip()
            
            # Verifica se já existe
            existente = col.find_one({'nome': nome_moto})
            
            if existente:
                return {'existe': True, 'criado': False, 'moto': existente}
            
            # Não existe, cria automaticamente
            moto = MotoModel.create({
                'nome': nome_moto,
                'alta_cc': bool(alta_cc),
                'status': 'ativo'
            })
            col.insert_one(moto)
            
            return {'existe': False, 'criado': True, 'moto': moto}
        except Exception as e:
            import logging
            logging.error(f"Erro ao garantir moto {nome_moto}: {str(e)}", exc_info=True)
            return {'existe': False, 'criado': False, 'moto': None}
    
    @staticmethod
    def sincronizar_motos(motos_dados):
        """Sincroniza motos do upload (cria as que faltam, atualiza alta_cc e valor_tabela)
        
        motos_dados: dict com {'nome': {'alta_cc': bool, 'valor_tabela': float}} 
                    ou dict simples {'nome': bool} (retrocompatibilidade)
        
        Retorna: dict com status, novo_count, duplicado_count, novos, duplicados
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            col = mongo.db.motos
            novo_count = 0
            duplicado_count = 0
            novos = []
            duplicados = []
            
            # Se for lista, converte em dict (retrocompatibilidade)
            if isinstance(motos_dados, list):
                motos_dados = {nome: {'alta_cc': False, 'valor_tabela': 0.0} for nome in motos_dados}
            
            for nome, dados in motos_dados.items():
                if not nome or nome == 'Desconhecida':
                    continue
                
                nome = nome.strip()
                
                # Extrai dados (compatibilidade com formato antigo ou novo)
                if isinstance(dados, dict):
                    alta_cc = bool(dados.get('alta_cc', False))
                    valor_tabela = float(dados.get('valor_tabela', 0.0))
                else:
                    # Formato antigo: apenas um booleano
                    alta_cc = bool(dados)
                    valor_tabela = 0.0
                
                # Verifica se já existe
                existente = col.find_one({'nome': nome})
                
                if not existente:
                    # Procura com busca case-insensitive como fallback
                    existente = col.find_one({'nome': {'$regex': f'^{nome}$', '$options': 'i'}})
                    if not existente:
                        # Cria nova moto
                        moto = MotoModel.create({
                            'nome': nome,
                            'alta_cc': alta_cc,
                            'valor_tabela': valor_tabela,
                            'status': 'ativo'
                        })
                        col.insert_one(moto)
                        novo_count += 1
                        novos.append(nome)
                    else:
                        # Encontrou com regex - reativa se estava inativa e atualiza valor_tabela
                        update_data = {
                            'status': 'ativo',
                            'valor_tabela': valor_tabela, 
                            'data_atualizacao': __import__('datetime').datetime.now()
                        }
                        col.update_one({'_id': existente['_id']}, {'$set': update_data})
                        duplicado_count += 1
                        duplicados.append(nome)
                else:
                    # Encontrou com nome exato - reativa se inativa e atualiza apenas valor_tabela
                    # Não atualiza alta_cc pois deve ser persistente no frontend
                    update_data = {
                        'status': 'ativo',
                        'data_atualizacao': __import__('datetime').datetime.now()
                    }
                    
                    # Atualiza valor_tabela se mudou
                    if existente.get('valor_tabela', 0.0) != valor_tabela:
                        update_data['valor_tabela'] = valor_tabela
                    
                    col.update_one({'_id': existente['_id']}, {'$set': update_data})
                    
                    duplicado_count += 1
                    duplicados.append(nome)
            
            return {
                'sucesso': True,
                'novo_count': novo_count,
                'duplicado_count': duplicado_count,
                'novos': novos,
                'duplicados': duplicados
            }
        except Exception as e:
            import logging
            logging.error(f"Erro ao sincronizar motos: {str(e)}", exc_info=True)
            return {'erro': str(e)}

class ComissaoService:
    """Serviço de cálculo de comissão"""
    
    # Alíquotas por regra - VENDEDOR INTERNO
    ALIQ_AC_ACIMA_97_INT = 0.012   # 1.2%
    ALIQ_AC_ABAIXO_97_INT = 0.008  # 0.8%
    
    ALIQ_OM_ACIMA_100_INT = 0.020  # 2.0%
    ALIQ_OM_97_A_99999_INT = 0.016 # 1.6%
    ALIQ_OM_95_A_96999_INT = 0.012 # 1.2%
    ALIQ_OM_ATE_94999_INT = 0.010  # 1.0%
    
    # Alíquotas por regra - VENDEDOR EXTERNO (simplificado)
    ALIQ_ACIMA_97_EXT = 0.012   # 1.2%
    ALIQ_ABAIXO_97_EXT = 0.008  # 0.8%
    
    @staticmethod
    def registrar_comissao(dados_comissao):
        """Registra uma comissão na collection de comissões
        
        Args:
            dados_comissao (dict): Dados da comissão com:
                - vendedor: nome
                - cidade: cidade
                - modelo: modelo da moto
                - valor_venda: valor total
                - valor_comissao: valor calculado
                - aliquota: percentual aplicado
                - forma_recebimento: forma de pagamento
                - eh_interno: se é vendedor interno
                
        Returns:
            dict: {'sucesso': bool, 'id': str, 'comissao': {}}
        """
        try:
            from bson import ObjectId
            
            col = mongo.db.comissoes
            
            comissao = {
                '_id': ObjectId(),
                'vendedor': dados_comissao.get('vendedor', ''),
                'cidade': dados_comissao.get('cidade', ''),
                'modelo': dados_comissao.get('modelo', ''),
                'valor_venda': dados_comissao.get('valor_venda', 0),
                'valor_comissao': dados_comissao.get('valor_comissao', 0),
                'aliquota': dados_comissao.get('aliquota', 0),
                'forma_recebimento': dados_comissao.get('forma_recebimento', ''),
                'eh_interno': dados_comissao.get('eh_interno', False),
                'data_processamento': datetime.now()
            }
            
            col.insert_one(comissao)
            
            return {
                'sucesso': True,
                'id': str(comissao['_id']),
                'comissao': comissao
            }
        except Exception as e:
            import logging
            logging.error(f"Erro ao registrar comissão: {str(e)}", exc_info=True)
            return {'sucesso': False, 'erro': str(e)}
    
    @staticmethod
    def calcular_comissao(proposta, valor_meta, eh_alta_cilindrada, eh_vendedor_interno=True):
        """
        Calcula comissão baseada nas regras de negócio
        
        Args:
            proposta (dict): Dados da proposta
            valor_meta (float): Valor da meta
            eh_alta_cilindrada (bool): Se é modelo de alta cilindrada
            eh_vendedor_interno (bool): Se é vendedor interno ou externo
            
        Returns:
            dict: Resultado com valor e alíquota
        """
        
        if not proposta or not valor_meta or valor_meta <= 0:
            raise ValueError("Proposta ou meta inválida")
        
        # Calcula percentual de meta
        valor_venda = float(proposta.get('valor_venda', 0))
        percentual_meta = (valor_venda / valor_meta) * 100
        
        # Obtém alíquota do banco de dados (ou padrão se não encontrar)
        aliquota, avisos = ComissaoService._obter_aliquota_banco(mongo.db, percentual_meta, eh_alta_cilindrada, eh_vendedor_interno)
        
        # Calcula valor de comissão
        valor_comissao = round(valor_venda * aliquota, 2)
        
        return {
            'id_proposta': proposta.get('id'),
            'vendedor': proposta.get('vendedor'),
            'modelo': proposta.get('modelo'),
            'cidade': proposta.get('cidade'),
            'valor_venda': valor_venda,
            'valor_meta': valor_meta,
            'percentual_meta': round(percentual_meta, 2),
            'valor_comissao': valor_comissao,
            'aliquota': aliquota * 100,
            'alta_cilindrada': eh_alta_cilindrada,
            'vendedor_interno': eh_vendedor_interno
        }
    
    @staticmethod
    def _obter_aliquota(percentual_meta, eh_alta_cilindrada, eh_vendedor_interno=True):
        """Obtém alíquota conforme regras e tipo de vendedor"""
        
        if eh_vendedor_interno:
            # VENDEDOR INTERNO - com diferenciação Alta CC vs Baixa CC
            if eh_alta_cilindrada:
                # Alta CC - Motos de Alta Cilindrada
                if percentual_meta >= 97:
                    return ComissaoService.ALIQ_AC_ACIMA_97_INT  # 1.2%
                else:
                    return ComissaoService.ALIQ_AC_ABAIXO_97_INT  # 0.8%
            else:
                # Baixa CC - Outras Motos
                if percentual_meta >= 100:
                    return ComissaoService.ALIQ_OM_ACIMA_100_INT  # 2.0%
                elif percentual_meta >= 97:
                    return ComissaoService.ALIQ_OM_97_A_99999_INT  # 1.6%
                elif percentual_meta >= 95:
                    return ComissaoService.ALIQ_OM_95_A_96999_INT  # 1.2%
                else:
                    return ComissaoService.ALIQ_OM_ATE_94999_INT  # 1.0%
        else:
            # VENDEDOR EXTERNO - simples (sem diferenciação Alta CC vs Baixa CC)
            if percentual_meta >= 97:
                return ComissaoService.ALIQ_ACIMA_97_EXT  # 1.2%
            else:
                return ComissaoService.ALIQ_ABAIXO_97_EXT  # 0.8%

    @staticmethod
    def _obter_aliquota_banco(mongo_db, percentual_meta, eh_alta_cilindrada, eh_vendedor_interno=True, tipo_moto_nome=None):
        """
        Obtém alíquota do banco de dados MongoDB. Se não encontrar, usa valor padrão.
        
        Returns:
            tuple: (aliquota, avisos_list) - aliquota é decimal, avisos_list contém mensagens de aviso
        """
        avisos = []
        
        try:
            if eh_vendedor_interno:
                # Para interno, precisa saber o tipo de moto
                tipo_moto = "Alta CC" if eh_alta_cilindrada else "Baixa CC"
                
                param = mongo_db.parametros_aliquota.find_one({
                    'eh_interno': True,
                    'tipo_moto': tipo_moto,
                    'meta_min': {'$lte': percentual_meta}
                })
                
                if param:
                    # Se meta_max está definido, verificar se está no intervalo
                    if param.get('meta_max') is not None:
                        if percentual_meta <= param['meta_max']:
                            return param.get('aliquota'), avisos
                    else:
                        # Sem meta_max, retorna o primeiro que corresponde
                        return param.get('aliquota'), avisos
            else:
                # Para externo, não diferencia tipo de moto
                param = mongo_db.parametros_aliquota.find_one({
                    'eh_interno': False,
                    'meta_min': {'$lte': percentual_meta}
                })
                
                if param:
                    if param.get('meta_max') is not None:
                        if percentual_meta <= param['meta_max']:
                            return param.get('aliquota'), avisos
                    else:
                        return param.get('aliquota'), avisos
            
            # Se não encontrou no banco, usa valor padrão (hardcoded) e adiciona aviso
            tipo_vendedor = "Interno" if eh_vendedor_interno else "Externo"
            tipo_moto = "Alta CC" if eh_alta_cilindrada else "Baixa CC"
            
            # NÃO mostra aviso se Meta % > 100% (venda acima do valor de tabela)
            if percentual_meta <= 100:
                avisos.append(f"⚠️ AVISO: Nenhuma alíquota cadastrada para {tipo_vendedor} - {tipo_moto} (Meta {percentual_meta:.2f}%). Usando valor padrão.")
            
            aliquota_padrao = ComissaoService._obter_aliquota(percentual_meta, eh_alta_cilindrada, eh_vendedor_interno)
            return aliquota_padrao, avisos
            
        except Exception as e:
            # Em caso de erro, usa valor padrão e avisa
            avisos.append(f"⚠️ ERRO ao buscar alíquota: {str(e)}. Usando valor padrão.")
            aliquota_padrao = ComissaoService._obter_aliquota(percentual_meta, eh_alta_cilindrada, eh_vendedor_interno)
            return aliquota_padrao, avisos


class CSVProcessadorService:
    """Serviço para processar arquivos CSV"""
    
    @staticmethod
    def processar_saida(filepath):
        """Processa arquivo saida.csv"""
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Tenta detectar o delimitador
            with open(filepath, 'r', encoding='utf-8') as f:
                primeira_linha = f.readline()
                
                # Detecta delimitador
                delim = ',' if ',' in primeira_linha else ';'
            
            df = pd.read_csv(filepath, encoding='utf-8-sig', sep=delim)
            
            # Remove espaços dos nomes das colunas
            df.columns = df.columns.str.strip()
            
            # Validações básicas
            if df.empty:
                raise ValueError("Arquivo vazio")
            
            # Limpa dados
            df = df.fillna('')
            df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)
            
            resultado = df.to_dict('records')
            
            # Sincroniza vendedores do arquivo com suas cidades (Origem Venda)
            vendedores_sync = {'novo_count': 0, 'duplicado_count': 0, 'novos': [], 'duplicados': []}
            vendedores_map = {}
            for doc in resultado:
                nome = doc.get('Vendedor', '').strip()
                cidade = doc.get('Origem Venda', '').strip()
                if nome and nome != 'Desconhecido':
                    vendedores_map[nome] = cidade
            if vendedores_map:
                result = VendedorService.sincronizar_vendedores(vendedores_map)
                if 'sucesso' in result:
                    vendedores_sync = {
                        'novo_count': result.get('novo_count', 0),
                        'duplicado_count': result.get('duplicado_count', 0),
                        'novos': result.get('novos', []),
                        'duplicados': result.get('duplicados', [])
                    }
            
            # Sincroniza motos do arquivo
            motos_sync = {'novo_count': 0, 'duplicado_count': 0, 'novos': [], 'duplicados': []}
            motos_map = {}
            for doc in resultado:
                modelo = doc.get('Modelo', '').strip()
                if modelo and modelo != 'Desconhecida':
                    # Detecta se é AC (Alta Cilindrada) procurando por "AC" no modelo
                    eh_alta_cc = 'AC' in modelo.upper()
                    
                    # Extrai valor tabela e converte para float
                    valor_tabela_str = doc.get('Valor Tabela', '0')
                    if isinstance(valor_tabela_str, str):
                        valor_tabela_str = valor_tabela_str.strip()
                    else:
                        valor_tabela_str = str(valor_tabela_str).strip()
                    
                    # Remove espaços e converte vírgula para ponto
                    valor_tabela_str = valor_tabela_str.replace('.', '').replace(',', '.')
                    
                    try:
                        valor_tabela = float(valor_tabela_str)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"CSV - Erro ao converter '{doc.get('Valor Tabela')}' do modelo {modelo}: {e}")
                        valor_tabela = 0.0
                    
                    motos_map[modelo] = {
                        'alta_cc': eh_alta_cc,
                        'valor_tabela': valor_tabela
                    }
            
            if motos_map:
                result = MotoService.sincronizar_motos(motos_map)
                result = MotoService.sincronizar_motos(motos_map)
                if 'sucesso' in result:
                    motos_sync = {
                        'novo_count': result.get('novo_count', 0),
                        'duplicado_count': result.get('duplicado_count', 0),
                        'novos': result.get('novos', []),
                        'duplicados': result.get('duplicados', [])
                    }
            
            # Retorna os dados junto com info de sincronização
            return {
                'dados': resultado,
                'vendedores': vendedores_sync,
                'motos': motos_sync
            }
            
        except Exception as e:
            import logging
            logging.error(f"Erro ao processar saida.csv: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao processar arquivo: {str(e)}")
    
    @staticmethod
    def processar_proposta(filepath):
        """Processa arquivo proposta.csv"""
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Tenta detectar o delimitador
            with open(filepath, 'r', encoding='utf-8') as f:
                primeira_linha = f.readline()
                
                # Detecta delimitador
                delim = ',' if ',' in primeira_linha else ';'
            
            df = pd.read_csv(filepath, encoding='utf-8', sep=delim)
            
            # Limpa dados
            df = df.fillna('')
            df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)
            
            # Converte valores monetários
            for col in ['valor_venda', 'valor_proposta', 'proposal_value', 'sales_achieved']:
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
                    except:
                        pass
            
            resultado = df.to_dict('records')
            
            # Sincroniza formas de recebimento do arquivo
            formas_sync = {'novo_count': 0, 'duplicado_count': 0, 'novos': [], 'duplicados': []}
            formas_set = set()
            for doc in resultado:
                forma = doc.get('Forma Recebimento', '').strip()
                if forma and forma != 'Desconhecido':
                    formas_set.add(forma)
            if formas_set:
                result = FormaRecebimentoService.sincronizar_formas(formas_set)
                if 'sucesso' in result:
                    formas_sync = {
                        'novo_count': result.get('novo_count', 0),
                        'duplicado_count': result.get('duplicado_count', 0),
                        'novos': result.get('novos', []),
                        'duplicados': result.get('duplicados', [])
                    }
            
            return {
                'dados': resultado,
                'motos': {'novo_count': 0, 'duplicado_count': 0, 'novos': [], 'duplicados': []},
                'formas': formas_sync
            }
            
        except Exception as e:
            import logging
            logging.error(f"Erro ao processar proposta.csv: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao processar arquivo: {str(e)}")


class RelatorioService:
    """Serviço para gerar relatórios"""
    
    @staticmethod
    def _converter_valor(valor):
        """Converte valor em formato brasileiro (1.000,00) para float"""
        if not valor:
            return 0
        
        try:
            # Converte para string
            valor_str = str(valor).strip()
            
            # Se tem vírgula, é formato brasileiro
            if ',' in valor_str:
                # Remove pontos (separadores de milhares) e substitui vírgula por ponto
                valor_str = valor_str.replace('.', '').replace(',', '.')
            
            return float(valor_str)
        except:
            return 0
    
    @staticmethod
    def _forma_recebimento_valida(forma_nome):
        """Valida se a forma de recebimento está cadastrada no banco
        
        Returns:
            bool: True se forma existe e está ativa, False caso contrário
        """
        if not forma_nome:
            return False
        
        try:
            forma = mongo.db.formas_recebimento.find_one({
                'nome': forma_nome.strip(),
                'status': 'ativo'
            })
            return forma is not None
        except:
            return False
    
    @staticmethod
    def resumo_comissoes(filtros=None):
        """Gera resumo de comissões por vendedor com Meta % correta e forma de recebimento"""
        
        import logging
        try:
            # Busca as coleções
            saida_col = mongo.db.saida
            proposta_col = mongo.db.propostas
            vendedor_col = mongo.db.vendedores
            
            # Busca dados com os nomes corretos de colunas
            saida_docs = list(saida_col.find({}))
            proposta_docs = list(proposta_col.find({}))
            
            # Busca vendedores cadastrados
            vendedores_cadastrados = {v['nome']: v for v in vendedor_col.find({})}
            
            # Mapa de Pessoa -> Vendedor (extraído de saida)
            pessoa_vendedores = {}
            for doc in saida_docs:
                pessoa = doc.get('Pessoa', '').strip()
                vendedor = doc.get('Vendedor', '').strip()
                
                if pessoa and vendedor:
                    if pessoa not in pessoa_vendedores:
                        pessoa_vendedores[pessoa] = []
                    if vendedor not in pessoa_vendedores[pessoa]:
                        pessoa_vendedores[pessoa].append(vendedor)
            
            # Cria mapa de Pedido -> Valor Tabela (da saida) por vendedor
            valor_tabela_map = {}
            for doc in saida_docs:
                vendedor = doc.get('Vendedor', '').strip()
                pedido = doc.get('Pedido', '')
                doc_fiscal = doc.get('Doc Fiscal', '').strip()
                valor_tabela = RelatorioService._converter_valor(doc.get('Valor Tabela', 0))
                if pedido and valor_tabela > 0:
                    chave = f"{vendedor}|{pedido}|{doc_fiscal}" if doc_fiscal else f"{vendedor}|{pedido}"
                    valor_tabela_map[chave] = valor_tabela
            
                # Processa em dicionários para join
            vendedores = {}
            
            # Agrupa propostas por Vendedor, Pedido e Doc Fiscal para calcular Meta % corretamente
            propostas_por_vendedor_pedido = {}
            for doc in proposta_docs:
                pessoa = doc.get('Pessoa', '').strip()
                pedido = doc.get('Nº Pedido', '') or doc.get('N° Pedido', '') or doc.get('Pedido', '')
                doc_fiscal = doc.get('Doc Fiscal', '').strip()
                valor = RelatorioService._converter_valor(doc.get('Valor Total', 0))
                
                # NÃO filtra valores negativos aqui - será feito após agrupar por pedido
                if not pessoa or not pedido:
                    continue
                
                # Procura qual vendedor fez a venda para essa pessoa
                vendedores_dessa_pessoa = pessoa_vendedores.get(pessoa, [])
                if not vendedores_dessa_pessoa:
                    continue
                
                nome_vendedor = vendedores_dessa_pessoa[0]
                
                # Se vendedor não está cadastrado, ignora
                if nome_vendedor not in vendedores_cadastrados:
                    continue
                
                chave_vendedor_pedido = f"{nome_vendedor}|{pedido}|{doc_fiscal}" if doc_fiscal else f"{nome_vendedor}|{pedido}"
                
                if chave_vendedor_pedido not in propostas_por_vendedor_pedido:
                    propostas_por_vendedor_pedido[chave_vendedor_pedido] = {
                        'nome_vendedor': nome_vendedor,
                        'pedido': pedido,
                        'valor_total': 0,
                        'propostas': []
                    }
                
                propostas_por_vendedor_pedido[chave_vendedor_pedido]['valor_total'] += valor
                propostas_por_vendedor_pedido[chave_vendedor_pedido]['propostas'].append(doc)
            
            # FILTRO: Ignora pedidos cuja soma total é negativa
            propostas_por_vendedor_pedido_filtrado = {}
            for chave, dados_pedido in propostas_por_vendedor_pedido.items():
                valor_total = dados_pedido['valor_total']
                nome_vendedor = dados_pedido['nome_vendedor']
                pedido = dados_pedido.get('pedido', chave.split('|')[1])  # Usa pedido guardado ou extrai da chave
                
                if valor_total < 0:
                    continue
                
                propostas_por_vendedor_pedido_filtrado[chave] = dados_pedido
            
            # Calcula comissões respeitando Meta % e Forma de Recebimento
            for chave, dados_pedido in propostas_por_vendedor_pedido_filtrado.items():
                nome_vendedor = dados_pedido['nome_vendedor']
                valor_total_pedido = dados_pedido['valor_total']
                
                # Busca Valor Tabela para calcular Meta %
                valor_tabela = valor_tabela_map.get(chave, 0)
                
                # Inicializa vendedor se não existe
                if nome_vendedor not in vendedores:
                    vendedor_info = vendedores_cadastrados.get(nome_vendedor, {})
                    vendedores[nome_vendedor] = {
                        'vendor_name': nome_vendedor,
                        'total_vendas': 0,
                        'total_comissoes': 0,
                        'quantidade_propostas': 0,
                        'eh_interno': vendedor_info.get('interno', False)
                    }
                
                eh_interno = vendedores_cadastrados[nome_vendedor].get('interno', False)
                
                # NOVO: Soma todos os valores presentes das formas de pagamento (PRIMEIRO)
                valor_venda_total_pedido = 0
                detalhes_formas = []
                
                for proposta in dados_pedido['propostas']:
                    modelo = proposta.get('Modelo', 'Outro').upper()
                    valor = RelatorioService._converter_valor(proposta.get('Valor Total', 0))
                    forma_recebimento = proposta.get('Forma Recebimento', '').strip()
                    numero_parcelas = int(proposta.get('Nº Parcela', 1)) if proposta.get('Nº Parcela') else 1
                    
                    # Calcular valor presente para cada forma de pagamento
                    valor_venda_forma = valor
                    
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
                    
                    # Acumula o valor presente
                    valor_venda_total_pedido += valor_venda_forma
                    detalhes_formas.append({
                        'valor_original': valor,
                        'valor_venda_forma': valor_venda_forma
                    })
                
                # Calcula Meta % usando o valor VP TOTAL (não o valor original)
                percentual_meta = (valor_venda_total_pedido / valor_tabela * 100) if valor_tabela > 0 else 100
                
                # Calcula comissão apenas se houver valor VP válido
                if valor_venda_total_pedido > 0:
                    # Calcula comissão uma única vez sobre o total de todas as formas
                    eh_ac = 'AC' in dados_pedido['propostas'][0].get('Modelo', '').upper()
                    aliquota, _ = ComissaoService._obter_aliquota_banco(mongo.db, percentual_meta, eh_ac, eh_interno)
                    comissao_total = round(valor_venda_total_pedido * aliquota, 2)
                    
                    vendedores[nome_vendedor]['total_vendas'] += valor_venda_total_pedido
                    vendedores[nome_vendedor]['total_comissoes'] += comissao_total
                    vendedores[nome_vendedor]['quantidade_propostas'] += len(dados_pedido['propostas'])
                else:
                    # Sem valor de venda, apenas registra sem comissão (transações de ajuste)
                    vendedores[nome_vendedor]['total_vendas'] += 0
                    vendedores[nome_vendedor]['total_comissoes'] += 0
                    vendedores[nome_vendedor]['quantidade_propostas'] += len(dados_pedido['propostas'])
            
            # Converte para lista e ordena
            resultado = list(vendedores.values())
            resultado = sorted(resultado, key=lambda x: x['total_comissoes'], reverse=True)
            
            import logging
            logging.info(f"Resumo de vendedores: {resultado}")
            
            return resultado
            
        except Exception as e:
            import logging
            logging.error(f"Erro em resumo_comissoes: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def resumo_por_cidade(filtros=None):
        """Gera resumo de comissões por cidade
        
        Fluxo:
        1. Extrai dados da proposta (pessoa, modelo, forma)
        2. GARANTE que vendedor existe (cria se não existir)
        3. GARANTE que moto existe (cria se não existir)
        4. GARANTE que forma existe e está ativa (cria se não existir)
        5. Se passou em TODOS os 4 passos → REGISTRA comissão no banco
        """
        
        try:
            from bson import ObjectId
            
            # Busca as coleções
            saida_col = mongo.db.saida
            proposta_col = mongo.db.propostas
            vendedor_col = mongo.db.vendedores
            moto_col = mongo.db.motos
            
            saida_docs = list(saida_col.find({}))
            proposta_docs = list(proposta_col.find({}))
            
            cidades = {}
            comissoes_registradas = 0
            comissoes_rejeitadas = 0
            
            # Mapeamento: Vendedor -> Cidade (da saida)
            vendedor_cidade = {}
            
            # Primeiro, mapeia cada vendedor com sua cidade (de Origem Venda na saida)
            for doc in saida_docs:
                vendedor_nome = doc.get('Vendedor', '').strip()
                cidade = doc.get('Origem Venda', '').strip()
                
                if vendedor_nome and cidade:
                    vendedor_cidade[vendedor_nome] = cidade
            
            # Agora processa propostas buscando pela pessoa (cliente)
            # Mapeia cliente -> vendedor (via saida)
            cliente_vendedor = {}
            for doc in saida_docs:
                pessoa = doc.get('Pessoa', '').strip()
                vendedor_nome = doc.get('Vendedor', '').strip()
                
                if pessoa and vendedor_nome:
                    cliente_vendedor[pessoa] = vendedor_nome
            
            # Processa propostas para calcular comissões
            for doc in proposta_docs:
                pessoa = doc.get('Pessoa', '').strip()
                modelo = doc.get('Modelo', 'Outro').upper()
                valor = RelatorioService._converter_valor(doc.get('Valor Total', 0))
                forma_recebimento = doc.get('Forma Recebimento', '').strip()
                
                if not pessoa:
                    continue
                
                # Encontra o vendedor associado a esse cliente
                vendedor_nome = cliente_vendedor.get(pessoa)
                if not vendedor_nome:
                    comissoes_rejeitadas += 1
                    continue
                
                # PASSO 1: GARANTIR que o vendedor existe (cria se necessário)
                # Usa a cidade mapeada ou vazia se não temos
                cidade_vendedor = vendedor_cidade.get(vendedor_nome, '')
                resultado_vendedor = VendedorService.garantir_vendedor(vendedor_nome, cidade_vendedor)
                if not resultado_vendedor['existe'] and not resultado_vendedor['criado']:
                    # Falha ao garantir vendedor, rejeita comissão
                    comissoes_rejeitadas += 1
                    continue
                
                vendedor = resultado_vendedor['vendedor']
                eh_interno = vendedor.get('interno', False)
                
                # PASSO 2: GARANTIR que a moto existe (cria se necessário)
                # Detecta se é alta CC pelo nome (heurística simples)
                eh_alta_cc = RelatorioService._detectar_alta_cc(modelo)
                resultado_moto = MotoService.garantir_moto(modelo, eh_alta_cc)
                if not resultado_moto['existe'] and not resultado_moto['criado']:
                    # Falha ao garantir moto, rejeita comissão
                    comissoes_rejeitadas += 1
                    continue
                
                # PASSO 3: GARANTIR que a forma de recebimento existe (cria se necessário)
                if forma_recebimento:
                    resultado_forma = FormaRecebimentoService.garantir_forma(forma_recebimento)
                    if not resultado_forma['existe'] and not resultado_forma['criado']:
                        # Falha ao garantir forma, rejeita comissão
                        comissoes_rejeitadas += 1
                        continue
                
                # Encontra a cidade do vendedor
                cidade = vendedor_cidade.get(vendedor_nome, '').strip()
                if not cidade:
                    comissoes_rejeitadas += 1
                    continue
                
                # PASSO 4: Calcula comissão (todos os dados estão garantidos)
                eh_ac = 'AC' in modelo
                
                # Usa valor nominal (sem taxa progressiva)
                valor_base = valor
                
                aliquota, _ = ComissaoService._obter_aliquota_banco(mongo.db, 100, eh_ac, eh_interno)
                comissao = round(valor_base * aliquota, 2)
                
                # PASSO 5: REGISTRA comissão no banco (SÓ se passou em TODOS os passos)
                resultado_registro = ComissaoService.registrar_comissao({
                    'vendedor': vendedor_nome,
                    'cidade': cidade,
                    'modelo': modelo,
                    'valor_venda': valor,
                    'valor_comissao': comissao,
                    'aliquota': aliquota * 100,
                    'forma_recebimento': forma_recebimento,
                    'eh_interno': eh_interno
                })
                
                if resultado_registro['sucesso']:
                    comissoes_registradas += 1
                    # Agrega para resumo por cidade
                    if cidade not in cidades:
                        cidades[cidade] = {
                            'cidade': cidade,
                            'total_vendas': 0,
                            'total_comissoes': 0,
                            'quantidade': 0
                        }
                    
                    cidades[cidade]['total_comissoes'] += comissao
                    cidades[cidade]['total_vendas'] += valor
                    cidades[cidade]['quantidade'] += 1
                else:
                    comissoes_rejeitadas += 1
            
            resultado = list(cidades.values())
            resultado = sorted(resultado, key=lambda x: x['total_comissoes'], reverse=True)
            
            import logging
            logging.info(f"Resumo por cidade: {resultado} | Registradas: {comissoes_registradas}, Rejeitadas: {comissoes_rejeitadas}")
            
            return resultado
            
        except Exception as e:
            import logging
            logging.error(f"Erro em resumo_por_cidade: {str(e)}", exc_info=True)
            return []


class FormaRecebimentoService:
    """Serviço para gerenciar formas de recebimento"""
    
    @staticmethod
    def garantir_forma(nome_forma):
        """Garante que a forma de recebimento existe no banco. Se não existir, cria automaticamente.
        
        Args:
            nome_forma (str): Nome da forma de recebimento
            
        Returns:
            dict: {'existe': True/False, 'criado': True/False, 'forma': {}}
        """
        try:
            if not nome_forma:
                return {'existe': False, 'criado': False, 'forma': None}
            
            col = mongo.db.formas_recebimento
            nome_forma = nome_forma.strip()
            
            if not nome_forma or nome_forma.lower() == 'desconhecido':
                return {'existe': False, 'criado': False, 'forma': None}
            
            # Verifica se já existe
            existente = col.find_one({'nome': nome_forma})
            
            if existente:
                return {'existe': True, 'criado': False, 'forma': existente}
            
            # Não existe, cria automaticamente
            forma = FormaRecebimentoModel.create({
                'nome': nome_forma,
                'status': 'ativo'
            })
            col.insert_one(forma)
            
            return {'existe': False, 'criado': True, 'forma': forma}
        except Exception as e:
            import logging
            logging.error(f"Erro ao garantir forma de recebimento {nome_forma}: {str(e)}", exc_info=True)
            return {'existe': False, 'criado': False, 'forma': None}
    
    @staticmethod
    def criar_forma(dados):
        """Cria uma nova forma de recebimento"""
        try:
            col = mongo.db.formas_recebimento
            existente = col.find_one({'nome': dados.get('nome')})
            
            if existente:
                return {'erro': 'Forma de recebimento já existe'}
            
            forma = FormaRecebimentoModel.create(dados)
            col.insert_one(forma)
            
            return {'sucesso': True, 'id': str(forma['_id'])}
        except Exception as e:
            import logging
            logging.error(f"Erro ao criar forma de recebimento: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def listar_formas(status='ativo'):
        """Lista formas de recebimento"""
        try:
            col = mongo.db.formas_recebimento
            query = {'status': status} if status else {}
            formas = list(col.find(query).sort('nome', 1))
            
            # Converte ObjectId para string
            for f in formas:
                f['_id'] = str(f['_id'])
            
            return formas
        except Exception as e:
            import logging
            logging.error(f"Erro ao listar formas de recebimento: {str(e)}", exc_info=True)
            return []
    
    @staticmethod
    def obter_forma(forma_id):
        """Obtém uma forma de recebimento por ID"""
        try:
            from bson import ObjectId
            col = mongo.db.formas_recebimento
            forma = col.find_one({'_id': ObjectId(forma_id)})
            
            if forma:
                forma['_id'] = str(forma['_id'])
            
            return forma
        except Exception as e:
            import logging
            logging.error(f"Erro ao obter forma de recebimento: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def desativar_forma(forma_id):
        """Desativa uma forma de recebimento (soft delete)"""
        try:
            from bson import ObjectId
            col = mongo.db.formas_recebimento
            
            result = col.update_one(
                {'_id': ObjectId(forma_id)},
                {'$set': {'status': 'inativo', 'data_atualizacao': datetime.now()}}
            )
            
            return {'sucesso': result.modified_count > 0}
        except Exception as e:
            import logging
            logging.error(f"Erro ao desativar forma de recebimento: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def deletar_forma(forma_id):
        """Deleta uma forma de recebimento permanentemente"""
        try:
            from bson import ObjectId
            col = mongo.db.formas_recebimento
            
            result = col.delete_one({'_id': ObjectId(forma_id)})
            
            return {'sucesso': result.deleted_count > 0}
        except Exception as e:
            import logging
            logging.error(f"Erro ao deletar forma de recebimento: {str(e)}", exc_info=True)
            return {'erro': str(e)}
    
    @staticmethod
    def atualizar_aplicar_vp(forma_id, aplicar_vp, taxa_juros=0.0, tabela_progressiva_id=''):
        """Atualiza se a forma aplica Valor Presente (VP)
        
        Args:
            forma_id (str): ID da forma de recebimento
            aplicar_vp (bool): Se aplica VP
            taxa_juros (float): Taxa de juros mensal (ex: 0.015 para 1.5%)
            tabela_progressiva_id (str): ID da tabela progressiva a usar (opcional)
            
        Returns:
            dict: {'sucesso': bool, 'forma': dict}
        """
        try:
            from bson import ObjectId
            from datetime import datetime
            
            col = mongo.db.formas_recebimento
            
            # Se está usando tabela progressiva, ignora taxa_juros fixa
            # Se não está usando tabela progressiva, usa a taxa_juros
            dados_atualizacao = {
                'aplicar_vp': bool(aplicar_vp),
                'taxa_juros': float(taxa_juros) if not tabela_progressiva_id else 0.0,
                'tabela_progressiva_id': str(tabela_progressiva_id) if tabela_progressiva_id else '',
                'data_atualizacao': datetime.now()
            }
            
            result = col.update_one(
                {'_id': ObjectId(forma_id)},
                {'$set': dados_atualizacao}
            )
            
            if result.modified_count > 0:
                forma_atualizada = col.find_one({'_id': ObjectId(forma_id)})
                forma_atualizada['_id'] = str(forma_atualizada['_id'])
                return {'sucesso': True, 'forma': forma_atualizada}
            else:
                return {'sucesso': False}
        except Exception as e:
            import logging
            logging.error(f"Erro ao atualizar aplicar_vp: {str(e)}", exc_info=True)
            return {'sucesso': False, 'erro': str(e)}
    
    @staticmethod
    def sincronizar_formas(formas_dados):
        """Sincroniza formas de recebimento do upload (cria as que faltam)
        
        formas_dados: lista de nomes de formas ou dict com nomes
        
        Retorna: dict com status, novo_count, duplicado_count, novos, duplicados
        """
        try:
            col = mongo.db.formas_recebimento
            novo_count = 0
            duplicado_count = 0
            novos = []
            duplicados = []
            
            # Se for lista, processa
            if isinstance(formas_dados, (list, set)):
                formas_dados = list(formas_dados)
            else:
                formas_dados = []
            
            for nome in formas_dados:
                if not nome:
                    continue
                
                nome = str(nome).strip()
                if not nome or nome.lower() == 'desconhecido':
                    continue
                
                # Verifica se já existe (CASE-INSENSITIVE para evitar duplicatas)
                existente = col.find_one({'nome': {'$regex': f'^{nome}$', '$options': 'i'}})
                
                if not existente:
                    # Cria nova forma de recebimento
                    forma = FormaRecebimentoModel.create({
                        'nome': nome,
                        'status': 'ativo'
                    })
                    col.insert_one(forma)
                    novo_count += 1
                    novos.append(nome)
                else:
                    # Forma já existe
                    duplicado_count += 1
                    duplicados.append(nome)
            
            return {
                'sucesso': True,
                'novo_count': novo_count,
                'duplicado_count': duplicado_count,
                'novos': novos,
                'duplicados': duplicados
            }
        except Exception as e:
            import logging
            logging.error(f"Erro ao sincronizar formas de recebimento: {str(e)}", exc_info=True)
            return {'erro': str(e)}
