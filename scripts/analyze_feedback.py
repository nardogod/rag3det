"""
Script para analisar o feedback salvo em data/feedback.db.

Uso:
  python scripts/analyze_feedback.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que o pacote `src` seja encontrado quando o script é chamado diretamente
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.feedback_loop import analyze_feedback


def main() -> None:
    stats = analyze_feedback()
    print("Total de queries avaliadas:", stats.get("total_entries", 0))
    print("\nQueries com menor satisfação (rating médio < 0):")
    for item in stats.get("low_satisfaction_queries", []):
        print(
            f"- {item['query']}  | média={item['avg_rating']:.2f}  "
            f"(n={item['count']})"
        )


if __name__ == "__main__":
    main()

