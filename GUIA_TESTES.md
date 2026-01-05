# 🧪 Guia de Testes - Sistema de Comissão 2.0

**Data:** Janeiro 5, 2026  
**Versão:** 2.0

---

## 📋 Índice

1. [Testes Manuais](#testes-manuais)
2. [Casos de Teste](#casos-de-teste)
3. [Dados de Teste](#dados-de-teste)
4. [Verificação de Resultados](#verificação-de-resultados)

---

## 🧪 Testes Manuais

### 1. Teste de Upload de Saída

**Objetivo:** Validar se o sistema processa corretamente o arquivo de saída (tabela de motos)

**Passos:**
1. Abra http://localhost:5000/
2. Clique em "Upload Saída"
3. Selecione arquivo CSV com dados de vendedores
4. Clique "Processar"

**Resultado Esperado:**
- ✅ Arquivo enviado com sucesso
- ✅ Vendedores cadastrados no banco
- ✅ Motos registradas
- ✅ Valores de tabela salvos

---

### 2. Teste de Upload de Propostas

**Objetivo:** Validar processamento correto de propostas (vendas)

**Passos:**
1. Vá para http://localhost:5000/
2. Clique em "Upload Proposta"
3. Selecione arquivo CSV com propostas
4. Clique "Processar"

**Resultado Esperado:**
- ✅ Propostas enviadas com sucesso
- ✅ Relacionadas aos vendedores corretos
- ✅ Formas de pagamento ativadas
- ✅ Propostas aparecem em relatórios

---

### 3. Teste de Cálculo HP12C

**Objetivo:** Validar aplicação correta da fórmula HP12C inversa

**Dados de Teste:**
```
Venda:        R$ 11.126,80
Parcelas:     10
Taxa:         1,59% a.m.
Valor Esperado (VP): R$ 10.212,59
```

**Verificação:**
1. Faça upload de uma proposta com estes dados
2. Vá para Relatórios > Detalhes do Vendedor
3. Procure pela proposta
4. Verifique campo "Valor da Venda" = R$ 10.212,59

---

### 4. Teste de Agrupamento por Pedido + Doc Fiscal

**Objetivo:** Validar que propostas com mesmo Nº Pedido mas notas diferentes são agrupadas separadamente

**Dados de Teste:**
```
Proposta 1:  Pedido 27421, NF-E 407979/1, CARTÃO, R$ 11.126,80
Proposta 2:  Pedido 27421, NF-E 407979/2, DEPÓSITO, R$ 12.250,00
(Mesmo pedido, notas diferentes)
```

**Verificação:**
1. Upload de duas propostas
2. Relatório > Detalhes do Vendedor
3. Devem aparecer como **2 vendas separadas**
4. Comissões calculadas independentemente

---

### 5. Teste de Meta % sobre VP

**Objetivo:** Validar cálculo correto de Meta %

**Dados de Teste:**
```
Venda 1 (CARTÃO):   R$ 10.212,59 VP (de R$ 11.126,80)
Venda 2 (DEPÓSITO): R$ 12.250,00 (à vista)
Total VP:           R$ 22.462,59
Valor Tabela:       R$ 22.300,00

Meta % Esperada: (22.462,59 / 22.300,00) × 100 = 100,73%
```

**Verificação:**
1. Upload de propostas
2. Relatório > Detalhes
3. Campo "Meta %" deve ser ≈ 100,73%

---

### 6. Teste de Distribuição Proporcional de Comissão

**Objetivo:** Validar que comissão é distribuída proporcionalmente entre formas

**Dados de Teste:**
```
Total VP:       R$ 22.462,59
Alíquota:       2,0%
Total Comissão: R$ 449,25 (calculado)

Distribuição esperada:
  CARTÃO:   (10.212,59 / 22.462,59) × 449,25 = R$ 204,25
  DEPÓSITO: (12.250,00 / 22.462,59) × 449,25 = R$ 245,00
```

**Verificação:**
1. Relatório > Detalhes do Vendedor
2. Verificar comissão de cada forma
3. Soma deve ser ≈ R$ 449,25

---

## 🎯 Casos de Teste

### Caso 1: Venda Simples (Sem Juros)

**Entrada:**
```
Pedido:       27421
Forma:        DEPÓSITO
Valor:        R$ 12.250,00
Parcelas:     1
Taxa:         0%
Valor Tabela: R$ 12.250,00
```

**Esperado:**
```
VP:       R$ 12.250,00 (sem aplicação de taxa)
Meta %:   100,0%
Comissão: Conforme alíquota para 100%
```

---

### Caso 2: Venda Parcelada com Juros

**Entrada:**
```
Pedido:       27421
Forma:        CARTÃO
Valor:        R$ 11.126,80
Parcelas:     10
Taxa:         1,59% a.m.
Valor Tabela: R$ 10.212,59
```

**Esperado:**
```
VP:       R$ 10.212,59 (aplicado HP12C)
Meta %:   100,0%
Comissão: Conforme alíquota para 100%
```

---

### Caso 3: Múltiplas Formas (Mesmo Pedido)

**Entrada:**
```
Forma 1:  CARTÃO + DEPÓSITO = R$ 11.126,80 + R$ 12.250,00
Valor:    R$ 23.376,80
Valor T:  R$ 22.300,00
```

**Esperado:**
```
VP Total: R$ 10.212,59 + R$ 12.250,00 = R$ 22.462,59
Meta %:   100,73%
Comissão: Única, distribuída proporcionalmente
```

---

### Caso 4: Pedido com Ajuste (Valor Zero)

**Entrada:**
```
Pedido:    27462
Forma 1:   A PAGAR    -R$ 968,61
Forma 2:   A RECEBER  +R$ 968,61
Total:     R$ 0,00
```

**Esperado:**
```
VP:       R$ 0,00
Meta %:   0%
Comissão: R$ 0,00 (sem comissão)
Aparece no relatório: SIM (com comissão zero)
```

---

### Caso 5: Vendedor Interno vs Externo

**Entrada:**
```
Vendedor 1: PAULO (interno)
Vendedor 2: JOÃO (externo)
Mesmo Meta %: 100%
```

**Esperado:**
```
Comissão PAULO: Conforme tabela "interno"
Comissão JOÃO:  Conforme tabela "externo"
(Alíquotas diferentes)
```

---

### Caso 6: Moto Alta CC vs Baixa CC

**Entrada:**
```
Moto 1: CG 160 (Baixa CC) - Meta 100%
Moto 2: CB 500 (Alta CC)  - Meta 100%
```

**Esperado:**
```
Comissão CG:  Conforme tabela "Baixa CC"
Comissão CB:  Conforme tabela "Alta CC"
(Alíquotas podem ser diferentes)
```

---

## 📊 Dados de Teste

### Arquivo CSV: saida.csv

```csv
Vendedor;Pessoa;Pedido;Doc Fiscal;Modelo;Valor Tabela
PAULO BRAIDO;JOAO SILVA;27421;NF-E 407979/1;CG 160;22300
PAULO BRAIDO;MARIA SANTOS;27422;NF-E 407980/1;CB 500;35000
BRUNA SANTOS;CARLOS COSTA;27423;NF-E 407981/1;CG 160;21500
```

### Arquivo CSV: propostas.csv

```csv
Nº Pedido;Doc Fiscal;Pessoa;Modelo;Forma Recebimento;Nº Parcela;Valor Total
27421;NF-E 407979/1;JOAO SILVA;CG 160;CARTÃO;10;11126.80
27421;NF-E 407979/1;JOAO SILVA;CG 160;DEPÓSITO;1;12250.00
27422;NF-E 407980/1;MARIA SANTOS;CB 500;FINANCIAMENTO;24;38000.00
27423;NF-E 407981/1;CARLOS COSTA;CG 160;DEPÓSITO;1;21500.00
27462;NF-E 408101/1;PEDRO OLIVEIRA;CG 160;A PAGAR;1;-968.61
27462;NF-E 408101/1;PEDRO OLIVEIRA;CG 160;A RECEBER;1;968.61
```

---

## ✅ Verificação de Resultados

### Checklist pós-teste

- [ ] Todos os 6 testes manuais passaram
- [ ] Cálculos HP12C retornam valores esperados
- [ ] Agrupamento por pedido + doc fiscal funciona
- [ ] Meta % calculado corretamente
- [ ] Distribuição proporcional de comissão OK
- [ ] Relatórios mostram dados corretos
- [ ] Nenhum erro no console (F12)
- [ ] Logs não contêm exceções críticas

### Validação de Dados

```bash
# Via MongoDB
mongo
use comissao_db
db.propostas.find({"Nº Pedido": 27421}).pretty()
db.vendedores.find({"nome": "PAULO BRAIDO"}).pretty()
db.parametros_aliquota.find().pretty()
```

### Teste de API via Curl

```bash
# Resumo de vendedores
curl http://localhost:5000/api/resumo/vendedor

# Vendas de um vendedor
curl "http://localhost:5000/api/vendedor/vendas?nome=PAULO%20BRAIDO"

# Processar comissões
curl -X POST http://localhost:5000/api/comissoes/processar
```

---

## 🎓 Cenários de Erro (Negative Tests)

### Erro 1: Arquivo Inválido

**Teste:**
1. Upload de arquivo .txt ou .xlsx sem dados
2. **Esperado:** Mensagem de erro clara

### Erro 2: Vendedor Não Encontrado

**Teste:**
1. Upload de proposta sem saída anteriormente
2. **Esperado:** Erro 404 "Vendedor não encontrado"

### Erro 3: Valor Negativo

**Teste:**
1. Upload com valor negativo em forma normal
2. **Esperado:** Sistema ignora ou mostra comissão zero

### Erro 4: Banco de Dados Offline

**Teste:**
1. Desligar MongoDB
2. Tentar acessar qualquer endpoint
3. **Esperado:** Erro 500 com mensagem clara

---

## 📈 Testes de Performance

### Teste de Carga: 1000 Propostas

```bash
# Gerar 1000 propostas e fazer upload
# Expectativa: < 10 segundos

Resultado esperado:
- ✅ Todas as propostas processadas
- ✅ Relatório carrega em < 2s
- ✅ Nenhuma perda de dados
```

---

## 🔍 Debugging

### Ativar Modo Debug

**No arquivo `.env`:**
```
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

**No navegador:**
- Abra DevTools: F12
- Aba "Network": veja requisições HTTP
- Aba "Console": veja erros JavaScript

### Verificar Logs

```bash
# Terminal
tail -f logs/comissao.log

# Ver últimas 100 linhas
Get-Content logs/comissao.log -Tail 100
```

---

**FIM DO GUIA DE TESTES**

*Documento de referência para QA e desenvolvimento*
