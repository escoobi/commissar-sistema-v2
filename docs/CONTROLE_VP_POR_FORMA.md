# Integração de Valor Presente com Controle por Forma de Recebimento

## 📋 Implementação Realizada

### 1. **Banco de Dados (Modelo)**
✅ Adicionado ao `FormaRecebimentoModel`:
```python
'aplicar_vp': bool        # Se aplica Valor Presente
'taxa_juros': float       # Taxa de juros mensal (ex: 0.015 = 1.5%)
```

### 2. **Serviço de Taxa (Lógica Principal)**
✅ Atualizado `detectar_taxa_padrao()` para:
- Ler do banco de dados campos `aplicar_vp` e `taxa_juros`
- Usar como fallback os valores hardcoded (CARTÃO = 1.5%, CHEQUE = 2.0%, outros = 0%)
- Retornar dict em vez de apenas float:
```python
{
    'aplicar_vp': bool,      # Se deve aplicar VP
    'taxa_juros': float      # Taxa a usar
}
```

### 3. **Endpoint de Atualização**
✅ Criado endpoint `PUT /api/formas-recebimento/<id>/aplicar-vp`:
```python
@api_bp.route('/formas-recebimento/<forma_id>/aplicar-vp', methods=['PUT'])
def atualizar_aplicar_vp(forma_id):
    # Recebe: {'aplicar_vp': bool, 'taxa_juros': float}
    # Retorna: {'status': 'sucesso', 'dados': forma_atualizada}
```

### 4. **Serviço de Forma**
✅ Adicionado método `atualizar_aplicar_vp()`:
```python
FormaRecebimentoService.atualizar_aplicar_vp(forma_id, aplicar_vp, taxa_juros)
```

### 5. **Interface do Usuário (HTML/JS)**
✅ Adicionado na página de formas de recebimento:
- Checkbox: "Aplicar Valor Presente (VP)"
- Campo de entrada: "Taxa de Juros Mensal (%)"
- Atualização dinâmica sem recarregar página
- Exibe status (SIM/NÃO) e taxa atual

---

## 🎯 Como Usar

### **Passo 1: Acessar Gerenciamento de Formas**
1. Acesse: `http://seu-servidor/formas-recebimento`
2. Veja lista de todas as formas cadastradas

### **Passo 2: Ativar VP para uma Forma**
1. Localize a forma (ex: "CARTÃO")
2. Marque o checkbox "Aplicar Valor Presente (VP)"
3. O campo "Taxa de Juros Mensal (%)" aparece automaticamente
4. Defina a taxa (ex: 1.5 para 1.5% ao mês)
5. Sistema atualiza automaticamente (sem botão)

### **Passo 3: Desativar VP (opcional)**
1. Desmarque o checkbox
2. Campo de taxa desaparece
3. Sistema salva alteração

---

## 📊 Exemplo de Uso

### **Cenário**
```
CARTÃO → Aplicar VP? [✓ SIM]
         Taxa: 1.5% ao mês

CHEQUE → Aplicar VP? [✓ SIM]
         Taxa: 2.0% ao mês

DEPÓSITO → Aplicar VP? [✗ NÃO]
           (Taxa não editável)

FINANCIAMENTO → Aplicar VP? [✗ NÃO]
                (Taxa não editável)
```

### **Processamento na Comissão**
```python
# No processamento de propostas:
taxa_info = ValorPresenteService.detectar_taxa_padrao(forma_recebimento)

if taxa_info['aplicar_vp']:
    # Calcular VP com taxa
    vp = ValorPresenteService.calcular_valor_presente(
        valor_parcela,
        numero_parcelas,
        taxa_info['taxa_juros']  # ← Usa taxa do banco
    )
    valor_base_comissao = vp
else:
    # Usar valor nominal (à vista)
    valor_base_comissao = valor_tabela

comissao = valor_base_comissao * aliquota
```

---

## ✅ Checklist de Integração

- ✅ Campo `aplicar_vp` adicionado ao modelo
- ✅ Campo `taxa_juros` adicionado ao modelo
- ✅ Função `detectar_taxa_padrao()` lê do banco
- ✅ Endpoint PUT criado para atualizar
- ✅ Método `atualizar_aplicar_vp()` implementado
- ✅ UI com checkbox e campo de taxa
- ✅ JavaScript para atualizar valores dinamicamente
- ⏳ **PRÓXIMO: Integrar VP no cálculo de comissões**
- ⏳ Atualizar `resumo_por_cidade()` para usar VP
- ⏳ Armazenar VP calculado nas propostas

---

## 🔧 Próximas Alterações Necessárias

