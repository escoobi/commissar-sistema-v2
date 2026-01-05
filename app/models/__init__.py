# -*- coding: utf-8 -*-
"""
Modelos de dados para MongoDB
"""

from datetime import datetime
from bson import ObjectId

class VendedorModel:
    """Modelo para Vendedor"""
    
    COLLECTION = 'vendedores'
    
    @staticmethod
    def create(data):
        """Cria um novo vendedor"""
        return {
            '_id': ObjectId(),
            'nome': data.get('nome', ''),
            'cidade': data.get('cidade', ''),
            'interno': data.get('interno', False),  # True = interno, False = externo
            'status': data.get('status', 'ativo'),  # ativo ou inativo
            'data_cadastro': datetime.now(),
            'data_atualizacao': datetime.now()
        }

class MotoModel:
    """Modelo para Motocicleta"""
    
    COLLECTION = 'motos'
    
    @staticmethod
    def create(data):
        """Cria uma nova motocicleta"""
        return {
            '_id': ObjectId(),
            'nome': data.get('nome', ''),
            'alta_cc': data.get('alta_cc', False),  # True = Alta CC, False = Não
            'valor_tabela': data.get('valor_tabela', 0.0),  # Valor da tabela em reais
            'status': data.get('status', 'ativo'),  # ativo ou inativo
            'data_cadastro': datetime.now(),
            'data_atualizacao': datetime.now()
        }

class PropostaModel:
    """Modelo para Proposta de Venda"""
    
    COLLECTION = 'propostas'
    
    @staticmethod
    def create(data):
        """Cria uma nova proposta"""
        return {
            '_id': ObjectId(),
            'id': data.get('id'),
            'data': data.get('data', datetime.now()),
            'vendedor': data.get('vendedor'),
            'loja': data.get('loja'),
            'modelo': data.get('modelo'),
            'valor_venda': float(data.get('valor_venda', 0)),
            'valor_proposta': float(data.get('valor_proposta', 0)),
            'tipo_pagamento': data.get('tipo_pagamento'),
            'parcelas': int(data.get('parcelas', 1)),
            'cidade': data.get('cidade'),
            'status': 'ativo',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @staticmethod
    def to_dict(doc):
        """Converte documento MongoDB para dict"""
        if not doc:
            return None
        doc['id'] = str(doc.get('_id'))
        return doc


class ComissaoModel:
    """Modelo para Comissão Calculada"""
    
    COLLECTION = 'comissoes'
    
    @staticmethod
    def create(data):
        """Cria um novo registro de comissão"""
        return {
            '_id': ObjectId(),
            'id_proposta': data.get('id_proposta'),
            'vendedor': data.get('vendedor'),
            'modelo': data.get('modelo'),
            'cidade': data.get('cidade'),
            'valor_venda': float(data.get('valor_venda', 0)),
            'valor_meta': float(data.get('valor_meta', 0)),
            'percentual_meta': float(data.get('percentual_meta', 0)),
            'valor_comissao': float(data.get('valor_comissao', 0)),
            'aliquota': float(data.get('aliquota', 0)),
            'alta_cilindrada': bool(data.get('alta_cilindrada', False)),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @staticmethod
    def to_dict(doc):
        """Converte documento MongoDB para dict"""
        if not doc:
            return None
        doc['id'] = str(doc.get('_id'))
        return doc


class UsuarioModel:
    """Modelo para Usuário"""
    
    COLLECTION = 'usuarios'
    
    @staticmethod
    def create(data):
        """Cria um novo usuário"""
        return {
            '_id': ObjectId(),
            'email': data.get('email'),
            'nome': data.get('nome'),
            'role': data.get('role', 'user'),
            'ativo': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }


class FormaRecebimentoModel:
    """Modelo para Forma de Recebimento"""
    
    COLLECTION = 'formas_recebimento'
    
    @staticmethod
    def create(data):
        """Cria uma nova forma de recebimento"""
        return {
            '_id': ObjectId(),
            'nome': data.get('nome', ''),
            'status': data.get('status', 'ativo'),  # ativo ou inativo
            'aplicar_vp': data.get('aplicar_vp', False),  # Se aplica Valor Presente
            'taxa_juros': data.get('taxa_juros', 0.0),  # Taxa de juros para VP (fallback)
            'tabela_progressiva_id': data.get('tabela_progressiva_id', ''),  # ID da tabela progressiva (se usar)
            'data_cadastro': datetime.now(),
            'data_atualizacao': datetime.now()
        }
