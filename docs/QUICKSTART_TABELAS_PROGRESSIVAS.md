# Guia Rápido: Usar Tabelas Progressivas nas Formas de Recebimento

## 📋 Resumo Executivo

Agora você pode conectar as **Tabelas Progressivas de Impostos** diretamente às **Formas de Recebimento**, através de uma interface web intuitiva com:

- ✅ **Switch Toggle** elegante (estilo Bulma) para ativar/desativar VP
- ✅ **Dropdown Selector** para escolher qual tabela progressiva usar
- ✅ **Taxa Fixa** como fallback quando nenhuma tabela é selecionada
- ✅ **Validação Automática** de compatibilidade entre forma e tabelas

---

## 🚀 Como Usar

### Passo 1: Acessar Gerenciador de Formas

1. Abra o sistema: `http://seu-servidor/formas-recebimento`
2. Você verá lista de todas as formas cadastradas (CARTÃO, CHEQUE, etc)

### Passo 2: Ativar VP com Tabela Progressiva

Para uma forma como "CARTÃO":

1. **Clique no Switch** "Aplicar VP" para ativar
   - O switch ficará **verde** quando ativado
   
2. **Dropdown Automático** aparece com opções:
   ```
   -- Sem tabela progressiva (usar taxa fixa) --
   10x - CARTÃO 10x com 2% ao mês
   6x - CARTÃO 6x com 2% ao mês
   ```

3. **Selecione a Tabela Desejada**
   - Ex: Escolher "10x - CARTÃO 10x com 2% ao mês"
   - Sistema salva automaticamente

### Passo 3: Processar Propostas

Quando você importa uma proposta:
- ✅ Sistema detecta a **forma de recebimento** (ex: CARTÃO)
- ✅ Busca a **tabela progressiva selecionada**
- ✅ Carrega os **coeficientes** (desconto por parcela)
- ✅ Calcula o **Valor Presente com desconto progressivo**
- ✅ Aplica a **comissão correta**

---

## 🎯 Cenários de Uso

### Cenário 1: CARTÃO com Tabela 10x

```
Forma: CARTÃO
VP Ativo? SIM ✓
Tabela: 10x - CARTÃO 10x com 2% ao mês
Taxa Fixa: [oculto - não mostra]

Proposta: R$ 1.000,00 em 10 parcelas
Cálculo: Usa coeficientes progressivos da tabela 10x
Resultado: VP ≈ R$ 898,18 (desconto 10,18%)
```

### Cenário 2: CHEQUE com Taxa Fixa (sem tabela)

```
Forma: CHEQUE
VP Ativo? SIM ✓
Tabela: -- Nenhuma tabela para CHEQUE --
Taxa Fixa: 2.0% [visível e editável]

Proposta: R$ 1.000,00 em 6 parcelas
Cálculo: Usa taxa fixa 2% para todas as parcelas
Resultado: VP com desconto uniforme
```

### Cenário 3: PIX/TRANSFERÊNCIA (VP desativado)

```
Forma: PIX
VP Ativo? NÃO ✗
[Todos os campos ocultos]

Proposta: R$ 1.000,00
Cálculo: Valor nominal (sem VP)
Resultado: R$ 1.000,00
```

---

## 🔧 Troubleshooting

### ❓ "Nenhuma tabela para CARTÃO"

**Problema**: Dropdown vazio mesmo ativando VP

**Solução**:
1. Vá para `/gerenciar-taxas-progressivas`
2. Crie uma tabela com:
   - Forma: CARTÃO (exatamente igual!)
   - Parcelas: 10x (ou outra)
   - Taxa: 2% (exemplo)
3. Volte para `/formas-recebimento` e recarregue (F5)
4. Dropdown agora deve mostrar as tabelas

### ❓ Proposta ainda usa taxa antiga após mudar tabela

**Problema**: Propostas importadas ANTES da mudança não são recalculadas

**Solução**:
- Isto é normal! Propostas são registradas uma única vez.
- **Novo fluxo**: Mude a tabela → importe propostas novas
- Para corrigir antigas: Delete a proposta → re-importe

### ❓ Comissão não mudou quando selecionei tabela

**Problema**: Proposta não usa a nova tabela progressiva

