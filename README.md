# 💼 Sistema de Comissão 2.0

**Sistema Inteligente de Cálculo de Comissões com Fórmula HP12C**

![Status](https://img.shields.io/badge/status-pronto-green)
![Versão](https://img.shields.io/badge/versão-2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![MongoDB](https://img.shields.io/badge/mongodb-5.0+-green)

---

## 🎯 O Que é Este Sistema?

Sistema web completo para **cálculo automático de comissões** de vendedores de motocicletas. Processa vendas parceladas com taxa de juros usando a fórmula HP12C, agrupa automaticamente por pedido + nota fiscal, e gera relatórios detalhados em tempo real.

### ✨ Destaques

- 🧮 **Fórmula HP12C Inversa**: Cálculo correto de valor presente para parcelamentos
- 📊 **Múltiplas Formas de Pagamento**: CARTÃO, DEPÓSITO, FINANCIAMENTO agrupadas por pedido
- 📈 **Meta % Dinâmica**: Percentual calculado sobre valor presente total
- 💰 **Tabelas de Alíquota**: Comissão varia por tipo de moto e vendedor (interno/externo)
- 📱 **Interface Intuitiva**: Upload simples, relatórios em tempo real
- 🔄 **Distribuição Proporcional**: Comissão distribuída entre formas de forma inteligente

---

## 🚀 Quick Start

### 1️⃣ Pré-requisitos

```bash
# Verificar Python
python --version  # Deve ser 3.11+

# Verificar MongoDB
mongo --version
```

### 2️⃣ Instalação

```bash
# Clonar repositório
git clone <seu-repo>
cd sas-comissao

# Criar virtual environment
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3️⃣ Configurar Banco de Dados

```bash
# Verificar conexão MongoDB
mongo mongodb://localhost:27017

# Criar banco de dados (automático)
# O sistema cria comissao_db na primeira execução
```

### 4️⃣ Iniciar Aplicação

```bash
# Terminal 1: Iniciar Flask
python run.py

# Acesso: http://localhost:5000
```

---

## 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [DOCUMENTACAO.md](DOCUMENTACAO.md) | 📚 Documentação completa do sistema |
| [GUIA_TESTES.md](GUIA_TESTES.md) | 🧪 Guia de testes e casos de teste |
| [COMECE_AQUI.txt](COMECE_AQUI.txt) | ⚡ Início rápido (versão anterior) |

---

## 🎓 Tutorial Completo

### Etapa 1: Upload de Dados

#### 1.1 Arquivo de Saída (Tabela de Motos)

**O que é?** Lista de pedidos com seus valores de tabela e vendedores responsáveis

**Colunas necessárias:**
```
Vendedor | Pessoa | Pedido | Doc Fiscal | Modelo | Valor Tabela
```

**Como fazer upload?**
1. Vá para http://localhost:5000/
2. Clique em "Upload Saída"
3. Selecione arquivo CSV
4. Clique "Processar"

#### 1.2 Arquivo de Propostas (Vendas)

**O que é?** Todas as propostas de venda com suas formas de pagamento

**Colunas necessárias:**
```
Nº Pedido | Doc Fiscal | Pessoa | Modelo | Forma Recebimento | Nº Parcela | Valor Total
```

**Como fazer upload?**
1. Vá para http://localhost:5000/
2. Clique em "Upload Proposta"
3. Selecione arquivo CSV
4. Clique "Processar"

### Etapa 2: Visualizar Relatórios

**Acesso:** http://localhost:5000/relatorios

**O que você vê:**
- 📊 Resumo de comissões por vendedor
- 💰 Total de vendas e comissões
- 📋 Quantidade de propostas
- 📈 Média de comissão por venda

**Clique em um vendedor para ver:**
- 🔍 Detalhes de todas as vendas
- 📌 Número do pedido e nota fiscal
- 💵 Valor original vs valor presente
- 📊 Meta % calculada
- 💸 Comissão de cada venda
- 📐 Alíquota aplicada

### Etapa 3: Processar Comissões

**Botão:** "Processar Comissões" no relatório

**O que faz:**
1. ✅ Calcula todas as comissões
2. ✅ Salva no banco de dados
3. ✅ Gera relatório em PDF
4. ✅ Disponibiliza para download

---

## 📐 Como Funciona a Fórmula HP12C

### Problema

Vendas parceladas precisam ser trazidas ao presente para cálculo correto de meta. Exemplo:

```
Venda de R$ 11.126,80 em 10 parcelas com taxa de 1,59% a.m.
Quanto vale HOJE essa venda?
Resposta: R$ 10.212,59 (valor presente)
```

### Solução

Implementamos a fórmula HP12C inversa:

```
PV = PMT × [((1+i)^n - 1) / (i × (1+i)^n)]

PV  = Valor Presente (o que queremos encontrar)
PMT = Parcela mensal
i   = Taxa de juros
n   = Número de parcelas
```

### Cálculo Passo a Passo

```
1. Valor Total: R$ 11.126,80
2. Parcelas: 10
3. Taxa: 1,59% a.m. (0,0159 em decimal)

PMT = 11.126,80 / 10 = 1.112,68

Numerador = (1,0159)^10 - 1 = 0,166837
Denominador = 0,0159 × (1,0159)^10 = 0,0265978

PV = 1.112,68 × (0,166837 / 0,0265978) = R$ 10.212,59
```

### Por Que Importa?

```
SEM HP12C (ERRADO):
  VP = R$ 11.126,80 (valor original)
  Meta % = (11.126,80 / 10.212,59) = 108,9% ❌ INFLACIONADO

COM HP12C (CORRETO):
  VP = R$ 10.212,59 (valor presente)
  Meta % = (10.212,59 / 10.212,59) = 100% ✅ CORRETO
```

---

## 🏗️ Arquitetura

### Stack Tecnológico

```
Frontend
  ├── HTML5 + CSS (Bulma Framework)
  ├── JavaScript Vanilla
  └── Fetch API

Backend
  ├── Flask 3.0.0
  ├── Flask-PyMongo 2.3.0
  ├── Pandas 2.1.3
  └── Python 3.11

Database
  └── MongoDB 5.0+
      ├── propostas (277 docs)
      ├── saida (455 docs)
      ├── vendedores (63 docs)
      ├── motos (23 docs)
      ├── formas_recebimento (15 docs)
      ├── parametros_aliquota (8 docs)
      └── comissoes (sumários)
```

### Fluxo de Dados

```
1. CSV Upload
   └─> Validação → Processamento → MongoDB

2. Cálculo de Comissões
   └─> HP12C → Meta % → Alíquota → Distribuição

3. Relatórios
   └─> Agregação → Formatação → JSON/HTML

4. Armazenamento
   └─> Comissões salvas → Disponíveis para download
```

---

## 🔌 API REST

### Endpoints Principais

#### `GET /api/resumo/vendedor`
Retorna resumo de comissões por vendedor

```bash
curl http://localhost:5000/api/resumo/vendedor
```

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

#### `GET /api/vendedor/vendas?nome=PAULO%20BRAIDO`
Retorna detalhes de todas as vendas de um vendedor

```bash
curl "http://localhost:5000/api/vendedor/vendas?nome=PAULO%20BRAIDO"
```

#### `POST /api/comissoes/processar`
Processa e salva todas as comissões

```bash
curl -X POST http://localhost:5000/api/comissoes/processar
```

---

## 🧪 Testes

### Executar Testes Manuais

Veja [GUIA_TESTES.md](GUIA_TESTES.md) para:
- 6 testes manuais completos
- 6 casos de teste predefinidos
- Dados de teste prontos para usar
- Checklist de verificação

### Teste Rápido

```bash
# 1. Iniciar aplicação
python run.py

# 2. Em outro terminal, testar API
python -c "
import requests
resp = requests.get('http://localhost:5000/api/resumo/vendedor')
print(resp.json())
"
```

---

## 🐛 Troubleshooting

### Problema: MongoDB não conecta

```bash
# Verificar se está rodando
mongo --version

# Conectar manualmente
mongo mongodb://localhost:27017
```

### Problema: "Vendedor não encontrado"

**Solução:** Faça upload do arquivo de saída primeiro

### Problema: Frontend mostra dados antigos

**Solução:** Limpar cache do navegador (Ctrl+Shift+R)

### Problema: Comissão está zero

**Causa possível:** Valor presente total = 0 (é esperado para ajustes)

Veja [DOCUMENTACAO.md](DOCUMENTACAO.md) seção Troubleshooting para mais...

---

## 📊 Exemplos de Uso

### Exemplo 1: Venda Simples

```
Forma: DEPÓSITO
Valor: R$ 12.250,00
Parcelas: 1
Taxa: 0%

Resultado:
  VP: R$ 12.250,00
  Meta: 100%
  Comissão: Conforme alíquota
```

### Exemplo 2: Venda Parcelada com Juros

```
Forma: CARTÃO
Valor: R$ 11.126,80
Parcelas: 10
Taxa: 1,59%

Resultado:
  VP: R$ 10.212,59 (HP12C)
  Meta: 100%
  Comissão: Conforme alíquota
```

### Exemplo 3: Múltiplas Formas

```
Forma 1: CARTÃO    R$ 11.126,80 (10x) → VP: R$ 10.212,59
Forma 2: DEPÓSITO  R$ 12.250,00 (1x)  → VP: R$ 12.250,00
         TOTAL:    R$ 23.376,80        → VP: R$ 22.462,59

Meta: (22.462,59 / 22.300,00) × 100 = 100,73%
Comissão: Distribuída proporcionalmente
  - CARTÃO:   R$ 204,25
  - DEPÓSITO: R$ 245,00
  - TOTAL:    R$ 449,25
```

---

## 📈 Versão Anterior

Veja [COMECE_AQUI.txt](COMECE_AQUI.txt) para documentação da versão 1.0

---

## 🤝 Contribuição

Sugestões de melhoria são bem-vindas! Por favor:

1. Identifique o problema
2. Descreva a solução proposta
3. Teste antes de submeter
4. Documente as mudanças

---

## 📝 License

Projeto privado - Rondomotos

---

## 📞 Contato

Para dúvidas sobre o sistema:
- Consulte [DOCUMENTACAO.md](DOCUMENTACAO.md)
- Veja [GUIA_TESTES.md](GUIA_TESTES.md)
- Verifique logs em `logs/comissao.log`

---

## 🎉 Changelog

### v2.0 (Janeiro 2026) ✅ ATUAL

**Novidades:**
- ✅ Fórmula HP12C inversa para valor presente
- ✅ Agrupamento por pedido + doc fiscal
- ✅ Meta % calculado sobre VP total
- ✅ Distribuição proporcional de comissão
- ✅ Busca case-insensitive para vendedores

**Bugs Corrigidos:**
- ✅ Duplicação de vendedores por case sensitivity
- ✅ Mistura de pedidos com mesma numeração

### v1.0 (Versão Original)

- Cálculo básico de comissões
- Interface simples
- Upload manual

---

**Status:** 🟢 Pronto para Produção  
**Última Atualização:** Janeiro 5, 2026  
**Teste Final:** ✅ Aprovado

