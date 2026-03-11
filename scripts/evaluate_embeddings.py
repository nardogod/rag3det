"""
Benchmark de embeddings: baseline vs fine-tuned.

Uso (na raiz do projeto):
  python scripts/evaluate_embeddings.py

Carrega data/training/benchmark_queries.json e data/processed/chunks.json.
Roda retrieval com modelo baseline e (se existir) modelo fine-tuned.
Métricas: MRR@10, Recall@5, NDCG@5, MAP.
Gera models/embeddings/evaluation_report.json.
Critério de aceitação: MRR melhorou >= 15% vs baseline.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ml.training.evaluate_embeddings import (
    REPORT_PATH,
    MRR_IMPROVEMENT_THRESHOLD,
    run_evaluation,
)

if __name__ == "__main__":
    report = run_evaluation(run_viz=True)
    if report.get("error"):
        print(f"[ERRO] {report['error']}")
        sys.exit(1)

    print("Benchmark concluído.")
    print(f"  Report: {REPORT_PATH}")
    print("  Baseline:", report.get("baseline", {}).get("metrics"))
    if report.get("finetuned"):
        print("  Fine-tuned:", report.get("finetuned", {}).get("metrics"))
        print("  Deltas %:", report.get("deltas_pct"))
        mrr_delta = report.get("mrr_improvement_pct")
        if mrr_delta is not None:
            pct = mrr_delta * 100.0
            ok = report.get("acceptance", False)
            print(f"  MRR melhoria: {pct:+.1f}%  →  {'ACEITO (>= 15%)' if ok else 'ABAIXO (meta >= 15%)'}")
        if report.get("recommendations"):
            print("  Recomendações:")
            for r in report["recommendations"]:
                print(f"    - {r}")
    else:
        print("  Fine-tuned: modelo não encontrado (rode scripts/finetune_embeddings.py).")

    if report.get("acceptance") is False and report.get("finetuned"):
        sys.exit(2)  # convenção: 2 = benchmark falhou (não atingiu 15%)
    sys.exit(0)
