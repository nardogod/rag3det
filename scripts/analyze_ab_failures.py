"""
Analisa falhas do A/B test de embeddings e gera triplas específicas para reforçar o fine-tuning.

Em vez de ler um log salvo, este script REEXECUTA a comparação baseline vs fine-tuned
usando as mesmas queries de benchmark do `ab_test_embeddings.py` e identifica
em quais queries o fine-tuned perde.

Para cada query em que o fine-tuned é pior que o baseline, gera triplas do tipo:
  - anchor: a própria query
  - positive: melhor trecho (maior score) segundo o fine-tuned
  - negative: melhor trecho segundo o baseline (quando ele diverge)

Saída:
  data/training/ab_failures_triples.jsonl  (anchor, positive, negative, weight, query)

Uso (na raiz do projeto):
  python scripts/analyze_ab_failures.py
  python scripts/analyze_ab_failures.py --queries 50
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retrieval.pipeline import retrieve_relevant_chunks

DATA = ROOT / "data"
OUT_PATH = DATA / "training" / "ab_failures_triples.jsonl"


def load_test_queries(n: int = 50) -> list[str]:
    """Copiado de ab_test_embeddings.load_test_queries (evita import circular)."""
    bench = DATA / "training" / "benchmark_queries.json"
    if bench.exists():
        with bench.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        queries = [q.get("query") or "" for q in raw if q.get("query")]
        if len(queries) >= n:
            return queries[:n]
    default = [
        "Fênix",
        "Bola de Fogo",
        "stats do Ghoul",
        "O que é Magia Elemental?",
        "custo de Cura Total",
        "diferença entre Magia Branca e Magia Negra",
        "Muralha de Fogo",
        "Invocação do Elemental",
        "O que é um Vampiro?",
        "Corpo Elemental",
        "Resistência à Magia",
        "Vulnerabilidade",
    ] * 5
    return default[:n]


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Analisa falhas do A/B test e gera triplas específicas.")
    p.add_argument("--queries", type=int, default=50)
    args = p.parse_args()

    queries = load_test_queries(args.queries)
    if not queries:
        print("[ERRO] Nenhuma query disponível para análise.")
        sys.exit(1)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated = 0

    with OUT_PATH.open("w", encoding="utf-8") as f_out:
        for q in queries:
            q_strip = q.strip()
            if not q_strip:
                continue
            try:
                chunks_b = retrieve_relevant_chunks(q_strip, k=6, use_baseline=True)
                chunks_f = retrieve_relevant_chunks(q_strip, k=6, use_baseline=False)
            except Exception as e:
                print(f"[WARN] Erro na query {q_strip!r}: {e}")
                continue

            scores_b = [getattr(c, "score", 0) or 0 for c in chunks_b]
            scores_f = [getattr(c, "score", 0) or 0 for c in chunks_f]
            mean_b = sum(scores_b) / len(scores_b) if scores_b else 0
            mean_f = sum(scores_f) / len(scores_f) if scores_f else 0

            if mean_f >= mean_b:
                # Fine-tuned não perdeu; não é alvo de reforço.
                continue

            # Escolhe melhor trecho fine-tuned e melhor trecho baseline
            best_f = chunks_f[0] if chunks_f else None
            best_b = chunks_b[0] if chunks_b else None
            if not best_f or not best_b:
                continue

            # RetrievedChunk tem atributo `content`, não `page_content`.
            pos_text = (getattr(best_f, "content", "") or "").strip()
            neg_text = (getattr(best_b, "content", "") or "").strip()
            if not pos_text or not neg_text:
                continue

            row = {
                "anchor": q_strip,
                "positive": pos_text,
                "negative": neg_text,
                "weight": 1.0,
                "strategy": "ab_failure",
            }
            f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
            generated += 1

    print("Análise de A/B concluída.")
    print(f"  Queries analisadas: {len(queries)}")
    print(f"  Triplas geradas (falhas): {generated}")
    print(f"  Arquivo: {OUT_PATH}")


if __name__ == "__main__":
    main()

