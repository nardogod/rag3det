"""
Constrói o grafo de relações a partir das entidades extraídas.

Uso (na raiz do projeto):
  python scripts/build_knowledge_graph.py

- Lê data/entities/extracted_entities.json (ou extracted_entities_clean.json com --use-clean)
- Extrai relações (is_a, cost, requires, element, etc.) dos contexts
- Salva data/knowledge_graph/relations.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths
from src.ml.knowledge_graph.build_graph import build_relations

ENTITIES_JSON = paths.data_dir / "entities" / "extracted_entities.json"
ENTITIES_CLEAN_JSON = paths.data_dir / "entities" / "extracted_entities_clean.json"
OUTPUT_JSON = paths.data_dir / "knowledge_graph" / "relations.json"


def main() -> None:
    use_clean = "--use-clean" in sys.argv
    input_path = ENTITIES_CLEAN_JSON if (use_clean and ENTITIES_CLEAN_JSON.exists()) else ENTITIES_JSON
    if not input_path.exists():
        print("Execute antes: python scripts/extract_entities.py (ou clean_entities.py para --use-clean)")
        print(f"Arquivo esperado: {input_path}")
        sys.exit(1)
    relations = build_relations(input_path, OUTPUT_JSON)
    print(f"Relações extraídas: {len(relations)}. Salvas em {OUTPUT_JSON}")
    for r in relations[:10]:
        print(f"  {r['source']} --{r['relation']}--> {r['target']}")


if __name__ == "__main__":
    main()
