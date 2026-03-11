"""
Testa uma query e mostra os trechos recuperados (com embedding fine-tuned).

Uso (na raiz do projeto):
  python scripts/test_query.py "Fênix"
  python scripts/test_query.py "Fênix" --baseline   # compara com índice baseline (genérico)

Esperado para "Fênix": "Bola de Fogo", "Muralha de Fogo" ou trechos sobre Invocação da Fênix
antes de entidades não relacionadas.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retrieval.pipeline import retrieve_relevant_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Testa retrieval para uma query.")
    parser.add_argument("query", nargs="?", default="Fênix", help="Query (default: Fênix)")
    parser.add_argument("--baseline", action="store_true", help="Usar índice baseline (embedding genérico)")
    parser.add_argument("-k", type=int, default=6, help="Número de trechos a retornar")
    args = parser.parse_args()

    query = args.query.strip() or "Fênix"
    use_baseline = args.baseline
    model_label = "baseline (genérico)" if use_baseline else "fine-tuned"

    print(f"Query: {query!r}")
    print(f"Modelo: {model_label}")
    print(f"Top-{args.k} trechos:\n")

    try:
        chunks = retrieve_relevant_chunks(query, k=args.k, use_baseline=use_baseline)
    except Exception as e:
        print(f"ERRO: {e}")
        sys.exit(1)

    if not chunks:
        print("Nenhum trecho retornado.")
        sys.exit(0)

    for i, c in enumerate(chunks, 1):
        score = getattr(c, "score", None) or 0
        snippet = (c.content or "")[:200].replace("\n", " ")
        print(f"  {i}. [score={score:.4f}] {snippet}...")
        print()
    print("Concluído.")


if __name__ == "__main__":
    main()
