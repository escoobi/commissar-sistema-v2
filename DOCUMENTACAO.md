# 📖 Documentação do Sistema de Comissão 2.0

**Versão:** 2.0  
**Data de Atualização:** Janeiro 5, 2026  
**Status:** ✅ Pronto para Produção

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Fórmula HP12C](#fórmula-hp12c)
4. [Guia de Instalação](#guia-de-instalação)
5. [Guia de Uso](#guia-de-uso)
6. [API Endpoints](#api-endpoints)
7. [Processo de Cálculo](#processo-de-cálculo)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O Sistema de Comissão 2.0 é uma aplicação web para cálculo automático de comissões de vendedores de motocicletas. O sistema foi completamente refatorado com as seguintes melhorias:

### ✨ Principais Características

- ✅ **Fórmula HP12C Inversa**: Cálculo correto de valor presente para vendas parceladas
- ✅ **Múltiplas Formas de Pagamento**: Agrupamento automático por pedido + nota fiscal
- ✅ **Meta % Dinâmica**: Calcula percentual de meta sobre valor presente total
- ✅ **Tabelas de Alíquota**: Comissões variam por tipo de moto (Alta CC/Baixa CC) e vendedor (interno/externo)
- ✅ **Upload Automático**: Processa CSVs de saída e propostas
- ✅ **Relatórios em Tempo Real**: Visualização imediata de comissões por vendedor

---

## 🏗️ Arquitetura

### Stack Tecnológico

```
Frontend:
  └── HTML5 + CSS (Bulma Framework)
  └── JavaScript Vanilla
  └── Fetch API para comunicação

Backend:
  └── Flask 3.0.0
  └── Flask-PyMongo 2.3.0
  └── Pandas 2.1.3
  └── Python 3.11

Database:
  └── MongoDB 5.0+
  └── Coleções: propostas, saida, vendedores, motos, 
                formas_recebimento, parametros_aliquota
```

### Estrutura de Pastas

```
sas-comissao/
├── app/
│   ├── __init__.py              # Factory da aplicação
│   ├── models/                  # Modelos MongoDB
│   │   └── __init__.py
│   ├── services/                # Lógica de negócio
│   │   └── __init__.py          # ComissaoService, RelatorioService
│   ├── routes.py                # Endpoints da API
│   ├── templates/               # Templates HTML
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── relatorios.html
│   │   └── vendedores.html
│   └── static/                  # CSS, JS, imagens
│       ├── css/
│       └── js/
├── uploads/                     # Arquivos CSV carregados
├── logs/                        # Arquivos de log
├── .env                         # Variáveis de ambiente
├── requirements.txt             # Dependências Python
└── run.py                       # Entry point da aplicação
```

---

## 📐 Fórmula HP12C

### Problema Resolvido

Vendas parceladas com taxa de juros precisam ter o valor **trazido ao presente** para cálculo correto da meta. Exemplo:

**Cenário:**
- Venda: R$ 11.126,80 em 10 parcelas
- Taxa de juros: 1,59% ao mês
- Valor Tabela (Meta): R$ 10.212,59

### Fórmula Implementada

A fórmula HP12C inversa (Present Value) foi implementada:

```
PV = PMT × [((1+i)^n - 1) / (i × (1+i)^n)]

Onde:
  PV  = Valor Presente (o que buscamos)
  PMT = Parcela mensal (valor_total / numero_parcelas)
  i   = Taxa de juros decimal (taxa_juros / 100)
  n   = Número de parcelas
```

### Implementação em Python

```python
# Em app/services/__init__.py
class ValorPresenteService:
    @staticmethod
    def calcular_valor_com_juro_simples(valor_total, numero_parcelas, taxa_juros):
        """
        Calcula valor presente usando fórmula HP12C inversa
        
        Args:
            valor_total: Valor total da venda parcelada
            numero_parcelas: Número de parcelas
            taxa_juros: Taxa de juros em decimal (ex: 0.0159 para 1.59%)
        
        Returns:
            float: Valor presente (trazido ao presente)
        """
        if numero_parcelas <= 1:
            return valor_total
        
        if taxa_juros <= 0:
            return valor_total
        
        pmt = valor_total / numero_parcelas
        numerador = (1 + taxa_juros) ** numero_parcelas - 1
        denominador = taxa_juros * ((1 + taxa_juros) ** numero_parcelas)
        
        valor_presente = pmt * (numerador / denominador)
        return round(valor_presente, 2)
```

### Exemplo de Cálculo

**Dados de Entrada:**
- Valor Total: R$ 11.126,80
- Parcelas: 10
- Taxa: 1,59% a.m.

**Cálculo:**
```
PMT = 11.126,80 / 10 = 1.112,68
i = 0,0159
n = 10

Numerador = (1,0159)^10 - 1 = 0,166837
Denominador = 0,0159 × (1,0159)^10 = 0,0265978

PV = 1.112,68 × (0,166837 / 0,0265978)
PV = 1.112,68 × 6,2762
PV = R$ 6.987,43  (Valor presente)
```

---

## 🚀 Guia de Instalação

### Pré-requisitos

- Python 3.11+
- MongoDB 5.0+
- Git

### Passo 1: Clonar Repositório

```bash
cd "c:\Users\Administrador\OneDrive - rondomotos"
git clone <seu-repositório>
cd sas-comissao
```

### Passo 2: Criar Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Configurar .env

```bash
# Editar .env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True

MONGO_URI=mongodb://localhost:27017/comissao_db
SECRET_KEY=seu-secret-key-aqui

UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS=csv,xlsx
MAX_CONTENT_LENGTH=16777216

LOG_LEVEL=DEBUG
```

### Passo 5: Iniciar Aplicação

```bash
python run.py
```

Acesse: http://localhost:5000

---

## 📱 Guia de Uso

### 1. Upload de Dados

#### Arquivo de Saída (Tabela de Motos)

**Colunas Necessárias:**
```
Vendedor | Pessoa | Pedido | Doc Fiscal | Modelo | Valor Tabela
PAULO    | JOÃO   | 27421  | NF-E ...   | CG 160 | 10.212,59
```

**Como Fazer Upload:**
1. Vá para http://localhost:5000/
2. Clique em "Upload Saída"
3. Selecione arquivo CSV
4. Clique "Processar"

#### Arquivo de Propostas (Vendas)

**Colunas Necessárias:**
```
Nº Pedido | Doc Fiscal | Pessoa | Modelo | Forma Recebimento | Nº Parcela | Valor Total
27421     | NF-E ...   | JOÃO   | CG 160 | CARTÃO            | 10         | 11.126,80
27421     | NF-E ...   | JOÃO   | CG 160 | DEPÓSITO          | 1          | 12.250,00
```

### 2. Visualizar Relatórios

**Relatório por Vendedor:**
1. Vá para http://localhost:5000/relatorios
2. Veja resumo de comissões por vendedor
3. Clique em "Ver Detalhes" para expandir

**Detalhes de Vendas:**
1. No relatório, clique no nome do vendedor
2. Visualize todas as propostas com:
   - Número do pedido
   - Modelo da moto
   - Valor da venda
   - Meta % calculada
   - Comissão
   - Alíquota aplicada

### 3. Processar Comissões

1. Clique em "Processar Comissões"
2. Sistema calcula todas as comissões
3. Salva no banco de dados
4. Gera PDF do relatório

---

## 🔌 API Endpoints

### Relatórios

#### GET /api/resumo/vendedor
Retorna resumo de comissões por vendedor

**Response:**
```json
{
  "status": "sucesso",
  "dados": [
    {
      "vendor_name": "PAULO BRAIDO",
      "total_vendas": 78829.01,
      "total_comissoes": 1236.78,
      "quantidade_propostas": 8,
      "eh_interno": true
    }
  ]
}
```

#### GET /api/vendedor/vendas?nome=PAULO%20BRAIDO
Retorna todas as vendas de um vendedor específico

**Response:**
```json
{
  "status": "sucesso",
  "eh_interno": true,
  "dados": [
    {
      "Nº Pedido": 27421,
      "Doc Fiscal": "NF-E 407979/1",
      "Modelo": "CG 160",
      "Forma Recebimento": "CARTÃO",
      "Nº Parcela": 10,
      "Valor Total": 11126.80,
      "valor_venda": 10212.59,
      "percentual_meta": 100.96,
      "comissao": 204.25,
      "aliquota": 2.0
    }
  ]
}
```

#### POST /api/comissoes/processar
Processa todas as comissões e salva no banco

**Request:**
```bash
POST /api/comissoes/processar
```

**Response:**
```json
{
  "status": "sucesso",
  "mensagem": "Comissões processadas com sucesso",
  "total_comissoes": 46,
  "total_valor": 45862.50
}
```

---

## 🧮 Processo de Cálculo

### Fluxo Completo de Cálculo

```
1. AGRUPAMENTO POR PEDIDO + DOC FISCAL
   ├─ Busca todas as propostas
   ├─ Agrupa por: "Pedido|DocFiscal"
   └─ Cria chaves compostas para evitar misturar vendas diferentes

2. CÁLCULO DE VALOR PRESENTE
   ├─ Para cada forma de pagamento
   ├─ Se tem taxa de juros e múltiplas parcelas:
   │  └─ Aplica fórmula HP12C inversa
   └─ Soma todos os VP (todas as formas)

3. CÁLCULO DE META %
   ├─ Busca Valor Tabela da saída
   ├─ Calcula: Meta % = (VP Total / Valor Tabela) × 100
   └─ Exemplo: (22.462,59 / 22.300,00) × 100 = 100,73%

4. BUSCA DE ALÍQUOTA
   ├─ Verifica tipo de moto (Alta CC ou Baixa CC)
   ├─ Verifica se vendedor é interno ou externo
   ├─ Busca range de meta na tabela parametros_aliquota
   └─ Exemplo: 100% < meta < 120% → alíquota = 2,0%

5. CÁLCULO DE COMISSÃO
   ├─ Total = VP Total × Alíquota
   ├─ Distribui proporcionalmente entre formas
   └─ Exemplo: 22.462,59 × 0,02 = R$ 449,25

6. ARMAZENAMENTO
   ├─ Salva cada proposta com comissão calculada
   └─ Disponibiliza em relatórios
```

### Exemplo Prático: Pedido 27421

**Dados de Entrada:**
```
Forma 1 (CARTÃO):     R$ 11.126,80 em 10x @ 1,59%
Forma 2 (DEPÓSITO):   R$ 12.250,00 à vista
Valor Tabela:         R$ 22.300,00
Vendedor:             PAULO BRAIDO (interno)
Modelo:               CG 160 (Baixa CC)
```

**Passo 1 - Cálculo de VP:**
```
CARTÃO:   PV = R$ 10.212,59  (aplicou HP12C)
DEPÓSITO: PV = R$ 12.250,00  (à vista)
TOTAL VP: R$ 22.462,59
```

**Passo 2 - Meta %:**
```
Meta % = (22.462,59 / 22.300,00) × 100 = 100,73%
```

**Passo 3 - Alíquota:**
```
Intervalo: 100% < 100,73% < 120%
Alíquota: 2,0%
```

**Passo 4 - Comissão:**
```
Total: 22.462,59 × 0,02 = R$ 449,25

Distribuição proporcional:
  CARTÃO:   (10.212,59 / 22.462,59) × 449,25 = R$ 204,25
  DEPÓSITO: (12.250,00 / 22.462,59) × 449,25 = R$ 245,00
```

---

## 🐛 Troubleshooting

### Problema: "Vendedor não encontrado"

**Causa:** Arquivo de saída não foi enviado
**Solução:**
1. Vá para http://localhost:5000/
2. Clique em "Upload Saída"
3. Envie o CSV com dados dos vendedores
4. Clique "Processar"

### Problema: Frontend mostra dados antigos

**Causa:** Cache do navegador
**Solução:**
1. Pressione `Ctrl+Shift+R` (hard refresh)
2. Ou: Ctrl+Shift+Delete (limpar cache completo)

### Problema: Cálculo de comissão está zero

**Causa:** Valor presente total é 0 (ajuste de pedido)
**Solução:**
- Isso é esperado para pedidos com valores negativos
- Sistema não calcula comissão quando VP ≤ 0

### Problema: Meta % acima de 200%

**Causa:** Valor presente > valor tabela (venda foi bem)
**Solução:**
- Isso é normal quando VP > Valor Tabela
- Alíquota progressiva é aplicada corretamente

### Problema: MongoDB não conecta

**Verificar:**
1. MongoDB está rodando? `mongo --version`
2. URI correta em `.env`?
3. Banco de dados `comissao_db` existe?

**Comando para testar:**
```bash
# Via Powershell
python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017').admin.command('ping')"
```

---

## 📊 Modelo de Dados

### Coleção: propostas

```json
{
  "_id": ObjectId,
  "Nº Pedido": 27421,
  "Doc Fiscal": "NF-E 407979/1",
  "Pessoa": "JOÃO SILVA",
  "Modelo": "CG 160",
  "Forma Recebimento": "CARTÃO",
  "Nº Parcela": 10,
  "Valor Total": 11126.80,
  "comissao": 204.25,
  "valor_presente": 10212.59,
  "percentual_meta": 100.73,
  "aliquota": 0.02
}
```

### Coleção: saida

```json
{
  "_id": ObjectId,
  "Vendedor": "PAULO BRAIDO",
  "Pessoa": "JOÃO SILVA",
  "Pedido": 27421,
  "Doc Fiscal": "NF-E 407979/1",
  "Modelo": "CG 160",
  "Valor Tabela": 22300.00
}
```

### Coleção: vendedores

```json
{
  "_id": ObjectId,
  "nome": "PAULO BRAIDO",
  "interno": true,
  "status": "ativo"
}
```

### Coleção: formas_recebimento

```json
{
  "_id": ObjectId,
  "nome": "CARTÃO",
  "aplicar_vp": true,
  "taxa_juros": 1.59,
  "status": "ativo"
}
```

### Coleção: parametros_aliquota

```json
{
  "_id": ObjectId,
  "eh_interno": true,
  "tipo_moto": "Baixa CC",
  "meta_min": 100,
  "meta_max": 120,
  "aliquota": 0.02
}
```

---

## 🔐 Segurança

### Medidas Implementadas

- ✅ Validação de entrada (tipos de arquivo)
- ✅ Limite de tamanho de upload (16MB)
- ✅ Queries parametrizadas no MongoDB
- ✅ Tratamento de exceções centralizado
- ✅ Logs de auditoria

### Boas Práticas

1. **Nunca compartilhe `.env`**
2. **Use SECRET_KEY forte** em produção
3. **Configure CORS** se frontend estiver em outro domínio
4. **Faça backup regular** do MongoDB

---

## 📈 Performance

### Otimizações Implementadas

- ✅ Índices MongoDB nas coleções principais
- ✅ Cache de lookups (valor_tabela_map)
- ✅ Processamento em batch para uploads
- ✅ Paginação nos endpoints de listagem

### Timeouts Típicos

- Upload pequeno (< 1MB): < 1 segundo
- Cálculo de 100 propostas: 2-3 segundos
- Relatório de 50 vendedores: < 1 segundo

---

## 📞 Suporte e Contribuição

Para dúvidas ou sugestões de melhoria:

1. Verifique a seção [Troubleshooting](#troubleshooting)
2. Consulte os logs em `logs/comissao.log`
3. Teste via MongoDB shell diretamente

---

## 📝 Changelog

### v2.0 (Janeiro 2026)

✅ **Implementado:**
- Fórmula HP12C inversa para valor presente
- Agrupamento por pedido + doc fiscal (composite key)
- Cálculo de Meta % sobre VP total
- Distribuição proporcional de comissão
- Case-insensitive search para vendedores/formas

✅ **Corrigido:**
- Bug de duplicação de vendedores (case sensitivity)
- Bug de mistura de pedidos com mesma numeração

### v1.0 (Versão Original)

- Cálculo básico de comissões
- Uploads simples
- Relatórios por vendedor

---

**FIM DA DOCUMENTAÇÃO**

*Última atualização: Janeiro 5, 2026*
