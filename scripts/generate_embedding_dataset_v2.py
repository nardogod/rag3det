"""
Gera dataset de triplas v2 para fine-tuning de embeddings (3D&T), focado em hard negatives.

Uso (na raiz do projeto):
  python scripts/generate_embedding_dataset_v2.py --target 3000

Lê: data/entities/extracted_entities.json, data/properties/entity_properties.json
Gera: data/training/embedding_triples_v2.jsonl, train_triples_v2.jsonl, val_triples_v2.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.generate_embedding_dataset_v2 import MIN_TRIPLES_V2, run_v2


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera triplas v2 (hard negatives) para fine-tuning de embeddings.")
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        metavar="N",
        help="Meta de triplas a gerar (ex.: 3000). Default: 3000.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Semente aleatória.")
    args = parser.parse_args()

    min_triples = max(args.target or MIN_TRIPLES_V2, MIN_TRIPLES_V2)
    stats = run_v2(seed=args.seed, min_triples=min_triples)
    if stats.get("error"):
        print(f"[ERRO] {stats['error']}")
        sys.exit(1)
    print("Dataset de embeddings v2 gerado:")
    print(f"  Total de triplas: {stats['total_triples']}")
    print(f"  Treino: {stats['train']} (85%)")
    print(f"  Validação: {stats['val']} (15%)")
    print("  Por estratégia:", stats.get("by_strategy", {}))
    for k, p in stats.get("paths", {}).items():
        print(f"  {k}: {p}")


if __name__ == "__main__":
    main()

