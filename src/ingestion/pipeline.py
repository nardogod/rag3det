from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.config import paths
from src.ingestion.document_processor import DocumentProcessor
from src.ingestion.pdf_loader import load_pdfs_from_source_dir
from src.logging_config import setup_logging
from src.types import DocumentList


logger = logging.getLogger(__name__)


def _ensure_directories() -> None:
    """
    Garante que as pastas de dados existem.

    - Se você quer usar outro caminho para os PDFs,
      ajuste `SOURCE_PDF_DIR` no `.env` ou `paths.source_pdf_dir` em `config.py`.
    """
    for p in (paths.data_dir, paths.raw_data_dir, Path(paths.chroma_dir)):
        p.mkdir(parents=True, exist_ok=True)


def run_ingestion(source_dir: Optional[Path] = None) -> DocumentList:
    """
    Roda a pipeline completa de ingestão:

    1. Garante que as pastas de dados existem.
    2. Carrega PDFs em `source_dir` (se informado) ou `paths.source_pdf_dir`.
    3. Processa com `DocumentProcessor` (limpeza, tabelas, seções, metadados).

    Retorna a lista de chunks (`Document`s) prontos para gerar embeddings.

    - Se você quer apenas chamar “faça toda a ingestão” de outro lugar (scripts,
      interface Streamlit), chame **esta função**.
    """
    setup_logging()
    logger.info("Iniciando pipeline de ingestão 3D&T")

    _ensure_directories()

    docs = load_pdfs_from_source_dir(source_dir=source_dir)
    if not docs:
        logger.warning(
            "Nenhum documento PDF carregado. "
            "Verifique se o diretório %s contém arquivos .pdf",
            source_dir if source_dir is not None else paths.source_pdf_dir,
        )
        return []

    processor = DocumentProcessor()
    chunks = processor.process(docs)

    logger.info("Pipeline de ingestão concluída. Total de chunks: %d", len(chunks))

    return chunks


if __name__ == "__main__":
    # Execução direta para teste rápido:
    result = run_ingestion()
    print(f"Ingestão concluída. Total de chunks: {len(result)}")

