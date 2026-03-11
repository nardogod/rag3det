"""
Infere propriedades (PM, PV, stats, escola, etc.) a partir dos contexts das entidades.

Uso (na raiz do projeto):
  python scripts/infer_properties.py
  python scripts/infer_properties.py --use-clean   # usa extracted_entities_clean.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths
from src.ml.inference.infer_properties import infer_properties_from_entities

ENTITIES_JSON = paths.data_dir / "entities" / "extracted_entities.json"
ENTITIES_CLEAN_JSON = paths.data_dir / "entities" / "extracted_entities_clean.json"
OUTPUT_JSON = paths.data_dir / "properties" / "entity_properties.json"


def main() -> None:
    use_clean = "--use-clean" in sys.argv
    input_path = ENTITIES_CLEAN_JSON if (use_clean and ENTITIES_CLEAN_JSON.exists()) else ENTITIES_JSON
    if not input_path.exists():
        print("Execute antes: python scripts/extract_entities.py (ou clean_entities.py para --use-clean)")
        sys.exit(1)
    out = infer_properties_from_entities(input_path, OUTPUT_JSON)
    print(f"Propriedades inferidas para {len(out)} entidades. Salvas em {OUTPUT_JSON}")
    for name, data in list(out.items())[:10]:
        print(f"  {name}: {data.get('properties', {})}")


if __name__ == "__main__":
    main()
