# 📋 Resumo: Sistema de Controle de VP por Forma de Recebimento

## 🎯 Objetivo Atingido
Adicionar **checkbox/switch** na tabela de forma de recebimento para **controlar qual forma aplica VP** e com **qual taxa**.

---

## ✅ Implementação Completa

### **1. MODELO (Banco de Dados)**
```python
# app/models/__init__.py - FormaRecebimentoModel

class FormaRecebimentoModel:
    def create(data):
        return {
            'nome': data.get('nome'),
            'status': data.get('status', 'ativo'),
            'aplicar_vp': data.get('aplicar_vp', False),  ✅ NOVO
            'taxa_juros': data.get('taxa_juros', 0.0),   ✅ NOVO
            'data_cadastro': datetime.now(),
            'data_atualizacao': datetime.now()
        }
```

### **2. SERVIÇO (Lógica)**
```python
# app/services/__init__.py - ValorPresenteService.detectar_taxa_padrao()

@staticmethod
def detectar_taxa_padrao(forma_recebimento):
    """
    Lê do BANCO DE DADOS:
    - aplicar_vp: bool (se aplica VP)
    - taxa_juros: float (taxa a usar)
    
    Se não encontrar, usa fallback hardcoded.
    """
    try:
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
    except:
        pass
    
    # FALLBACK
    if 'CARTÃO' in forma_recebimento.upper():
        return {'aplicar_vp': True, 'taxa_juros': 0.015}
    elif 'CHEQUE' in forma_recebimento.upper():
        return {'aplicar_vp': True, 'taxa_juros': 0.020}
    else:
        return {'aplicar_vp': False, 'taxa_juros': 0.0}
```

### **3. ENDPOINT (API)**
```python
# app/routes.py

@api_bp.route('/formas-recebimento/<forma_id>/aplicar-vp', methods=['PUT'])
def atualizar_aplicar_vp(forma_id):
    """
    PUT /api/formas-recebimento/<id>/aplicar-vp
    
    Body:
    {
        "aplicar_vp": true,
        "taxa_juros": 0.015
    }
    """
    dados = request.get_json()
    resultado = FormaRecebimentoService.atualizar_aplicar_vp(
        forma_id,
        dados.get('aplicar_vp'),
        dados.get('taxa_juros')
    )
    return jsonify({'status': 'sucesso', 'dados': resultado})
```

### **4. MÉTODO NO SERVIÇO (Persistência)**
```python
# app/services/__init__.py - FormaRecebimentoService

@staticmethod
def atualizar_aplicar_vp(forma_id, aplicar_vp, taxa_juros=0.0):
    """Atualiza VP e taxa no banco"""
    col = mongo.db.formas_recebimento
    result = col.update_one(
        {'_id': ObjectId(forma_id)},
        {'$set': {
            'aplicar_vp': bool(aplicar_vp),
            'taxa_juros': float(taxa_juros),
            'data_atualizacao': datetime.now()
        }}
    )
    return {'sucesso': result.modified_count > 0, ...}
```

### **5. INTERFACE (HTML + JavaScript)**
```html
<!-- app/templates/formas_recebimento.html -->

<!-- STATUS ATUAL -->
<div>
    Aplicar VP: <strong>${forma.aplicar_vp ? 'SIM ✓' : 'NÃO ✗'}</strong>
</div>
${forma.aplicar_vp ? `<div>Taxa: <strong>${taxaFormatada}%</strong></div>` : ''}

<!-- CHECKBOX -->
<label class="checkbox">
    <input type="checkbox" id="vp-${forma._id}" 
           ${forma.aplicar_vp ? 'checked' : ''}
           onchange="atualizarAplicarVP('${forma._id}', this.checked)">
    <span>Aplicar Valor Presente (VP)</span>
</label>

<!-- CAMPO DE TAXA (só aparece se VP ativo) -->
${forma.aplicar_vp ? `
<div class="field">
    <label class="label is-size-7">Taxa de Juros Mensal (%)</label>
    <input class="input is-small" type="number" id="taxa-${forma._id}"
           value="${taxaFormatada}" step="0.01"
           onchange="atualizarTaxaJuros('${forma._id}', this.value)">
