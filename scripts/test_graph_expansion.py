"""
Testa expansão de query usando o grafo de conhecimento.

Uso (na raiz do projeto):
  python scripts/test_graph_expansion.py "Fênix"
  python scripts/test_graph_expansion.py "Insano Megalomaníaco"
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retrieval.graph_expansion import expand_query_with_graph, get_expanded_queries_flat

def main() -> None:
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "Fênix"
    print(f"Query: {query}")
    weighted = expand_query_with_graph(query, max_terms=5)
    print("Expansões (termo, peso):")
    for term, w in weighted:
        print(f"  {term!r} -> {w}")
    flat = get_expanded_queries_flat(query, max_terms=5)
    print("Lista plana para busca:", flat)


if __name__ == "__main__":
    main()
