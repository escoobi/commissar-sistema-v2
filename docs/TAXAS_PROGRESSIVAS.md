# 📊 Sistema de Taxas Progressivas por Parcela

## 🎯 Objetivo
Permitir configurar coeficientes de desconto diferentes para cada número de parcela, possibilitando taxas mais realistas que variam conforme a parcela (1ª mais cara, 10ª mais barata).

---

## 📋 Como Funciona

### **Conceito**
Ao invés de usar uma **taxa fixa** (ex: 1.5% ao mês), o sistema permite definir um **coeficiente diferente para cada parcela**.

**Exemplo: CARTÃO 10x**
```
1ª parcela:  0.0000%     (sem desconto)
2ª parcela:  0.5151%     (desconto pequeno)
3ª parcela:  0.3468%
4ª parcela:  0.2626%
...
10ª parcela: 0.1113%     (desconto menor)
```

### **Cálculo do VP**
```
VP = P1 × (1 - 0.0000/100)
   + P2 × (1 - 0.5151/100)
   + P3 × (1 - 0.3468/100)
   + ... 
   + P10 × (1 - 0.1113/100)

Exemplo com P = R$2.000:
VP = 2000×(1-0) + 2000×(1-0.005151) + 2000×(1-0.003468) + ...
VP = 2000 + 1989.70 + 1993.06 + ...
VP = R$19.847,35 (desconto de R$152,65)
```

---

## 🖥️ Interface

### **Onde Acessar**
Menu → **Taxas Progressivas**

### **O que Você Faz**
1. **Criar tabela**
   - Forma: CARTÃO (ou CHEQUE, etc.)
   - Parcelas: 10 (quantidade de coeficientes)
   - Descrição: Tabela padrão CARTÃO 10x (opcional)
   - Coeficientes: [0, 0.5151, 0.3468, ...]

2. **Editar tabela**
   - Clique em "Editar"
   - Altere os coeficientes
   - Salve

3. **Deletar tabela**
   - Clique em "Deletar"
   - Confirme

---

## 📝 Exemplo Prático

### **Cenário: CARTÃO 10x**

**Passo 1: Acessar /taxas-progressivas**

**Passo 2: Criar Nova Tabela**
```
Forma: CARTÃO
Parcelas: 10
Descrição: Tabela padrão CARTÃO 10 parcelas
```

**Passo 3: Inserir Coeficientes**
```
Parc. 1: 0.0000
Parc. 2: 0.5151
Parc. 3: 0.3468
Parc. 4: 0.2626
Parc. 5: 0.2122
Parc. 6: 0.1785
Parc. 7: 0.1545
Parc. 8: 0.1385
Parc. 9: 0.1225
Parc. 10: 0.1113
```

**Passo 4: Salvar**
- Tabela criada com sucesso!

---

## 🔗 API

### **Listar Tabelas**
```
GET /api/taxas-progressivas

Response:
{
  "status": "sucesso",
  "dados": [
    {
      "_id": "65abc123...",
      "forma_recebimento": "CARTÃO",
      "numero_parcelas": 10,
      "coeficientes": [0, 0.5151, 0.3468, ...],
      "descricao": "Tabela padrão CARTÃO 10x",
      "ativa": true
    }
  ]
}
```

### **Criar Tabela**
```
POST /api/taxas-progressivas

Body:
{
  "forma_recebimento": "CARTÃO",
  "numero_parcelas": 10,
  "coeficientes": [0, 0.5151, 0.3468, 0.2626, 0.2122, 0.1785, 0.1545, 0.1385, 0.1225, 0.1113],
  "descricao": "Tabela padrão CARTÃO 10x"
}

Response:
{
  "status": "sucesso",
  "mensagem": "Tabela para CARTÃO (10x) criada com sucesso",
  "id": "65abc123..."
}
```

### **Obter Tabela**
```
GET /api/taxas-progressivas/<id>

Response:
{
  "status": "sucesso",
  "dados": { ... }
}
```

