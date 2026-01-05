# 🏗️ Arquitetura da Integração

## Diagrama de Classes

```
┌──────────────────────────────────────────────────────────────────┐
│                   ValorPresenteService                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  + calcular_valor_presente()                                     │
│    └─ Calcula VP com taxa fixa (método original)                │
│                                                                  │
│  + calcular_valor_presente_com_coeficientes() ← NOVO!           │
│    └─ Calcula VP com coeficientes progressivos                  │
│                                                                  │
│  + calcular_desconto_percentual()                               │
│    └─ Calcula % de desconto                                     │
│                                                                  │
│  + detectar_taxa_padrao()                                       │
│    └─ Obtém taxa fixa do banco (fallback)                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ usa
                              │
┌──────────────────────────────────────────────────────────────────┐
│                   TaxaProgressivaService                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  + buscar_coeficientes(forma, numero_parcelas)                  │
│    └─ Retorna [coef1, coef2, ..., coefn] ou None               │
│                                                                  │
│  + criar_tabela()                                               │
│  + listar_tabelas()                                             │
│  + obter_tabela()                                               │
│  + atualizar_tabela()                                           │
│  + deletar_tabela()                                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ▲
                              │ usa
                              │
┌──────────────────────────────────────────────────────────────────┐
│                   RelatorioService                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  + resumo_por_cidade() ← INTEGRADO!                             │
│    │                                                            │
│    ├─→ Para cada proposta:                                     │
│    │   ├─→ Extrai: forma, numero_parcelas, valor              │
│    │   ├─→ Busca coeficientes progressivos                    │
│    │   │   ├─ SIM → Calcula VP com progressivo               │
│    │   │   └─ NÃO → Fallback para taxa fixa                  │
│    │   └─→ Calcula comissão = VP × aliquota                  │
│    │                                                           │
│    └─→ Registra comissão no banco                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados

```
CSV / Excel
  │
  ├─ Pessoa
  ├─ Modelo
  ├─ Valor Total
  ├─ Forma Recebimento ─────┐
  └─ Numero Parcelas ────────┤
                            │
                            ↓
                  TaxaProgressivaService
                  .buscar_coeficientes()
                            │
                  ┌─────────┴─────────┐
                  │                   │
              ENCONTROU          NÃO ENCONTROU
                  │                   │
                  ↓                   ↓
          coeficientes[]      detectar_taxa_padrao()
                  │                   │
                  ↓                   ↓
    calcular_valor_presente_  calcular_valor_presente()
    com_coeficientes()        │ ou
         (NOVO)                  │ valor_nominal
                  │              │
                  └──────┬───────┘
                         │
                         ↓
                    valor_base
                         │
                         ↓
                comissao = valor_base × aliquota
                         │
                         ↓
              ComissaoService.registrar_comissao()
                         │
                         ↓
                  MongoDB (colection: comissoes)
```

---

## Integração em resumo_por_cidade()

```python
def resumo_por_cidade(filtros=None):
    """Processa propostas e calcula comissões"""
    
    for proposta in propostas:
        # ... [Passos 1-3: Garantir vendedor, moto, forma] ...
        
        # PASSO 4: Calcula comissão (NOVO CÓDIGO)
        valor_base = proposta['valor']  # padrão: nominal
        
        numero_parcelas = proposta.get('numero_parcelas')
        forma = proposta.get('forma_recebimento')
        
        if numero_parcelas and forma:
            # ┌─── INTEGRAÇÃO AQUI ───┐
            coeficientes = TaxaProgressivaService.buscar_coeficientes(
                forma, 
                numero_parcelas
            )
            
            if coeficientes:
                # Usa progressivo
                valor_base = ValorPresenteService.calcular_valor_presente_com_coeficientes(
                    valor / numero_parcelas,
                    numero_parcelas,
                    coeficientes
                )
            else:
                # Fallback: taxa fixa
                taxa_info = ValorPresenteService.detectar_taxa_padrao(forma)
                if taxa_info['aplicar_vp']:
                    valor_base = ValorPresenteService.calcular_valor_presente(
                        valor / numero_parcelas,
                        numero_parcelas,
                        taxa_info['taxa_juros']
                    )
            # └────────────────────────┘
        
        # Calcula comissão
        comissao = valor_base × aliquota
        
        # Registra comissão
        ComissaoService.registrar_comissao({...})
```

---

## Banco de Dados

### Coleção: `taxas_progressivas`

```json
{
  "_id": ObjectId("65abc123..."),
  "forma_recebimento": "CARTÃO",
  "numero_parcelas": 10,
  "coeficientes": [0, 0.5151, 0.3468, 0.2626, 0.2122, 0.1785, 0.1545, 0.1385, 0.1225, 0.1113],
  "descricao": "Tabela padrão CARTÃO 10 parcelas",
  "ativa": true,
  "data_cadastro": ISODate("2025-12-31T00:00:00Z"),
  "data_atualizacao": ISODate("2025-12-31T00:00:00Z")
}
```

### Coleção: `comissoes` (com integração)

```json
{
  "_id": ObjectId("..."),
  "vendedor": "João Silva",
  "cidade": "São Paulo",
  "modelo": "TITAN 150",
  "valor_venda": 20000.00,
  "valor_comissao": 299.39,        ← Baseado em VP progressivo!
  "aliquota": 1.5,
  "forma_recebimento": "CARTÃO",
  "numero_parcelas": 10,           ← Campo novo (opcional)
  "eh_interno": false,
  "data_registro": ISODate("2025-12-31T00:00:00Z")
}
```

---

## API REST

### Endpoints Existentes (já implementados)

```
GET    /api/taxas-progressivas
       └─ Lista todas as tabelas

