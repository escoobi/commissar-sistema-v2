# ⚡ Início Rápido: Taxas Progressivas em 5 Minutos

## 🎯 Objetivo
Colocar o sistema de taxas progressivas em produção em 5 minutos.

---

## ⏱️ PASSO 1: Verificar Instalação (30 segundos)

```bash
# Validar código
python -m py_compile app/services/__init__.py

# Resultado esperado: (sem erro)
# ✅ Sintaxe OK
```

---

## ⏱️ PASSO 2: Ver Demonstração (2 minutos)

```bash
# Executar demo
python demo_taxas_progressivas.py
```

**Resultado esperado:**
```
DEMONSTRAÇÃO: SISTEMA DE TAXAS PROGRESSIVAS

CENÁRIO 1: SEM tabela progressiva
  Comissão: R$300,00

CENÁRIO 2: COM tabela progressiva CARTÃO 10x
  VP: R$19.959,16
  Comissão: R$299,39

✓ Tabela progressiva REDUZ comissão em 0.20%
✓ Integração completa e operacional!
```

Se viu isso → ✅ Tudo funciona!

---

## ⏱️ PASSO 3: Criar Primeira Tabela (2 minutos)

### **Via Interface Web**

1. **Abra o sistema:** `http://localhost:5000`
2. **Vá para:** Menu → **Taxas Progressivas**
3. **Clique:** "Criar Nova Tabela"
4. **Preencha:**
   ```
   Forma: CARTÃO
   Parcelas: 10
   Descrição: Tabela padrão CARTÃO 10x
   ```
5. **Clique:** "Gerar Campos"
6. **Copie estes valores:**
   ```
   Parc 1:  0
   Parc 2:  0.5151
   Parc 3:  0.3468
   Parc 4:  0.2626
   Parc 5:  0.2122
   Parc 6:  0.1785
   Parc 7:  0.1545
   Parc 8:  0.1385
   Parc 9:  0.1225
   Parc 10: 0.1113
   ```
7. **Clique:** "Salvar"

✅ **Tabela criada!**

---

## ⏱️ PASSO 4: Testar com Proposta (1 minuto)

### **Preparar CSV de Teste**

Crie arquivo `teste.csv`:
```csv
Pessoa,Modelo,Valor Total,Forma Recebimento,Numero Parcelas
João Silva,TITAN 150,20000,CARTÃO,10
```

### **Importar**

1. **Vá para:** Menu → **Importar Propostas**
2. **Selecione:** `teste.csv`
3. **Clique:** "Importar"

✅ **Proposta importada!**

### **Ver Resultado**

**Via MongoDB:**
```bash
mongo
use comissao_2
db.comissoes.find({"valor_venda": 20000})
```

**Resultado esperado:**
```json
{
  "valor_venda": 20000,
  "valor_comissao": 299.39,
  "forma_recebimento": "CARTÃO",
  "numero_parcelas": 10
}
```

✅ **Comissão calculada com VP progressivo!**

---

## 🎉 PRONTO!

**Em menos de 5 minutos você:**
- ✅ Validou o código
- ✅ Viu demonstração
- ✅ Criou tabela progressiva
- ✅ Testou integração

---

## 📚 Para Aprender Mais

| Se quer... | Leia... | Tempo |
|-----------|--------|--------|
| Entender o conceito | [TAXAS_PROGRESSIVAS.md](TAXAS_PROGRESSIVAS.md) | 5 min |
| Detalhes técnicos | [INTEGRACAO_TAXAS_PROGRESSIVAS.md](INTEGRACAO_TAXAS_PROGRESSIVAS.md) | 10 min |
| Ver arquitetura | [ARQUITETURA_INTEGRACAO.md](ARQUITETURA_INTEGRACAO.md) | 10 min |
| Fazer testes | [TESTES_TAXAS_PROGRESSIVAS.md](TESTES_TAXAS_PROGRESSIVAS.md) | 20 min |
| Deploy | [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md) | 15 min |

---

## ❓ FAQ Rápido

**P: Preciso alterar algo no CSV?**  
A: Não! Está tudo automático.

**P: E se não criar tabela?**  
A: Usa fallback (taxa fixa ou valor nominal). Funciona tudo igual.

**P: Posso editar tabela depois?**  
A: Sim! Menu → Taxas Progressivas → Editar

**P: Qual é o benefício?**  
A: Comissões mais realistas. Veja demo!

**P: Posso ver diferença?**  
A: Sim! Compare comissão com/sem tabela (veja demo).

---

## ⚡ Próximos Passos

1. ✅ Criar tabelas para TODAS suas formas (CARTÃO, CHEQUE, etc.)
2. ✅ Importar propostas normalmente
3. ✅ Sistema usa automaticamente

**Pronto!** 🚀

---

## 🆘 Se algo não funcionar

1. **Verificar erro:**
   ```bash
   tail -f logs/app.log
   ```

2. **Restaurar:**
   ```bash
   # Deletar tabela e voltar a usar taxa fixa
   db.taxas_progressivas.deleteMany({})
   ```

3. **Contato:**
   - Ver TROUBLESHOOTING em [INTEGRACAO_TAXAS_PROGRESSIVAS.md](INTEGRACAO_TAXAS_PROGRESSIVAS.md)

---

**Tempo total:** ⏱️ ~5 minutos  
**Status:** ✅ 100% Funcional  
**Pronto para usar:** 🚀 AGORA!