### **Atualizar Tabela**
```
PUT /api/taxas-progressivas/<id>

Body:
{
  "coeficientes": [0, 0.5151, 0.3468, ...],
  "descricao": "Tabela atualizada"
}

Response:
{
  "status": "sucesso",
  "mensagem": "Tabela atualizada com sucesso"
}
```

### **Deletar Tabela**
```
DELETE /api/taxas-progressivas/<id>

Response:
{
  "status": "sucesso",
  "mensagem": "Tabela deletada com sucesso"
}
```

---

## 🛠️ Integração com VP

### **Fluxo Atual (a implementar)**
```python
# No arquivo: app/services/__init__.py

class ValorPresenteService:
    @staticmethod
    def calcular_com_coeficientes(valor_parcela, numero_parcelas, forma_recebimento):
        """Calcula VP usando coeficientes progressivos"""
        
        # 1. Busca coeficientes da tabela
        coeficientes = TaxaProgressivaService.buscar_coeficientes(
            forma_recebimento, 
            numero_parcelas
        )
        
        # 2. Se não encontrar, usa taxa fixa (fallback)
        if not coeficientes:
            taxa = ValorPresenteService.detectar_taxa_padrao(forma_recebimento)
            # Usa taxa fixa normalmente
            ...
        
        # 3. Se encontrar, calcula com coeficientes
        else:
            vp_total = 0
            for i, coef in enumerate(coeficientes, 1):
                desconto = coef / 100
                vp_parcela = valor_parcela * (1 - desconto)
                vp_total += vp_parcela
            return vp_total
```

---

## 📊 Exemplos de Tabelas Padrão

### **Tabela 1: CARTÃO 10x**
```
Parcela | Coef (%)
--------|----------
1       | 0.0000
2       | 0.5151
3       | 0.3468
4       | 0.2626
5       | 0.2122
6       | 0.1785
7       | 0.1545
8       | 0.1385
9       | 0.1225
10      | 0.1113
```

### **Tabela 2: CHEQUE 6x**
```
Parcela | Coef (%)
--------|----------
1       | 0.0000
2       | 0.8234
3       | 0.5123
4       | 0.3856
5       | 0.3012
6       | 0.2456
```

### **Tabela 3: CARTÃO 12x**
```
Parcela | Coef (%)
--------|----------
1       | 0.0000
2       | 0.4892
3       | 0.3267
4       | 0.2468
5       | 0.1976
6       | 0.1665
7       | 0.1425
8       | 0.1236
9       | 0.1089
10      | 0.0967
11      | 0.0865
12      | 0.0778
```

---

## ✅ Checklist de Implementação

- ✅ Modelo `TaxaProgressivaModel` criado
- ✅ Serviço `TaxaProgressivaService` implementado (CRUD completo)
- ✅ Endpoints API criados:
  - ✅ GET /api/taxas-progressivas (listar)
  - ✅ POST /api/taxas-progressivas (criar)
  - ✅ GET /api/taxas-progressivas/<id> (obter)
  - ✅ PUT /api/taxas-progressivas/<id> (atualizar)
  - ✅ DELETE /api/taxas-progressivas/<id> (deletar)
- ✅ Interface HTML completa (criar, editar, deletar)
- ✅ Menu de navegação atualizado
- ✅ Validação de coeficientes
- ⏳ Integração com VP (próxima fase)

---

## 🚀 Próximo Passo

Integrar `TaxaProgressivaService.buscar_coeficientes()` na função de cálculo de VP para usar coeficientes quando disponível, com fallback para taxa fixa.

```python
# Quando houver coeficientes: usar progressivo
# Quando não houver: usar taxa fixa
```

---

## 📌 Notas

- **Tabelas são reutilizáveis**: uma tabela CARTÃO 10x serve para qualquer venda em 10 parcelas
- **Fallback automático**: se não encontrar tabela, volta para taxa fixa
- **Flexibilidade**: cada forma pode ter múltiplas tabelas (CARTÃO 6x, CARTÃO 10x, CARTÃO 12x, etc.)
- **Ativa/Inativa**: tabelas têm status (implementar se necessário)