POST   /api/taxas-progressivas
       └─ Cria nova tabela

GET    /api/taxas-progressivas/<id>
       └─ Obtém tabela específica

PUT    /api/taxas-progressivas/<id>
       └─ Atualiza coeficientes

DELETE /api/taxas-progressivas/<id>
       └─ Deleta tabela
```

### Endpoints Usados Internamente (durante resumo_por_cidade)

```
TaxaProgressivaService.buscar_coeficientes(forma, parcelas)
├─ Query: {forma_recebimento: "CARTÃO", numero_parcelas: 10, ativa: true}
├─ Retorna: [0, 0.5151, 0.3468, ...] ou None
└─ Não é API HTTP (é chamada interna)
```

---

## Interface Web

```
┌─────────────────────────────────────────────────────┐
│  Menu → Taxas Progressivas                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ CRIAR NOVA TABELA                            │  │
│  ├──────────────────────────────────────────────┤  │
│  │ Forma: [CARTÃO      ]                        │  │
│  │ Parcelas: [10     ] [Gerar Campos]          │  │
│  │ Descrição: [Tabela padrão CARTÃO 10x]       │  │
│  │                                              │  │
│  │ Parcela 1:  [0      ]%                       │  │
│  │ Parcela 2:  [0.5151 ]%                       │  │
│  │ Parcela 3:  [0.3468 ]%                       │  │
│  │ ...                                          │  │
│  │ Parcela 10: [0.1113 ]%                       │  │
│  │                                              │  │
│  │ [Salvar] [Cancelar]                          │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ TABELAS EXISTENTES                           │  │
│  ├──────────────────────────────────────────────┤  │
│  │                                              │  │
│  │ ┌─────────────────────────────────────────┐ │  │
│  │ │ CARTÃO (10x)                            │ │  │
│  │ │ Tabela padrão CARTÃO 10 parcelas        │ │  │
│  │ │ Parc:  1    2    3    4    5    6    7  │ │  │
│  │ │ %:   0.0  0.51  0.34  0.26  0.21  0.17 │ │  │
│  │ │ [Editar] [Deletar]                      │ │  │
│  │ └─────────────────────────────────────────┘ │  │
│  │                                              │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Fluxo de Processamento Completo

```
┌─────────────────────────────────────────────────────────┐
│  USUÁRIO IMPORTA CSV                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  RelatorioService.resumo_por_cidade()                   │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┴─────────────┐
    │                          │
    ↓                          ↓
Para cada proposta:        Processar normalmente
  1. Garantir vendedor
  2. Garantir moto
  3. Garantir forma
    │
    ├─ Tem numero_parcelas? ──┐
    │                         │
    │                    SIM (vai adiante)
    │                         │
    ↓                         ↓
Buscar coeficientes    ┌─ Sem parcelas
   │                   │
   ├─ Encontrou?   NÃO─┘
   │    │
   │   SIM
   │    │
   ├─────┬──────┐
   │     │      │
  SIM   NÃO    ERRO
   │     │      │
   ↓     ↓      ↓
  [A]   [B]    [C]

[A] COM TABELA:
   Calcula VP progressivo
   └─ valor_base = VP_progressivo

[B] SEM TABELA:
   Detecta taxa fixa
   ├─ SIM: calcula VP_taxa_fixa
   │       └─ valor_base = VP_taxa_fixa
   └─ NÃO: usa valor_nominal
           └─ valor_base = valor_nominal

[C] ERRO:
   Log aviso
   └─ valor_base = valor_nominal

    │     │      │
    └─────┴──────┘
          │
          ↓
    comissao = valor_base × aliquota
          │
          ↓
    ComissaoService.registrar_comissao()
          │
          ↓
    MongoDB (comissoes)
          │
          ↓
    Relatório mostrado ao usuário
```

---

## Modificações Mínimas

```
Arquivo: app/services/__init__.py

Adições:
  + 1 novo método (calcular_valor_presente_com_coeficientes)
  + Integração em resumo_por_cidade()

Total de linhas adicionadas: ~50 linhas

Mudanças em métodos existentes: Nenhuma
Mudanças em assinaturas: Nenhuma
Quebra de compatibilidade: Nenhuma
```

---

## Segurança e Tratamento de Erros

```python
try:
    coeficientes = TaxaProgressivaService.buscar_coeficientes(forma, parcelas)
    
    if coeficientes:
        # Valida coeficientes
        if len(coeficientes) != numero_parcelas:
            # Erro: quantidade não bate
            valor_base = valor_nominal
        else:
            # Calcula VP
            vp = ValorPresenteService.calcular_valor_presente_com_coeficientes(...)
            if vp > 0:
                valor_base = vp
            else:
                # Erro no cálculo
                valor_base = valor_nominal
    else:
        # Nenhuma tabela encontrada - fallback
        taxa_info = ValorPresenteService.detectar_taxa_padrao(forma)
        ...

except Exception as e:
    # Qualquer erro
    logging.warning(f"Erro em coeficientes: {e}")
    valor_base = valor_nominal  # Fallback seguro
```

---

## Performance

```
Operações por proposta:
  1. Buscar coeficientes: ~10ms (query MongoDB)
  2. Calcular VP progressivo: ~1ms (10 iterações)
  3. Total por proposta: ~11ms

Para 100 propostas: ~1.1 segundo
Para 1000 propostas: ~11 segundos

Sem índices é rápido
Com índice em (forma_recebimento, numero_parcelas): <5ms
```

---

**Diagrama criado:** 2025-12-31  
**Versão:** 1.0 - Arquitetura Completa
