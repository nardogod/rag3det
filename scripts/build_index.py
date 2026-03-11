"""
Script para (re)construir o índice vetorial a partir dos PDFs.

Execute na raiz do projeto:
  python scripts/build_index.py

- Roda ingestão (carregar PDFs → limpar → chunkar) e depois indexa no Chroma.
- Use após adicionar novos PDFs ou quando quiser recriar o índice do zero.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.pipeline import run_ingestion
from src.vectorstore.chroma_store import build_or_update_vectorstore
from ml.ner.model_integration import enrich_documents_with_ner


def main() -> None:
    print("Iniciando build do índice 3D&T...")
    chunks = run_ingestion()
    if not chunks:
        print("Nenhum documento foi ingerido. Verifique SOURCE_PDF_DIR e se há PDFs no diretório.")
        sys.exit(1)
    print(f"Chunks gerados: {len(chunks)}. Rodando NER para enriquecer metadados...")
    chunks = enrich_documents_with_ner(chunks)
    print("Indexando no Chroma...")
    build_or_update_vectorstore(chunks)
    print("Índice construído com sucesso.")


if __name__ == "__main__":
    main()
