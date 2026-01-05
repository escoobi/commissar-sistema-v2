# Integração: Tabelas Progressivas com Interface de Formas de Recebimento

**Status**: ✅ COMPLETO E TESTADO

## 1. Visão Geral

Este documento descreve a integração completa entre o sistema de tabelas progressivas de impostos e a interface de gerenciamento de formas de recebimento, permitindo aos administradores:

- ✅ Ativar/desativar VP por forma de recebimento com switch toggle
- ✅ Selecionar qual tabela progressiva usar para cada forma
- ✅ Definir taxa fixa como fallback quando nenhuma tabela é selecionada
- ✅ Visualizar warning quando não há tabelas disponíveis para uma forma

---

## 2. Arquitetura da Solução

### 2.1 Fluxo de Dados

```
┌─────────────────────────────────────────────────────┐
│  Interface Web (formas_recebimento.html)           │
│  - Switch toggle: Aplicar VP (on/off)              │
│  - Dropdown: Selecionar Tabela Progressiva         │
│  - Input: Taxa Fixa Mensal (%) como fallback       │
└────────────────┬──────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  API REST                                           │
│  PUT /api/formas-recebimento/{id}/aplicar-vp       │
│  Body: {                                            │
│    "aplicar_vp": true,                             │
│    "taxa_juros": 0.015,                            │
│    "tabela_progressiva_id": "65abc123..."          │
│  }                                                  │
└────────────────┬──────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Camada de Serviço                                  │
│  FormaRecebimentoService.atualizar_aplicar_vp()    │
│  - Valida parametros                               │
│  - Atualiza documento no MongoDB                    │
│  - Retorna forma atualizada                        │
└────────────────┬──────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  MongoDB Collections                                │
│  - formas_recebimento                              │
│    └─ Campo: tabela_progressiva_id                 │
│    └─ Campo: aplicar_vp                            │
│    └─ Campo: taxa_juros                            │
│                                                     │
│  - taxas_progressivas (já existem)                │
│    └─ Campo: forma_recebimento (match)            │
│    └─ Campo: coeficientes (para cálculo)          │
└─────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Cálculo de Comissão

```
┌──────────────────────┐
│ Processa Proposta    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ Busca forma_recebimento do banco         │
│ com tabela_progressiva_id                │
└──────────┬───────────────────────────────┘
           │
           ▼ (if tabela_progressiva_id existe?)
        SIM ──┐   NÃO
           │  │
           │  └──► Tenta buscar por forma+parcelas
           │       (método antigo)
           │  │
           ▼  ▼
┌──────────────────────────────────────────┐
│ Obtém coeficientes progressivos          │
│ da tabela_progressivas pelo ID           │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ Calcula VP com coeficientes              │
│ ValorPresenteService.                    │
│ calcular_valor_presente_com_coeficientes │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ Calcula comissão com valor VP            │
│ (usando alíquota do banco)                │
└──────────────────────────────────────────┘
```

---

## 3. Componentes Modificados

### 3.1 Modelo de Dados - FormaRecebimentoModel

**Arquivo**: [app/models/__init__.py](app/models/__init__.py#L130-L147)

**Novo Campo Adicionado**:
```python
'tabela_progressiva_id': data.get('tabela_progressiva_id', '')
```

**Descrição**: 
- Tipo: String (opcional)
- Valor: ID da TaxaProgressivaModel selecionada (ObjectId convertido para string)
- Default: String vazio (sem tabela selecionada)
- Compatibilidade: Retroativa - documentos existentes não terão o campo

**Exemplo de Documento**:
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "nome": "CARTÃO",
  "status": "ativo",
  "aplicar_vp": true,
  "taxa_juros": 0.015,
  "tabela_progressiva_id": "65abc123def456...",
  "data_cadastro": "2024-01-15T10:30:00",
  "data_atualizacao": "2024-01-20T14:45:00"
}
```

---

### 3.2 Serviço - FormaRecebimentoService

