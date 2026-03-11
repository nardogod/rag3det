"""
Wrapper de linha de comando para fine-tuning do reranker.

Uso (na raiz do projeto):
  python scripts/generate_rerank_dataset.py
  python scripts/finetune_reranker.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.finetune_reranker import (
    BASE_MODEL,
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    MAX_LENGTH,
    run_finetune_reranker,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning do reranker 3D&T.")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--base_model", type=str, default=BASE_MODEL)
    parser.add_argument("--max_length", type=int, default=MAX_LENGTH)
    args = parser.parse_args()

    result = run_finetune_reranker(
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_length=args.max_length,
    )
    if result.get("error"):
        print(f"[ERRO] {result['error']}")
        sys.exit(1)
    print("[OK] Fine-tuning reranker concluído.")
    print(f"  Modelo salvo em: {result['output_dir']}")
    print(f"  Summary: {result['summary_path']}")


if __name__ == "__main__":
    main()

