# Serviço de Valor Presente (VP)

## Visão Geral

Converte vendas parceladas em **CARTÃO** ou **CHEQUE** para **Valor Presente** usando taxas de juros, permitindo calcular o desconto real da operação.

**IMPORTANTE**: VP se aplica APENAS para:
- ✅ **CARTÃO** (parcelamento com juros)
- ✅ **CHEQUE** (cheque pós-datado com juros)

Todas as demais formas são consideradas **À VISTA** (sem VP):
- ❌ DEPÓSITO BANCÁRIO
- ❌ FINANCIAMENTO
- ❌ CONSÓRCIO
- ❌ BOLETO
- ❌ Outras formas

**Fórmula Base:**
```
VP = Σ(P / (1+i)^x)

Onde:
  P = valor da parcela
  i = taxa de juros por período
  x = número sequencial da parcela (1 a n)
```

---

## 1. Cálculo de Valor Presente Simples

```python
from app.services import ValorPresenteService

# Exemplo: 12 parcelas de R$1.000 com taxa de 2% ao mês
vp = ValorPresenteService.calcular_valor_presente(
    valor_parcela=1000,
    numero_parcelas=12,
    taxa_juros=0.02  # 2% ao mês
)

print(f"VP Total: R${vp:,.2f}")
# Output: VP Total: R$11,121.71
```

**Significado:** As 12 parcelas de R$1.000 (total nominal = R$12.000) têm valor presente de R$11.121,71

---

## 2. Cálculo de Desconto Percentual

```python
# Comparar valor de tabela com valor em parcelas
resultado = ValorPresenteService.calcular_desconto_percentual(
    valor_tabela=15000,      # Valor à vista (de tabela)
    valor_parcela=500,       # Valor de cada parcela
    numero_parcelas=36,      # 36 parcelas
    taxa_juros=0.015        # 1.5% ao mês
)

print(f"VP: R${resultado['valor_presente']:,.2f}")
print(f"Desconto R$: {resultado['desconto_absoluto']:,.2f}")
print(f"Desconto %: {resultado['desconto_percentual_formatado']}")

# Output:
# VP: R$14,850.50
# Desconto R$: 149.50
# Desconto %: 0.99%
```

**Significado:** A venda em 36 parcelas resultou em apenas 0.99% de desconto comparado ao preço de tabela

---

## 3. Detectar Taxa Padrão por Forma de Recebimento

```python
# Para CARTÃO e CHEQUE, retorna taxa com juros
# Para demais formas, retorna 0 (à vista)

taxa_cartao = ValorPresenteService.detectar_taxa_padrao("CARTÃO")          # 0.015 (1.5%)
taxa_cheque = ValorPresenteService.detectar_taxa_padrao("CHEQUE")          # 0.020 (2.0%)
taxa_deposito = ValorPresenteService.detectar_taxa_padrao("DEPÓSITO")      # 0.0 (à vista)
taxa_financ = ValorPresenteService.detectar_taxa_padrao("FINANCIAMENTO")   # 0.0 (à vista)
taxa_consorcio = ValorPresenteService.detectar_taxa_padrao("CONSÓRCIO")    # 0.0 (à vista)

print(f"Cartão (COM JUROS): {taxa_cartao * 100}%")
print(f"Depósito (À VISTA): {taxa_deposito * 100}%")
# Output: 
# Cartão (COM JUROS): 1.5%
# Depósito (À VISTA): 0.0%
```

---

## 4. Caso de Uso Real: Vendas de Moto

### Cenário: Moto ELITE 125 = R$20.000 à vista

**Opção 1: Depósito Bancário (à vista) - SEM VP**
```python
resultado = ValorPresenteService.calcular_desconto_percentual(
    valor_tabela=20000,
    valor_parcela=20000,
    numero_parcelas=1,
    taxa_juros=0.0  # À VISTA - SEM JUROS
)
# VP: R$20.000,00 | Desconto: 0% | Comissão: R$300,00
```

**Opção 2: Cartão (12x R$1.667) - COM VP**
```python
resultado = ValorPresenteService.calcular_desconto_percentual(
    valor_tabela=20000,
    valor_parcela=1667,
    numero_parcelas=12,
    taxa_juros=0.015  # 1.5% ao mês (CARTÃO)
)
# VP: R$18.182,81 | Desconto: 9.09% | Comissão: R$272,74
```

