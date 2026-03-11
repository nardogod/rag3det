"""
Fine-tuning v3 de embeddings (wrapper de linha de comando).

Uso (na raiz do projeto):
  python scripts/finetune_embeddings_v3.py --dataset v2 --epochs 5 --lr 3e-5

Datasets:
  - v1: data/training/train_triples.jsonl / val_triples.jsonl  -> models/embeddings/3dt_finetuned_v2/
  - v2: data/training/train_triples_v2.jsonl / val_triples_v2.jsonl (+ ab_failures) -> models/embeddings/3dt_finetuned_v3/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.finetune_embeddings_v3 import run_finetune_v3, BATCH_SIZE, EPOCHS, LEARNING_RATE


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning v3 de embeddings 3D&T (dataset v1/v2).")
    parser.add_argument(
        "--dataset",
        choices=["v1", "v2"],
        default="v2",
        help="Versão do dataset (v1=original, v2=hard negatives).",
    )
    parser.add_argument("--epochs", type=int, default=EPOCHS, help="Número máximo de epochs (default: 5).")
    parser.add_argument("--lr", type=float, default=LEARNING_RATE, help="Learning rate (default: 3e-5).")
    parser.add_argument(
        "--no-ab-failures",
        action="store_true",
        help="Não adicionar triplas de falhas do A/B (ab_failures_triples.jsonl).",
    )
    args = parser.parse_args()

    use_ab_failures = not args.no_ab_failures

    print("[INFO] Iniciando fine-tuning v3")
    print(f"  Dataset: {args.dataset}")
    print(f"  Epochs: {args.epochs}")
    print(f"  LR: {args.lr}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  AB failures: {'ON' if use_ab_failures else 'OFF'}")

    result = run_finetune_v3(
        dataset=args.dataset,
        epochs=args.epochs,
        lr=args.lr,
        use_ab_failures=use_ab_failures,
    )
    if result.get("error"):
        print(f"[ERRO] {result['error']}")
        sys.exit(1)

    print("[OK] Fine-tuning v3 concluído.")
    print(f"  Modelo salvo em: {result['output_path']}")
    print(f"  Melhor score (val): {result['best_score']:.4f}")
    print(f"  Log/config: {result['training_log_path']}")


if __name__ == "__main__":
    main()