</div>
` : ''}

<!-- JAVASCRIPT -->
<script>
function atualizarAplicarVP(formaId, aplicarVP) {
    let taxa = 0.0;
    
    // Atribui taxa padrão conforme tipo de forma
    if (aplicarVP) {
        const forma = formas.find(f => f._id === formaId);
        if (forma) {
            if (forma.nome.toUpperCase().includes('CARTÃO')) {
                taxa = 1.5;
            } else if (forma.nome.toUpperCase().includes('CHEQUE')) {
                taxa = 2.0;
            }
        }
    }
    
    fetch(`/api/formas-recebimento/${formaId}/aplicar-vp`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            aplicar_vp: aplicarVP,
            taxa_juros: taxa / 100
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'sucesso') {
            carregarFormas();  // Recarrega lista
        }
    });
}

function atualizarTaxaJuros(formaId, taxaPercentual) {
    const taxa = parseFloat(taxaPercentual) / 100;
    
    fetch(`/api/formas-recebimento/${formaId}/aplicar-vp`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            aplicar_vp: true,
            taxa_juros: taxa
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Taxa atualizada');
    });
}
</script>
```

---

## 🎨 Como Fica na Interface

### **ANTES**
```
┌─────────────────────────────────┐
│ CARTÃO                          │
│ Status: Ativo                   │
│                                 │
│ [Desativar] [Deletar]           │
└─────────────────────────────────┘
```

### **DEPOIS**
```
┌─────────────────────────────────┐
│ CARTÃO                          │
│ Status: Ativo                   │
│ Aplicar VP: SIM ✓               │
│ Taxa de Juros: 1.50% ao mês     │
│                                 │
│ ☑ Aplicar Valor Presente (VP)   │
│                                 │
│ Taxa de Juros Mensal (%)        │
│ [1.50                        ]  │
│                                 │
│ [Desativar] [Deletar]           │
└─────────────────────────────────┘
```

---

## 🔄 Fluxo de Uso

1. **Usuário acessa** `/formas-recebimento`
2. **Vê lista de formas** com status de VP
3. **Clica checkbox** para ativar/desativar VP
4. **Sistema auto-salva** (sem botão confirmar)
5. **Campo de taxa** aparece/desaparece dinamicamente
6. **Usuário ajusta taxa** (ex: 1.5% para CARTÃO)
7. **Sistema salva** ao sair do campo
8. **Próxima vez que processar comissões**, usa esses valores!

---

## 📊 Exemplo de Uso Real

**Cenário:** Você quer alterar CARTÃO para aplicar 2.0% ao mês em vez de 1.5%

```
Antes:
  CARTÃO
  ☐ Aplicar VP (taxa 1.5% hardcoded)

Depois:
  CARTÃO
  ☑ Aplicar VP
  Taxa: [2.0]  ← Você altera para 2.0

Resultado:
  VP será calculado com 2.0% ao mês
  Comissões maiores (menos desconto)
```

---

## ✅ Checklist

### **Backend**
- ✅ Modelo atualizado com `aplicar_vp` e `taxa_juros`
- ✅ `detectar_taxa_padrao()` lê do banco
- ✅ Endpoint `PUT /api/formas-recebimento/<id>/aplicar-vp` criado
- ✅ `FormaRecebimentoService.atualizar_aplicar_vp()` implementado
- ✅ Sintaxe Python validada

### **Frontend**
- ✅ Checkbox para ativar/desativar VP
- ✅ Campo de taxa (aparece só se VP ativo)
- ✅ JavaScript para atualizar dinamicamente
- ✅ Exibe status (SIM ✓ ou NÃO ✗)
- ✅ Salva automaticamente ao alterar

### **Integração**
- ⏳ Atualizar `resumo_por_cidade()` para usar novo retorno de `detectar_taxa_padrao()`
- ⏳ Integrar VP no cálculo de comissões
- ⏳ Testar fluxo completo

---

## 🚀 Próximo Passo

Atualizar a função `resumo_por_cidade()` para:

```python
# Passo 4: Calcular comissão COM OU SEM VP

taxa_info = ValorPresenteService.detectar_taxa_padrao(forma_recebimento)
# Retorna: {'aplicar_vp': bool, 'taxa_juros': float}

if taxa_info['aplicar_vp']:
    # Calcular VP
    vp = ValorPresenteService.calcular_valor_presente(...)
    valor_base = vp  # Usar VP na comissão
else:
    # Usar valor nominal
    valor_base = valor

comissao = valor_base * aliquota
```

Quer que eu faça essa integração agora? 🚀