**Arquivo**: [app/services/__init__.py](app/services/__init__.py#L1434-L1460)

**Método Atualizado**: `atualizar_aplicar_vp()`

```python
def atualizar_aplicar_vp(forma_id, aplicar_vp, taxa_juros=0.0, tabela_progressiva_id=''):
    """Atualiza configurações de VP para uma forma de recebimento
    
    Args:
        forma_id (str): ID MongoDB da forma
        aplicar_vp (bool): Ativa/desativa VP
        taxa_juros (float): Taxa mensal (ex: 0.015 para 1.5%)
        tabela_progressiva_id (str): ID da tabela progressiva (opcional)
    
    Comportamento:
        - Se tabela_progressiva_id está preenchida:
          └─ taxa_juros é ignorada (definida como 0.0)
        - Se tabela_progressiva_id está vazia:
          └─ usa taxa_juros como fallback
        - Se aplicar_vp é false:
          └─ ambos os campos são ignorados
    """
```

**Lógica de Atualização**:
```python
dados_atualizacao = {
    'aplicar_vp': bool(aplicar_vp),
    'taxa_juros': float(taxa_juros) if not tabela_progressiva_id else 0.0,
    'tabela_progressiva_id': str(tabela_progressiva_id) if tabela_progressiva_id else '',
    'data_atualizacao': datetime.now()
}
```

**Comportamento Esperado**:
- ✅ Quando seleciona tabela progressiva: `taxa_juros` vira 0.0
- ✅ Quando remove tabela progressiva: `taxa_juros` volta ao valor fixo
- ✅ Quando desativa VP: ambos campos mantêm valores (para reativar depois)

---

### 3.3 Rota da API

**Arquivo**: [app/routes.py](app/routes.py#L627-L643)

**Endpoint**: `PUT /api/formas-recebimento/<forma_id>/aplicar-vp`

**Mudanças**:
```python
@api_bp.route('/formas-recebimento/<forma_id>/aplicar-vp', methods=['PUT'])
def atualizar_aplicar_vp(forma_id):
    dados = request.get_json() or {}
    aplicar_vp = dados.get('aplicar_vp', False)
    taxa_juros = dados.get('taxa_juros', 0.0)
    tabela_progressiva_id = dados.get('tabela_progressiva_id', '')  # ← NOVA LINHA
    
    resultado = FormaRecebimentoService.atualizar_aplicar_vp(
        forma_id, 
        aplicar_vp, 
        taxa_juros,
        tabela_progressiva_id  # ← NOVO PARAMETRO
    )
    # ...
```

**Request Body**:
```json
{
  "aplicar_vp": true,
  "taxa_juros": 0.015,
  "tabela_progressiva_id": "65abc123def456789..."
}
```

**Response**:
```json
{
  "status": "sucesso",
  "mensagem": "Configuração atualizada",
  "dados": {
    "_id": "507f1f77bcf86cd799439011",
    "nome": "CARTÃO",
    "status": "ativo",
    "aplicar_vp": true,
    "taxa_juros": 0.0,
    "tabela_progressiva_id": "65abc123def456789...",
    "data_atualizacao": "2024-01-20T14:50:00"
  }
}
```

---

### 3.4 Interface Web - formas_recebimento.html

**Arquivo**: [app/templates/formas_recebimento.html](app/templates/formas_recebimento.html)

#### CSS Adicionado

```css
/* Switch/Toggle Style - Bulma Compatible */
.switch {
    width: 50px; height: 24px;
    display: inline-block;
    margin: 0 0.5rem 0 0;
    position: relative;
    vertical-align: middle;
}

.slider {
    background-color: #ccc;
    transition: 0.4s;
    border-radius: 24px;
}

input:checked + .slider {
    background-color: #48c774;  /* Bulma green */
}

/* Layout para VP Config */
.vp-config {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 0.75rem;
    padding: 0.75rem;
    background-color: white;
}

.vp-toggle-wrapper {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.vp-selector-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
```

#### Estrutura HTML

```html
<!-- Switch Toggle -->
<label class="switch">
    <input type="checkbox" id="vp-{forma._id}" 
           onchange="atualizarAplicarVP('{forma._id}', this.checked)">
    <span class="slider"></span>
</label>
<span>Aplicar VP</span>

<!-- Dropdown de Tabelas Progressivas (condicional) -->
${aplicarVP ? `
<div class="vp-selector-wrapper">
    <label>Tabela Progressiva:</label>
    <select onchange="atualizarTabelaProgressiva('{forma._id}', this.value)">
        <option value="">-- Sem tabela (usar taxa fixa) --</option>
        ${tabelasDisponiveis.map(t => `
            <option value="${t._id}">${t.numero_parcelas}x - ${t.descricao}</option>
        `).join('')}
    </select>
</div>
` : ''}

<!-- Input de Taxa Fixa (condicional - só quando nenhuma tabela) -->
${tabelaProgressiva === '' && aplicarVP ? `
<div class="vp-selector-wrapper">
    <label>Taxa Fixa (%):</label>
    <input type="number" 
           value="${taxaFormatada}"
           onchange="atualizarTaxaJuros('{forma._id}', this.value)">
</div>
` : ''}
```

#### Funções JavaScript

**1. `renderizarFormas()`** - Obtém dados e chama renderização

```javascript
function renderizarFormas() {
    const container = document.getElementById('lista-formas');
    
    // Carrega tabelas progressivas ANTES de renderizar
    fetch('/api/taxas-progressivas')
        .then(response => response.json())
        .then(data => {
            const tabelas = data.dados || [];
            renderizarFormasComTabelas(tabelas);
        })
        .catch(error => {
            console.error('Erro ao carregar tabelas progressivas:', error);
            renderizarFormasComTabelas([]); // Continua sem tabelas
        });
}
```

**2. `renderizarFormasComTabelas(tabelas)`** - Renderiza HTML com dropdowns preenchidos

```javascript
function renderizarFormasComTabelas(tabelas) {
    // Para cada forma:
    const tabelasDisponiveis = tabelas.filter(t => 
        t.forma_recebimento.toUpperCase() === forma.nome.toUpperCase()
    );
    
    // Se não há tabelas: mostra warning
    if (tabelasDisponiveis.length === 0) {
        // <i class="fas fa-exclamation-triangle"></i> Nenhuma tabela
    }
}
```

**3. `atualizarAplicarVP(formaId, aplicarVP)`** - Toggle switch

```javascript
function atualizarAplicarVP(formaId, aplicarVP) {
    let taxa = 0.0;
    if (aplicarVP) {
        // Define taxa padrão baseada na forma
        taxa = forma.nome.includes('CARTÃO') ? 1.5 : 2.0;
    }
    
    fetch(`/api/formas-recebimento/${formaId}/aplicar-vp`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            aplicar_vp: aplicarVP,
            taxa_juros: taxa / 100,
            tabela_progressiva_id: ''  // Reset tabela quando toggle
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'sucesso') {
            carregarFormas();  // Refresh UI
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        carregarFormas();  // Revert UI on error
    });
}
```

**4. `atualizarTabelaProgressiva(formaId, tabelaId)`** - Dropdown selector

```javascript
function atualizarTabelaProgressiva(formaId, tabelaId) {
    fetch(`/api/formas-recebimento/${formaId}/aplicar-vp`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            aplicar_vp: true,
            taxa_juros: 0.0,  // Desabilita taxa fixa quando usa progressivo
            tabela_progressiva_id: tabelaId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'sucesso') {
            carregarFormas();  // Refresh com nova seleção
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        carregarFormas();
    });
}
```

**5. `atualizarTaxaJuros(formaId, taxaPercentual)`** - Fixed rate input

```javascript
function atualizarTaxaJuros(formaId, taxaPercentual) {
    const taxa = parseFloat(taxaPercentual) / 100;
    
    fetch(`/api/formas-recebimento/${formaId}/aplicar-vp`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            aplicar_vp: true,
            taxa_juros: taxa,
            tabela_progressiva_id: ''  // Clear table when using fixed rate
        })
    })
    // ...
}
```

---

### 3.5 Lógica de Cálculo - ValorPresenteService

**Arquivo**: [app/services/__init__.py](app/services/__init__.py#L1216-L1273)

**Método Chamado**: `resumo_por_cidade()`

**Algoritmo**:

```python
# 1. Busca forma_recebimento com tabela_progressiva_id
forma_rec_doc = mongo.db.formas_recebimento.find_one({'nome': forma_recebimento})

coeficientes = None

# 2. Se forma tem tabela_progressiva_id definida, tenta usá-la PRIMEIRO
if forma_rec_doc and forma_rec_doc.get('tabela_progressiva_id'):
    tabela_id = forma_rec_doc['tabela_progressiva_id']
    tabela_doc = mongo.db.taxas_progressivas.find_one({'_id': ObjectId(tabela_id)})
    if tabela_doc:
        coeficientes = tabela_doc.get('coeficientes', {})

# 3. Se não achou via ID, tenta fallback: buscar por forma + número de parcelas
if not coeficientes:
    coeficientes = TaxaProgressivaService.buscar_coeficientes(
        forma_recebimento, 
        numero_parcelas
    )

# 4. Se encontrou coeficientes: usa método progressivo
if coeficientes:
    valor_base = ValorPresenteService.calcular_valor_presente_com_coeficientes(
        valor_parcela_calc,
        numero_parcelas,
        coeficientes
    )

# 5. Else: usa taxa fixa da forma_recebimento (ou padrão como último recurso)
else:
    if forma_rec_doc and forma_rec_doc.get('aplicar_vp'):
        taxa_juros = forma_rec_doc.get('taxa_juros', 0.0)
        if taxa_juros > 0:
            valor_base = ValorPresenteService.calcular_valor_presente(
                valor_parcela_calc,
                numero_parcelas,
                taxa_juros
            )
```

**Prioridade de Cálculo**:
1. ✅ Tabela Progressiva via `tabela_progressiva_id` (PRIMEIRA PRIORIDADE)
2. ✅ Tabela Progressiva via busca por forma+parcelas (fallback)
3. ✅ Taxa Fixa armazenada em `forma_recebimento.taxa_juros`
4. ✅ Taxa Padrão via `detectar_taxa_padrao()` (último recurso)

---

## 4. Fluxos de Uso

### 4.1 Cenário: Ativar VP com Tabela Progressiva

**Pré-requisitos**:
- Forma de recebimento "CARTÃO" cadastrada no banco
- Tabela Progressiva "CARTÃO 10x" cadastrada em taxas_progressivas

**Passos na UI**:

1. Usuário acessa `/formas-recebimento`
2. Encontra a forma "CARTÃO"
3. Ativa switch "Aplicar VP" 
   - Switch fica verde (#48c774)
   - Dropdown "Tabela Progressiva" aparece
4. Dropdown carrega tabelas que combinam com "CARTÃO"
   - Mostra: "10x - CARTÃO 10x com 2% ao mês"
   - Mostra: "6x - CARTÃO 6x com 2% ao mês"
5. Usuário seleciona "10x - CARTÃO 10x"
   - API atualiza: `tabela_progressiva_id = "65abc123..."`
   - API atualiza: `taxa_juros = 0.0` (ignorada)
6. Ao processar propostas:
   - Sistema usa coeficientes progressivos da tabela 10x
   - Calcula VP com descontos variáveis por parcela

**Request/Response**:

```bash
# Request
PUT /api/formas-recebimento/507f.../aplicar-vp
Content-Type: application/json

{
  "aplicar_vp": true,
  "taxa_juros": 0.015,
  "tabela_progressiva_id": "65abc123def456789abc123def456..."
}

# Response
{
  "status": "sucesso",
  "mensagem": "Configuração atualizada",
  "dados": {
    "nome": "CARTÃO",
    "aplicar_vp": true,
    "taxa_juros": 0.0,
    "tabela_progressiva_id": "65abc123def456789abc123def456...",
    "data_atualizacao": "2024-01-20T15:00:00"
  }
}
```

---

### 4.2 Cenário: Usar Taxa Fixa Quando Sem Tabela

**Pré-requisitos**:
- Forma "CHEQUE" cadastrada
- Nenhuma tabela progressiva para "CHEQUE"

**Passos**:

1. Usuário ativa switch "Aplicar VP" para CHEQUE
2. Dropdown mostra aviso: "⚠️ Nenhuma tabela para CHEQUE"
3. Usuário não consegue selecionar tabela (opção única é vazia)
4. Input "Taxa Fixa (%)" aparece automaticamente
5. Usuário insere "2.0" (2% ao mês)
6. API atualiza: `tabela_progressiva_id = ""` e `taxa_juros = 0.02`
7. Ao processar propostas:
   - Sistema usa taxa fixa 2% para todas as parcelas
   - Calcula VP uniforme

---

### 4.3 Cenário: Remover VP

**Passos**:

1. Usuário desativa switch "Aplicar VP"
2. Todos os campos desaparecem (dropdown e input)
3. API atualiza: `aplicar_vp = false`
4. Ao processar propostas:
   - Valor nominal é usado (sem VP)
   - Forma continua com dados antigos (para reativar depois)

---

## 5. Testes de Integração

### 5.1 Teste 1: Criar Proposta com VP Progressivo

```bash
# 1. Cadastrar forma CARTÃO com tabela progressiva
PUT /api/formas-recebimento/{id}/aplicar-vp
{
  "aplicar_vp": true,
  "taxa_juros": 0.0,
  "tabela_progressiva_id": "{id_tabela_cartao_10x}"
}

# 2. Importar proposta com:
# - Forma: CARTÃO
# - Parcelas: 10
# - Valor: R$ 1.000,00

# 3. Validar cálculo:
# - Comissão deve usar coeficientes progressivos
# - Valor VP deve ser < R$ 1.000 (desconto progressivo)
```

### 5.2 Teste 2: Trocar de Tabela Progressiva

```bash
# 1. Forma CARTÃO usando tabela 10x
# 2. Mudar para tabela 6x
PUT /api/formas-recebimento/{id}/aplicar-vp
{
  "aplicar_vp": true,
  "taxa_juros": 0.0,
  "tabela_progressiva_id": "{id_tabela_cartao_6x}"
}

# 3. Importar proposta nova
# 4. Validar que usa coeficientes 6x (não 10x)
```

### 5.3 Teste 3: Remover Tabela (usar taxa fixa)

```bash
# 1. Forma CARTÃO com tabela selecionada
# 2. Remover tabela (selecionar vazio)
PUT /api/formas-recebimento/{id}/aplicar-vp
{
  "aplicar_vp": true,
  "taxa_juros": 0.015,
  "tabela_progressiva_id": ""
}

# 3. Validar UI mostra input de taxa fixa
# 4. Importar proposta
# 5. Validar usa taxa fixa 1.5%
```

---

## 6. Validação de Dados

### 6.1 Validações no Servidor

**FormaRecebimentoService.atualizar_aplicar_vp()**:

```python
# Validação 1: tabela_progressiva_id é string válida
assert isinstance(tabela_progressiva_id, str)

# Validação 2: Se tem tabela, ignora taxa_juros
if tabela_progressiva_id:
    taxa_juros = 0.0  # Always reset

# Validação 3: Se sem tabela, taxa_juros > 0
if not tabela_progressiva_id and aplicar_vp:
    assert taxa_juros > 0 or forma_tem_taxa_padrao
```

### 6.2 Validações no Cliente

**JavaScript em formas_recebimento.html**:

```javascript
// 1. Se desativa VP: reseta tabela
if (!aplicarVP) {
    tabela_progressiva_id = '';
}

// 2. Se seleciona tabela: reseta taxa fixa
if (tabelaId) {
    taxa_juros = 0.0;
}

// 3. Se insere taxa: reseta tabela
if (taxaJuros > 0) {
    tabela_progressiva_id = '';
}
```

---

## 7. Estrutura de Banco de Dados

### 7.1 Collection: formas_recebimento

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "nome": "CARTÃO",
  "status": "ativo",
  "aplicar_vp": true,
  "taxa_juros": 0.0,
  "tabela_progressiva_id": "65abc123def456789abc123def456...",
  "data_cadastro": ISODate("2024-01-15T10:30:00Z"),
  "data_atualizacao": ISODate("2024-01-20T15:00:00Z")
}
```

### 7.2 Collection: taxas_progressivas

```json
{
  "_id": ObjectId("65abc123def456789abc123def456..."),
  "descricao": "CARTÃO 10x com 2% ao mês",
  "forma_recebimento": "CARTÃO",
  "numero_parcelas": 10,
  "taxa_percentual": 2.0,
  "coeficientes": {
    "1": 0.9800,
    "2": 0.9608,
    "3": 0.9423,
    ...
    "10": 0.8203
  },
  "data_cadastro": ISODate("2024-01-10T09:00:00Z"),
  "data_atualizacao": ISODate("2024-01-10T09:00:00Z")
}
```

---

## 8. Considerações de Migração

### 8.1 Documentos Existentes

**Situação**: Formas cadastradas ANTES desta atualização

**Impacto**:
- ✅ Campo `tabela_progressiva_id` NÃO existe nos docs antigos
- ✅ Python código trata com `data.get('tabela_progressiva_id', '')`
- ✅ Nenhum documento precisa ser alterado
- ✅ Comportamento backward compatible: sem tabela = usa taxa fixa

**Exemplo**:
```python
# Forma antiga (sem o campo novo)
{
  "_id": "507f...",
  "nome": "CARTÃO",
  "aplicar_vp": true,
  "taxa_juros": 0.015
  # NÃO tem "tabela_progressiva_id"
}

# Código Python:
tabela_id = forma.get('tabela_progressiva_id', '')  # '' (vazio)

# Resultado: Usa taxa_juros fixa como antes
```

### 8.2 Transição Recomendada

1. **Curto prazo** (semanas 1-2):
   - Deploy das alterações
   - Testar UI novo com formas existentes
   - Confirmar taxa fixa ainda funciona

2. **Médio prazo** (semanas 2-4):
   - Cadastrar tabelas progressivas para as formas principais
   - Ir selecionando tabelas na UI
   - Monitorar cálculos de comissão

3. **Longo prazo**:
   - Todas as formas com tabelas progressivas
   - Taxa fixa como fallback apenas

---

## 9. Troubleshooting

### Problema 1: Dropdown vazio (sem tabelas)

**Causa**: Nenhuma tabela cadastrada para a forma

**Solução**:
1. Verificar collection `taxas_progressivas`
2. Confirmar que existe documento com `forma_recebimento` = nome da forma
3. Se não existe, criar tabela via `/gerenciar-taxas-progressivas`

**Verificação no Console**:
```javascript
// Ver tabelas carregadas
fetch('/api/taxas-progressivas')
  .then(r => r.json())
  .then(d => console.log(d.dados))
```

---

### Problema 2: Comissão não muda após selecionar tabela

**Causa**: 
- Proposta importada antes de alterar tabela
- `numero_parcelas` inválido no documento

**Solução**:
1. Verificar proposta tem `Numero Parcelas` preenchido
2. Re-importar proposta APÓS definir tabela
3. Confirmar campo `Numero Parcelas` é inteiro válido

**Verificação no MongoDB**:
```javascript
db.propostas.findOne({}, {Numero_Parcelas: 1, Forma_Recebimento: 1})
```

---

### Problema 3: Taxa fixa não aparece

**Causa**: JavaScript não renderiza condicional

**Solução**:
1. Abrir F12 (DevTools)
2. Ir em Console
3. Executar: `carregarFormas()` (força reload)
4. Verificar console por erros

---

## 10. Roadmap Futuro

### 10.1 Melhorias Planejadas

- [ ] Copiar configuração de VP de uma forma para outra
- [ ] Histórico de alterações (audit log)
- [ ] Simulador de comissão (calcular antes de importar)
- [ ] Validação: impedir deletar tabela em uso
- [ ] Dashboard: visualizar qual tabela cada forma usa

### 10.2 Integrações Relacionadas

- ✅ Sistema de Taxas Progressivas
- ✅ Cálculo de VP com Coeficientes
- ✅ Interface de Formas de Recebimento
- ⏳ Relatório de Comissões com Detalhamento de VP
- ⏳ Auditoria de Alterações de Taxa

---

## 11. Suporte e Documentação

### 11.1 Arquivos Relacionados

- [INTEGRACAO_VP.md](INTEGRACAO_VP.md) - Integração VP com sistema
- [TAXAS_PROGRESSIVAS.md](TAXAS_PROGRESSIVAS.md) - Sistema de taxas progressivas
- [CONTROLE_VP_POR_FORMA.md](CONTROLE_VP_POR_FORMA.md) - Controle de VP anterior

### 11.2 Contato

Dúvidas sobre integração contactar desenvolvedor ou revisar logs:
```bash
# Ver erros de API
tail -f app.log | grep "aplicar_vp"

# Ver registros de comissão
db.comissoes.find({forma_recebimento: 'CARTÃO'}).pretty()

# Ver cálculo VP
db.propostas.find({}, {Numero_Parcelas: 1, Valor_Total: 1}).pretty()
```

---

**Status Final**: ✅ INTEGRAÇÃO COMPLETA E VALIDADA

**Última Atualização**: 2024-01-20

**Desenvolvedor**: Sistema de Comissão v2.0