**Verificar**:
1. Proposta tem `Numero Parcelas` preenchido? (obrigatório)
2. Forma tem `tabela_progressiva_id` selecionada? (cheque em F12)
3. Tabela existe no MongoDB?

**Debug no Console (F12)**:
```javascript
// Ver tabelas disponíveis
fetch('/api/taxas-progressivas')
  .then(r => r.json())
  .then(d => console.log(d.dados))

// Ver forma de recebimento
fetch('/api/formas-recebimento')
  .then(r => r.json())
  .then(d => console.log(d.dados.find(f => f.nome === 'CARTÃO')))
```

---

## 📊 Interface em Ação

### Visual do Switch

```
CARTÃO
Status: Ativo

[O----] Aplicar VP    ← Desativado (cinza)

────────────────────────────────

[●----] Aplicar VP    ← Ativado (verde)
        Tabela Progressiva:
        [10x - CARTÃO 10x com 2% ao mês ▼]
```

### Quando Sem Tabela

```
[●----] Aplicar VP
        Tabela Progressiva:
        [-- Sem tabela (usar taxa fixa) --]
        
        Taxa Fixa (%):
        [1.50]
```

---

## 🔍 Como Funciona Internamente

```
1️⃣ Usuário seleciona tabela no dropdown
   └─ HTML: <select onchange="atualizarTabelaProgressiva(...)">

2️⃣ JavaScript faz POST para API
   └─ PUT /api/formas-recebimento/{id}/aplicar-vp
   └─ Body: {tabela_progressiva_id: "65abc123..."}

3️⃣ Servidor atualiza documento MongoDB
   └─ formas_recebimento
   └─ Campo "tabela_progressiva_id" = "65abc123..."

4️⃣ Ao processar proposta
   └─ Busca forma de recebimento (ex: CARTÃO)
   └─ Lê campo "tabela_progressiva_id"
   └─ Carrega coeficientes da tabela
   └─ Calcula VP com desconto progressivo
```

---

## 📈 Prioridade de Cálculo

Quando processo uma proposta, o sistema tenta nesta ordem:

```
1. Tem tabela_progressiva_id selecionada?
   ├─ SIM → Usa coeficientes dessa tabela ✅
   └─ NÃO → próximo

2. Encontra tabela por forma + número de parcelas?
   ├─ SIM → Usa coeficientes encontrados ✅
   └─ NÃO → próximo

3. Forma tem taxa_juros fixa definida?
   ├─ SIM → Usa taxa fixa ✅
   └─ NÃO → próximo

4. Sistema tem taxa padrão para essa forma?
   ├─ SIM → Usa taxa padrão ✅
   └─ NÃO → Usa valor nominal (sem VP)
```

---

## 📝 Checklist de Implementação

- ✅ Modelo `FormaRecebimentoModel` atualizado com `tabela_progressiva_id`
- ✅ Serviço `FormaRecebimentoService` atualizado para persistir campo
- ✅ Rota API `PUT /api/formas-recebimento/{id}/aplicar-vp` recebe novo parâmetro
- ✅ Interface HTML com switch e dropdown funcionando
- ✅ JavaScript carrega tabelas dinamicamente
- ✅ Cálculo de VP usa `tabela_progressiva_id` quando disponível
- ✅ Fallback para taxa fixa quando sem tabela
- ✅ Testes passando (validação de 5 cenários)
- ✅ Documentação completa

---

## 🆘 Suporte

**Encontrou um problema?** Verifique:

1. **Console do Navegador (F12)** → aba "Console"
   - Erros de JavaScript?
   - Requisições falhando?

2. **Logs do Servidor**
   - Erros ao atualizar forma?
   - Erros ao calcular VP?

3. **MongoDB**
   ```javascript
   // Ver formas
   db.formas_recebimento.find({nome: "CARTÃO"}).pretty()
   
   // Ver tabelas
   db.taxas_progressivas.find({forma_recebimento: "CARTÃO"}).pretty()
   ```

---

**🎉 Pronto para usar!**

A integração está **100% funcional** e validada. 

Comece selecionando uma tabela progressiva para sua forma de recebimento principal! 📲

---

*Versão 1.0 - 2024-01-20*
*Sistema de Comissão v2.0*
