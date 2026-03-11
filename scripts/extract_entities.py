"""
Extrai entidades 3D&T do corpus e gera data/entities/extracted_entities.json.

Uso (na raiz do projeto):
  python scripts/extract_entities.py

- Se data/processed/chunks.json existir, usa esses chunks.
- Caso contrário, roda ingestão (PDFs → chunks) e opcionalmente salva em data/processed/.
- min_mentions por tipo (MAGIA 2, MONSTRO 4, ITEM 3, DESCONHECIDO 10); críticas sempre mantidas.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths
from src.ingestion.pipeline import run_ingestion
from src.ml.ner.extract_entities_from_corpus import (
    load_chunks_from_processed_dir,
    run_extraction,
)

DATA_PROCESSED = paths.data_dir / "processed"
ENTITIES_DIR = paths.data_dir / "entities"
OUTPUT_JSON = ENTITIES_DIR / "extracted_entities.json"
MIN_MENTIONS = 4


def main() -> None:
    print("Extração de entidades 3D&T do corpus...")
    chunks = load_chunks_from_processed_dir(DATA_PROCESSED)
    if not chunks:
        print("data/processed/chunks.json não encontrado. Rodando ingestão a partir dos PDFs...")
        chunks = run_ingestion()
        if not chunks:
            print("Nenhum chunk gerado. Verifique SOURCE_PDF_DIR e os PDFs.")
            sys.exit(1)
        print(f"Chunks gerados: {len(chunks)}. Salvando em data/processed/ para próxima vez...")
    else:
        print(f"Carregados {len(chunks)} chunks de data/processed/.")
    entities = run_extraction(
        chunks,
        OUTPUT_JSON,
        min_mentions=MIN_MENTIONS,
        save_chunks_path=DATA_PROCESSED if not (DATA_PROCESSED / "chunks.json").exists() else None,
    )
    print(f"Entidades extraídas: {len(entities)}. Salvas em {OUTPUT_JSON}")
    for name, data in sorted(entities.items(), key=lambda x: -x[1]["mentions"])[:15]:
        print(f"  - {name}: {data['type']} ({data['mentions']} menções)")


if __name__ == "__main__":
    main()