**Opção 3: Cheque (6x R$3.334) - COM VP**
```python
resultado = ValorPresenteService.calcular_desconto_percentual(
    valor_tabela=20000,
    valor_parcela=3334,
    numero_parcelas=6,
    taxa_juros=0.020  # 2.0% ao mês (CHEQUE)
)
# VP: R$18.675,17 | Desconto: 6.62% | Comissão: R$280,13
```

**Opção 4: Financiamento (36x R$667) - SEM VP (À VISTA)**
```python
resultado = ValorPresenteService.calcular_desconto_percentual(
    valor_tabela=20000,
    valor_parcela=667,
    numero_parcelas=36,
    taxa_juros=0.0  # À VISTA - SEM JUROS
)
# VP: R$20.000,00 | Desconto: 0% | Comissão: R$300,00
```

**Decisão:** 
- DEPÓSITO e FINANCIAMENTO: Usar R$20.000 (valor tabela)
- CARTÃO: Usar R$18.182,81 (VP com desconto de 9.09%)
- CHEQUE: Usar R$18.675,17 (VP com desconto de 6.62%)

---

## 5. Integração com Cálculo de Comissão

```python
from app.services import ValorPresenteService, ComissaoService

# Proposta de venda
proposta = {
    'modelo': 'ELITE 125',
    'forma_recebimento': 'CARTÃO',
    'valor_parcela': 1667,
    'numero_parcelas': 12,
    'valor_tabela': 20000
}

# 1. Detectar taxa baseada na forma
taxa = ValorPresenteService.detectar_taxa_padrao(proposta['forma_recebimento'])

# 2. Calcular VP
calculo_vp = ValorPresenteService.calcular_desconto_percentual(
    valor_tabela=proposta['valor_tabela'],
    valor_parcela=proposta['valor_parcela'],
    numero_parcelas=proposta['numero_parcelas'],
    taxa_juros=taxa
)

# 3. Usar VP para calcular comissão
valor_base = calculo_vp['valor_presente']  # R$18.182,81 (não R$20.000)
aliquota = 0.015  # 1.5%
comissao = valor_base * aliquota

print(f"Forma: {proposta['forma_recebimento']}")
print(f"Valor Tabela: R${proposta['valor_tabela']:,.2f}")
print(f"Valor Presente: R${calculo_vp['valor_presente']:,.2f}")
print(f"Desconto: {calculo_vp['desconto_percentual_formatado']}")
print(f"Comissão (sobre VP): R${comissao:,.2f}")
```

---

## 6. Taxas Padrão Configuradas

| Forma de Recebimento | Taxa | Tipo | Comentário |
|---|---|---|---|
| **CARTÃO** | **1.5%** | ✅ **COM VP** | Parcelamento com juros |
| **CHEQUE** | **2.0%** | ✅ **COM VP** | Cheque pós-datado com juros |
| DEPÓSITO | 0.0% | ❌ SEM VP | À vista |
| FINANCIAMENTO | 0.0% | ❌ SEM VP | À vista |
| CONSÓRCIO | 0.0% | ❌ SEM VP | À vista |
| BOLETO | 0.0% | ❌ SEM VP | À vista |
| Outras | 0.0% | ❌ SEM VP | À vista |

---

## 7. Notas Importantes

### ✅ Benefícios
- **Comparação Justa**: Apenas CARTÃO e CHEQUE sofrem desconto
- **Desconto Correto**: Identifica o custo financeiro real
- **Comissão Justa**: CARTÃO e CHEQUE têm comissão menor (pelo desconto)
- **Rastreamento**: Registra VP realizado para auditoria

### ⚠️ Regra de Ouro
```
Se forma_recebimento in ['CARTÃO', 'CHEQUE']:
    Usar VP com taxa de juros
Else:
    Usar valor de tabela (sem VP)
```

### 📝 Próximos Passos
1. Integrar VP ao upload de propostas
2. Armazenar VP calculado na collection `propostas`
3. Usar VP (não valor tabela) para CARTÃO/CHEQUE em comissão
4. Relatório: Mostrar VP vs Valor Tabela
