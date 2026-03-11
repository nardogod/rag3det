"""
Avalia a qualidade do conhecimento extraído e gera data/quality_report.json.

Uso (na raiz do projeto):
  python scripts/evaluate_knowledge.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths
from src.evaluation.knowledge_quality import evaluate_knowledge, save_quality_report

OUTPUT_JSON = paths.data_dir / "quality_report.json"


def main() -> None:
    print("Avaliando qualidade do conhecimento...")
    report = evaluate_knowledge()
    path = save_quality_report(report, OUTPUT_JSON)
    print(f"Relatório salvo em {path}")
    print(f"  Total entidades: {report.get('total_entities', 0)}")
    print(f"  Suspeitas: {report.get('suspect_entities', 0)}")
    print(f"  Coverage propriedades: {report.get('properties_coverage', {})}")
    print(f"  Isoladas (amostra): {report.get('top_isolated_entities', [])[:5]}")
    recs = report.get("recommendations", [])
    if recs:
        print("  Recomendações:")
        for r in recs[:5]:
            print(f"    - {r}")
    if report.get("precision_heuristic", 0) < 0.7:
        print("  ALERTA: precision heurística abaixo de 0.7")


if __name__ == "__main__":
    main()
