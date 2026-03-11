# Checklist pós-fine-tuning

Execute estes passos quando o treinamento de embeddings terminar.

**Modelo v2:** O retreinamento com 4 epochs e L2 salva em `models/embeddings/3dt_finetuned_v2/`. Para usá-lo, defina `EMBEDDING_MODEL` (ou equivalente) para esse path e reindexe.

---

## 1. Verificar se o modelo foi salvo corretamente

**Windows (PowerShell):**
```powershell
Get-ChildItem models/embeddings/3dt_finetuned/ | Format-Table Name, Length -AutoSize
```

**Linux/macOS:**
```bash
ls -lh models/embeddings/3dt_finetuned/
```

**Esperado:**
- `model.safetensors` (~450 MB)
- `tokenizer.json` (~16 MB)
- `config.json` / `config_sentence_transformers.json`
- `training_log.json` (com 3–4 epochs)

---

## 2. Verificar normalização L2

```bash
python scripts/verify_embedding_normalization.py
```

Ou inline:
```bash
python -c "
from sentence_transformers import SentenceTransformer
import numpy as np
model = SentenceTransformer('models/embeddings/3dt_finetuned')
emb = model.encode('Fênix')
norm = np.linalg.norm(emb)
print(f'Norma do embedding: {norm:.4f} (deve ser ~1.0)')
"
```

**Esperado:** Norma ≈ 1,0 e mensagem "[OK] Normalizado corretamente". Para o modelo v2: `--model models/embeddings/3dt_finetuned_v2`.

---

## 3. Verificar log de treino

**Windows (PowerShell):**
```powershell
Get-Content models/embeddings/3dt_finetuned/training_log.json | python -m json.tool | Select-Object -First 30
```

**Linux/macOS:**
```bash
cat models/embeddings/3dt_finetuned/training_log.json | python -m json.tool | head -30
```

**Esperado:** `history` com scores por epoch; idealmente score de validação melhorando (ou loss decrescendo).

---

## 4. Reindexar (limpar opcional)

O script `reindex_with_finetuned.py --both` já **remove e recria** as collections antes de indexar. Se quiser limpar o diretório Chroma por completo:

**Windows (PowerShell):**
```powershell
Remove-Item -Recurse -Force data/chroma -ErrorAction SilentlyContinue
python scripts/reindex_with_finetuned.py --both
```

**Linux/macOS:**
```bash
rm -rf data/chroma
python scripts/reindex_with_finetuned.py --both
```

Sem limpar (só recriar collections):
```bash
python scripts/reindex_with_finetuned.py --both
```

---

## 5. Testar query (fine-tuned)

```bash
python scripts/test_query.py "Fênix"
```

**Esperado:** "Bola de Fogo", "Muralha de Fogo" no top 3; distâncias na faixa 0,0–1,5 (não 5,0+).

---

## 6. Comparar com baseline

```bash
python scripts/test_query.py "Fênix" --baseline
```

---

## 7. Rodar A/B test completo

```bash
python scripts/ab_test_embeddings.py
```

**Esperado:** fine-tuned ganha em ≥ 55% das queries.

---

## Se algo der errado

| Problema | Solução |
|----------|---------|
| Norma não é ~1,0 | O fine-tuning já usa o módulo Normalize em `finetune_embeddings.py`. Se o modelo foi treinado antes dessa alteração, retreine. Ou use `encode(..., normalize_embeddings=True)` no código que chama o modelo. |
| Loss não decresceu | Aumentar learning rate; verificar se o dataset tem variedade; checar se triplas estão corretas (anchor/positive/negative). |
| "Bola de Fogo" ainda não aparece no topo | Verificar se está no dataset de treino (entidades/taxonomia); aumentar epochs para 4 ou gerar mais triplas com `--augment`. |
| A/B test < 55% | Aumentar epochs para 4; gerar mais triplas: `python scripts/generate_embedding_dataset.py --augment` e retreinar. |

---

## Resumo dos comandos (ordem)

```bash
# 1. Verificar modelo
ls -lh models/embeddings/3dt_finetuned/   # ou Get-ChildItem no PowerShell

# 2. Normalização
python scripts/verify_embedding_normalization.py

# 3. Log de treino
cat models/embeddings/3dt_finetuned/training_log.json | python -m json.tool | head -30

# 4. Reindexar
python scripts/reindex_with_finetuned.py --both

# 5. Query fine-tuned
python scripts/test_query.py "Fênix"

# 6. Query baseline
python scripts/test_query.py "Fênix" --baseline

# 7. A/B test
python scripts/ab_test_embeddings.py
```
