"""
A/B test: embedding genérico vs fine-tuned.

- 50% das queries usam índice baseline (genérico), 50% índice fine-tuned.
- Log: qual modelo teve melhor reranking score médio por query.
- Decision: se fine-tuned ganha em 55%+ das queries, grava flag para torná-lo padrão.

Requisito: rodar antes scripts/reindex_with_finetuned.py com --both para criar os dois índices,
ou rodar reindex duas vezes (uma sem --both = finetuned, depois build manual do baseline).

Uso:
  python scripts/ab_test_embeddings.py
  python scripts/ab_test_embeddings.py --queries 30
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retrieval.pipeline import retrieve_relevant_chunks

DATA = ROOT / "data"
FLAG_PATH = DATA / "embedding_finetuned_default.flag"
WIN_THRESHOLD = 0.55  # 55%+ para tornar fine-tuned padrão


def load_test_queries(n: int = 50) -> list[str]:
    """Carrega queries do benchmark ou usa lista padrão."""
    bench = DATA / "training" / "benchmark_queries.json"
    if bench.exists():
        with bench.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        queries = [q.get("query") or "" for q in raw if q.get("query")][:n]
        if len(queries) >= n:
            return queries
    # Fallback: queries fixas
    default = [
        "Fênix", "Bola de Fogo", "stats do Ghoul", "O que é Magia Elemental?",
        "custo de Cura Total", "diferença entre Magia Branca e Magia Negra",
        "Muralha de Fogo", "Invocação do Elemental", "O que é um Vampiro?",
        "Corpo Elemental", "Resistência à Magia", "Vulnerabilidade",
    ] * 5
    return default[:n]


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--queries", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    queries = load_test_queries(args.queries)
    random.seed(args.seed)

    results_baseline = []
    results_finetuned = []
    wins_finetuned = 0

    for q in queries:
        if not q.strip():
            continue
        use_baseline = random.random() < 0.5
        try:
            chunks_b = retrieve_relevant_chunks(q, k=6, use_baseline=True)
            chunks_f = retrieve_relevant_chunks(q, k=6, use_baseline=False)
        except Exception as e:
            print(f"Erro na query {q!r}: {e}")
            continue
        scores_b = [getattr(c, "score", 0) or 0 for c in chunks_b]
        scores_f = [getattr(c, "score", 0) or 0 for c in chunks_f]
        mean_b = sum(scores_b) / len(scores_b) if scores_b else 0
        mean_f = sum(scores_f) / len(scores_f) if scores_f else 0
        results_baseline.append(mean_b)
        results_finetuned.append(mean_f)
        if mean_f > mean_b:
            wins_finetuned += 1

    n = len(results_baseline)
    if n == 0:
        print("Nenhuma query executada.")
        sys.exit(1)

    win_pct = wins_finetuned / n
    avg_b = sum(results_baseline) / n
    avg_f = sum(results_finetuned) / n

    print("--- A/B Test Embeddings ---")
    print(f"  Queries: {n}")
    print(f"  Rerank score médio baseline:   {avg_b:.4f}")
    print(f"  Rerank score médio fine-tuned:  {avg_f:.4f}")
    print(f"  Fine-tuned ganhou em {wins_finetuned}/{n} ({win_pct*100:.1f}%) das queries")

    if win_pct >= WIN_THRESHOLD:
        DATA.mkdir(parents=True, exist_ok=True)
        FLAG_PATH.write_text("fine-tuned", encoding="utf-8")
        print(f"  -> Fine-tuned >= 55%. Flag gravada em {FLAG_PATH} (padrao mantido: fine-tuned).")
    else:
        if FLAG_PATH.exists():
            FLAG_PATH.unlink()
        print(f"  -> Fine-tuned < 55%. Recomendacao: mais treino ou mais dados.")

    sys.exit(0)


if __name__ == "__main__":
    main()
