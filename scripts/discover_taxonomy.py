"""
Descobre taxonomia automática (clusters de entidades) por TF-IDF + K-Means.

Uso (na raiz do projeto):
  python scripts/discover_taxonomy.py
  python scripts/discover_taxonomy.py --clean   # usa extracted_entities_clean.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths
from src.ml.taxonomy.discover_types import discover_taxonomy

ENTITIES_JSON = paths.data_dir / "entities" / "extracted_entities.json"
ENTITIES_CLEAN_JSON = paths.data_dir / "entities" / "extracted_entities_clean.json"
OUTPUT_JSON = paths.data_dir / "taxonomy" / "auto_taxonomy.json"


def main() -> None:
    use_clean = "--clean" in sys.argv
    input_path = ENTITIES_CLEAN_JSON if (use_clean and ENTITIES_CLEAN_JSON.exists()) else ENTITIES_JSON
    if not input_path.exists():
        print("Execute antes: python scripts/extract_entities.py (ou clean_entities.py para --clean)")
        sys.exit(1)
    try:
        out = discover_taxonomy(input_path, OUTPUT_JSON, n_clusters=10)
    except ImportError as e:
        print("Instale scikit-learn: pip install scikit-learn")
        sys.exit(1)
    print(f"Clusters: {len(out.get('clusters', {}))}. Salvo em {OUTPUT_JSON}")
    for cid, c in list(out.get("clusters", {}).items())[:5]:
        terms = c.get("terms", c.get("common_terms", []))[:5]
        print(f"  {cid}: {len(c['entities'])} entidades, termos: {terms}")


if __name__ == "__main__":
    main()
