"""
Fine-tuning de embeddings para domínio 3D&T (4 epochs, L2 normalizado).

Uso (na raiz do projeto):
  python scripts/finetune_embeddings.py

Recomendado antes: python scripts/generate_embedding_dataset.py --target 2000

Carrega data/training/train_triples.jsonl e val_triples.jsonl.
Treina com TripletLoss (4 epochs, eval a cada 50 steps); salva melhor em
models/embeddings/3dt_finetuned_v2/. Gera training_log.json.
Após treino: python scripts/verify_embedding_normalization.py --model models/embeddings/3dt_finetuned_v2
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.finetune_embeddings import run_finetune

if __name__ == "__main__":
    result = run_finetune()
    if result.get("error"):
        print(f"[ERRO] {result['error']}")
        sys.exit(1)
    print("Fine-tuning concluído.")
    print(f"  Modelo salvo em: {result['output_path']}")
    print(f"  Melhor score (val): {result['best_score']:.4f}")
    print(f"  Log: {result['training_log_path']}")
    for e in result.get("history", [])[-5:]:
        print(f"    epoch {e['epoch']} step {e['step']} score {e['score']:.4f}")
