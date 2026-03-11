"""
Gera dataset de triplas para fine-tuning de embeddings (3D&T).

Uso (na raiz do projeto):
  python scripts/generate_embedding_dataset.py
  python scripts/generate_embedding_dataset.py --augment   # mais triplas (meta 2000)

Lê: data/entities/extracted_entities.json, data/taxonomy/auto_taxonomy.json,
     data/knowledge_graph/relations.json, data/properties/entity_properties.json
Gera: data/training/embedding_triples.jsonl, train_triples.jsonl, val_triples.jsonl
Valida: anchors devem ser entidades reais (existentes em extracted_entities).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.generate_embedding_dataset import run, MIN_TRIPLES

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera triplas para fine-tuning de embeddings.")
    parser.add_argument(
        "--augment",
        action="store_true",
        help="Gerar mais triplas (meta 2000; mínimo padrão é 1500).",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=None,
        metavar="N",
        help="Meta de triplas a gerar (ex.: 2000). Sobrescreve --augment se informado.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Semente aleatória.")
    args = parser.parse_args()
    if args.target is not None:
        min_triples = max(args.target, MIN_TRIPLES)
    else:
        min_triples = 2000 if args.augment else MIN_TRIPLES
    stats = run(seed=args.seed, min_triples=min_triples)
    if stats.get("error"):
        print(f"[ERRO] {stats['error']}")
        sys.exit(1)
    print("Dataset de embeddings gerado:")
    print(f"  Total de triplas: {stats['total_triples']}")
    print(f"  Treino: {stats['train']} (85%)")
    print(f"  Validação: {stats['val']} (15%)")
    print("  Por estratégia:", stats.get("by_strategy", {}))
    for k, p in stats.get("paths", {}).items():
        print(f"  {k}: {p}")