### **1. Atualizar `resumo_por_cidade()`**
```python
# PASSO 4: Calcula comissão com VP se aplicável

taxa_info = ValorPresenteService.detectar_taxa_padrao(forma_recebimento)

if taxa_info['aplicar_vp']:
    # Tem VP - calcular valor presente
    valor_parcela = valor / numero_parcelas  # Estimar
    vp_resultado = ValorPresenteService.calcular_desconto_percentual(
        valor,
        valor_parcela,
        numero_parcelas,
        taxa_info['taxa_juros']
    )
    valor_base = vp_resultado['valor_presente']
else:
    # Sem VP - usar valor nominal
    valor_base = valor

# Aplicar alíquota
aliquota, _ = ComissaoService._obter_aliquota_banco(...)
comissao = round(valor_base * aliquota, 2)

# Registrar com referência ao VP
ComissaoService.registrar_comissao({
    'valor_venda': valor,
    'valor_presente': valor_base,  # ← Novo campo
    'desconto_vp': valor - valor_base,
    'taxa_vp': taxa_info['taxa_juros'],
    'aplicou_vp': taxa_info['aplicar_vp'],
    ...
})
```

### **2. Armazenar VP nas Propostas**
```python
# Ao fazer upload de propostas:
for proposta in data:
    forma = proposta['Forma Recebimento']
    taxa_info = ValorPresenteService.detectar_taxa_padrao(forma)
    
    if taxa_info['aplicar_vp']:
        # Calcular VP e armazenar
        vp = ValorPresenteService.calcular_valor_presente(...)
        proposta['valor_presente'] = vp
        proposta['aplicou_vp'] = True
    else:
        proposta['valor_presente'] = proposta['Valor Total']
        proposta['aplicou_vp'] = False
    
    proposta_col.insert_one(proposta)
```

### **3. Relatório Mostrando VP**
```python
# Novo endpoint: GET /api/relatorio/formas-com-vp
# Mostra:
# - Forma de Recebimento
# - Status (Ativo/Inativo)
# - Aplica VP? (SIM/NÃO)
# - Taxa (%)
# - Total Vendas
# - VP Total
# - Desconto Total
# - Comissões Impactadas
```

---

## 🎨 Comportamento da UI Atual

### **Página: Formas de Recebimento**

**Forma ATIVA com VP:**
```
┌──────────────────────────────────────────┐
│ CARTÃO                                   │
│ Status: Ativo                            │
│ Aplicar VP: SIM ✓                        │
│ Taxa de Juros: 1.50% ao mês              │
│                                          │
│ ☑ Aplicar Valor Presente (VP)            │
│                                          │
│ Taxa de Juros Mensal (%)                 │
│ [1.50                                  ] │
│                                          │
│ [Desativar] [Deletar]                    │
└──────────────────────────────────────────┘
```

**Forma ATIVA sem VP:**
```
┌──────────────────────────────────────────┐
│ DEPÓSITO                                 │
│ Status: Ativo                            │
│ Aplicar VP: NÃO ✗                        │
│                                          │
│ ☐ Aplicar Valor Presente (VP)            │
│                                          │
│ [Desativar] [Deletar]                    │
└──────────────────────────────────────────┘
```

**Forma INATIVA:**
```
┌──────────────────────────────────────────┐
│ CONSÓRCIO (INATIVO)                      │
│ Status: Inativo                          │
│ Aplicar VP: NÃO ✗                        │
│                                          │
│ (Sem controles editáveis)                │
│                                          │
│ [Deletar]                                │
└──────────────────────────────────────────┘
```

---

## 🚀 Fluxo Completo (Final)

```
UPLOAD CSV
    ↓
[SINCRONIZAR FORMAS]
    ├─ Cria CARTÃO (aplicar_vp=true, taxa=1.5%)
    ├─ Cria CHEQUE (aplicar_vp=true, taxa=2.0%)
    ├─ Cria DEPÓSITO (aplicar_vp=false, taxa=0%)
    └─ Cria FINANCIAMENTO (aplicar_vp=false, taxa=0%)
    ↓
[USUÁRIO ACESSA /formas-recebimento]
    ├─ Vê todas as formas com status VP
    └─ Pode ajustar aplicar_vp e taxa_juros para cada forma
    ↓
[CÁLCULO DE COMISSÃO]
    ├─ Para CARTÃO com VP: usa VP (com 9% desconto)
    ├─ Para CHEQUE com VP: usa VP (com 6.6% desconto)
    ├─ Para DEPÓSITO: usa valor nominal (0% desconto)
    └─ Para FINANCIAMENTO: usa valor nominal (0% desconto)
    ↓
[REGISTRA COMISSÃO]
    └─ Com referência a VP calculado e taxa aplicada
```

---

## 🔍 Testes Recomendados

1. ✅ Checkbox de VP se comporta dinamicamente
2. ✅ Campo de taxa aparece/desaparece com checkbox
3. ✅ Taxa é salva corretamente no banco
4. ✅ Forma inativa não permite editar
5. ⏳ VP é aplicado corretamente ao calcular comissão
6. ⏳ Relatório mostra VP aplicado ou não

---

## 📝 Notas Técnicas

- **Leitura do Banco:** Toda vez que `detectar_taxa_padrao()` é chamado, verifica o banco primeiro
- **Fallback:** Se forma não estiver no banco ou houver erro, usa valores hardcoded
- **Compatibilidade:** Função retorna dict, necessário atualizar chamadas em `resumo_por_cidade()`
- **Armazenamento:** Novo documento mostra como integrar ao cálculo final
