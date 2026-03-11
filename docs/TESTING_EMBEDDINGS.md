# Testes: Fine-tuning e Queries

**Checklist completo pós-fine-tuning (ordem dos comandos):** [CHECKLIST_POS_FINETUNING.md](CHECKLIST_POS_FINETUNING.md)

---

## TESTE 1: Verificar se o fine-tuning rodou

### 1.1 Modelo salvo

```powershell
# Windows PowerShell
Get-ChildItem models/embeddings/3dt_finetuned/

# bash
ls models/embeddings/3dt_finetuned/
```

**Esperado:** `config_sentence_transformers.json`, `model.safetensors` (ou `pytorch_model.bin`), `tokenizer.json`, `1_Pooling/`, etc.

### 1.2 Log de treinamento

```powershell
Get-Content models/embeddings/3dt_finetuned/training_log.json
```

**Esperado:** `model_name`, `train_samples`, `val_samples`, `best_score`, `history` com métricas por epoch.

---

## TESTE 2: Query fine-tuned vs baseline

Reindexar se o índice foi criado com outro modelo (erro 768 vs 384 dims):

```bash
python scripts/reindex_with_finetuned.py --both
```

Rodar queries:

```bash
python scripts/test_query.py "Fênix"
python scripts/test_query.py "Fênix" --baseline
```

**Esperado:** Fine-tuned traz "Bola de Fogo", "Muralha de Fogo" no top 3; baseline pode trazer trechos menos relacionados.

---

## TESTE 3: Vizinhança no espaço vetorial

```bash
# Reindexar se necessário
python scripts/reindex_with_finetuned.py --both

# Distâncias entre entidades (fine-tuned vs baseline)
python scripts/test_embedding_neighborhood.py
```

**Esperado:** Fine-tuned: Fênix mais próximo de Bola de Fogo (razão dist(Fênix,Ghoul)/dist(Fênix,Bola de Fogo) > 1.5). Baseline: razão menor.

---

## TESTE 4: A/B test completo

```bash
# Verificar se ambos os índices existem
python scripts/check_indices.py

# Se faltar algum, recriar
python scripts/reindex_with_finetuned.py --both

# Rodar A/B test
python scripts/ab_test_embeddings.py
```

**Esperado:** Score médio fine-tuned > baseline; fine-tuned ganha em ≥ 55% das queries; criado `data/embedding_finetuned_default.flag`.

---

## TESTE 5: Cache separado

O cache de embeddings fica em **`data/embedding_cache/`** (não `data/cache/`).

```powershell
Get-ChildItem data/embedding_cache/
```

**Esperado:** Dois arquivos shelve (ou pastas) com prefixos diferentes, por exemplo:

- Um para o modelo fine-tuned (path ou id com `3dt_finetuned`)
- Um para o baseline (`sentence-transformers/paraphrase-multilingual-...`)

Trocar de modelo gera novo prefixo e novo cache.

---

## TESTE 5.5: Verificar normalização L2 (após fine-tuning)

O modelo fine-tuned deve produzir embeddings L2-normalizados (norma ≈ 1) para distâncias consistentes.

```bash
python scripts/verify_embedding_normalization.py
python scripts/verify_embedding_normalization.py --model models/embeddings/3dt_finetuned --text "Bola de Fogo"
```

**Esperado:** `Norma L2: 1.0000` (ou próximo) e mensagem "✓ Normalizado corretamente". Se não estiver normalizado, o fine-tuning deve ser feito com o módulo Normalize ativo (já incluído em `finetune_embeddings.py`).

---

## TESTE 6: Validação final rápida

```bash
python scripts/validate_embedding_config.py
```

**Esperado:** Exibe configuração (embedding_model, fallback), modelo efetivo carregado e teste de encode com "Fênix", "Bola de Fogo", "Ghoul"; dimensões consistentes e mensagem "✓ Embedding funcionando!".

---

## Diagnóstico rápido

| Problema | Comando / ação |
|----------|----------------|
| Modelo não encontrado | `Get-ChildItem models/embeddings/` |
| Índice não existe ou dimensão errada | `python scripts/reindex_with_finetuned.py --both` |
| Cache corrompido | Apagar `data/embedding_cache/` e reindexar |
| A/B test falha | `python scripts/check_indices.py` e recriar índices com `--both` |
| Query lenta | Verificar se `data/embedding_cache/` existe e está sendo usado |

---

## Checklist final

| Teste | Comando | Status |
|-------|---------|--------|
| Modelo salvo | `Get-ChildItem models/embeddings/3dt_finetuned/` | ⬜ |
| Query fine-tuned | `python scripts/test_query.py "Fênix"` | ⬜ |
| Query baseline | `python scripts/test_query.py "Fênix" --baseline` | ⬜ |
| Distâncias vetoriais | `python scripts/test_embedding_neighborhood.py` | ⬜ |
| Índices existem | `python scripts/check_indices.py` | ⬜ |
| A/B test | `python scripts/ab_test_embeddings.py` | ⬜ |
| Cache separado | `Get-ChildItem data/embedding_cache/` | ⬜ |
| Normalização L2 | `python scripts/verify_embedding_normalization.py` | ⬜ |
| Validação final | `python scripts/validate_embedding_config.py` | ⬜ |
