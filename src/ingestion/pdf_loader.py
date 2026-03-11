from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from pypdf.errors import PdfReadError

from src.config import paths
from src.types import DocumentList, SourceMetadata

# Fallback opcional: se pymupdf estiver instalado, usamos para PDFs que o pypdf não consegue ler
try:
    from langchain_community.document_loaders import PyMuPDFLoader
except ImportError:
    PyMuPDFLoader = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


def _normalize_book_title_from_path(path: Path) -> str:
    """
    Gera um nome de livro legível a partir do nome do arquivo.

    Ex.: "3det_alpha_magias.pdf" -> "3det alpha magias".
    """
    stem = path.stem.replace("_", " ").replace("-", " ").strip()
    return stem or path.name


def _enrich_metadata(docs: Iterable[Document]) -> DocumentList:
    """Adiciona metadados padronizados (book_title, content_type, etc.)."""
    enriched: DocumentList = []

    for doc in docs:
        meta: SourceMetadata = {}
        raw_meta = dict(doc.metadata or {})

        source_path = Path(raw_meta.get("source", raw_meta.get("file_path", "")))

        meta["source"] = str(source_path.name or raw_meta.get("source", "desconhecido"))
        meta["page"] = int(raw_meta.get("page", raw_meta.get("page_number", 0)) or 0)
        meta["book_title"] = _normalize_book_title_from_path(source_path)

        # Campo opcional – será melhor preenchido na etapa de chunking
        meta.setdefault("section", "Desconhecida")
        meta.setdefault("content_type", "texto")

        doc.metadata = {**raw_meta, **meta}
        enriched.append(doc)

    return enriched


def load_pdfs_from_source_dir(source_dir: Path | None = None) -> DocumentList:
    """
    Carrega todos os PDFs do diretório configurado e devolve uma lista de Documents.

    - PDFs que falharem (malformados, stream truncado, etc.) são ignorados com um
      aviso no log; o restante é processado normalmente.
    - Se você quiser apontar para outro diretório manualmente, passe `source_dir`.
    """
    pdf_dir = Path(source_dir) if source_dir is not None else paths.source_pdf_dir

    if not pdf_dir.exists():
        logger.warning("Diretório de PDFs não existe: %s", pdf_dir)
        return []

    logger.info("Carregando PDFs a partir de: %s", pdf_dir)

    pdf_files = sorted(pdf_dir.rglob("*.pdf"))
    if not pdf_files:
        logger.warning("Nenhum arquivo .pdf encontrado em %s", pdf_dir)
        return []

    all_docs: DocumentList = []
    skipped = 0

    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            all_docs.extend(docs)
        except (PdfReadError, Exception) as e:
            # Fallback: tentar PyMuPDF (mais tolerante a streams truncados / PDFs malformados)
            if PyMuPDFLoader is not None:
                try:
                    loader_fallback = PyMuPDFLoader(str(pdf_path))
                    docs = loader_fallback.load()
                    all_docs.extend(docs)
                    logger.info("PDF lido com PyMuPDF (fallback): %s", pdf_path.name)
                except Exception as e2:
                    logger.warning(
                        "PDF ignorado (pypdf e PyMuPDF falharam): %s — %s | %s",
                        pdf_path.name, e, e2,
                    )
                    skipped += 1
            else:
                logger.warning("PDF ignorado (erro de leitura): %s — %s", pdf_path.name, e)
                skipped += 1

    if skipped:
        logger.info("Total de PDFs ignorados por erro: %d", skipped)

    logger.info("Carregados %d documentos (páginas) de PDF", len(all_docs))

    enriched_docs = _enrich_metadata(all_docs)

    if enriched_docs:
        logger.debug("Exemplo de metadados: %s", enriched_docs[0].metadata)

    return enriched_docs

