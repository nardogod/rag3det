"""
Gera dataset de pares (query, documento, label) para fine-tuning do reranker.

Uso (na raiz do projeto):
  python scripts/generate_rerank_dataset.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.generate_rerank_dataset import generate_pairs


if __name__ == "__main__":
    stats = generate_pairs()
    if stats.get("error"):
        print(f"[ERRO] {stats['error']}")
        sys.exit(1)
    print("Dataset de reranking gerado:")
    print(f"  Total de pares: {stats['total_pairs']}")
    print(f"  Por label: {stats.get('by_label', {})}")
    print(f"  Por dificuldade: {stats.get('by_difficulty', {})}")
    for k, p in stats.get("paths", {}).items():
        print(f"  {k}: {p}")

