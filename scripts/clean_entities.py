"""
Aplica filtros de qualidade às entidades extraídas.

Uso (na raiz do projeto):
  python scripts/clean_entities.py

- Lê data/entities/extracted_entities.json
- Separa válidas vs suspeitas (entity_cleaner)
- Grava data/entities/extracted_entities_clean.json e data/entities/suspect_entities.json
- Exibe estatísticas
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from src.config import paths
from src.ml.ner.entity_cleaner import clean_entities

ENTITIES_DIR = paths.data_dir / "entities"
INPUT_JSON = ENTITIES_DIR / "extracted_entities.json"
OUTPUT_CLEAN = ENTITIES_DIR / "extracted_entities_clean.json"
OUTPUT_SUSPECT = ENTITIES_DIR / "suspect_entities.json"


def main() -> None:
    if not INPUT_JSON.exists():
        print(f"Arquivo não encontrado: {INPUT_JSON}")
        print("Execute antes: python scripts/extract_entities.py")
        sys.exit(1)
    with INPUT_JSON.open("r", encoding="utf-8") as f:
        entities = json.load(f)
    valid, suspect, stats = clean_entities(entities)
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CLEAN.open("w", encoding="utf-8") as f:
        json.dump(valid, f, ensure_ascii=False, indent=2)
    with OUTPUT_SUSPECT.open("w", encoding="utf-8") as f:
        json.dump(suspect, f, ensure_ascii=False, indent=2)
    print(f"Removidas {len(suspect)} entidades inválidas/suspeitas, mantidas {len(valid)} válidas.")
    print("Filtradas por: tamanho=%d, stopwords=%d, padrão=%d, substantivo=%d, contexto=%d" % (
        stats.get("tamanho", 0),
        stats.get("stopwords", 0),
        stats.get("padrão", 0),
        stats.get("substantivo", 0),
        stats.get("contexto", 0),
    ))
    print(f"  Válidas:   {OUTPUT_CLEAN}")
    print(f"  Suspeitas: {OUTPUT_SUSPECT}")
    print("Para revisar suspeitas: python scripts/validate_entities.py --review-suspects")


if __name__ == "__main__":
    main()
