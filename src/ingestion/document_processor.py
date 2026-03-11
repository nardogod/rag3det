from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from langchain_core.documents import Document

from src.ingestion.chunking import chunk_documents
from src.ingestion.text_cleaning import clean_documents
from src.types import DocumentList, SourceMetadata


logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessor:
    """
    Processa documentos de origem (páginas de PDF) em chunks prontos para indexação.

    Responsabilidades:
    - Detectar trechos que parecem tabelas e preservar a formatação (via `chunk_documents`).
    - Identificar headers/seções (ex.: "Magias", "Vantagens", "Monstros").
    - Enriquecer metadados com: `source`, `page`, `section_title`.
    """

    def process(self, documents: Iterable[Document]) -> DocumentList:
        """
        Executa a pipeline:
        1. Limpeza de texto.
        2. Chunking com preservação de tabelas.
        3. Enriquecimento de metadados.
        """
        logger.info("Iniciando processamento de documentos com DocumentProcessor.")

        cleaned_docs = clean_documents(documents)
        chunks = chunk_documents(cleaned_docs)

        for doc in chunks:
            meta: SourceMetadata = doc.metadata or {}
            # `section` já é inferido em `chunk_documents`; aqui padronizamos `section_title`.
            section = meta.get("section") or "Desconhecida"
            meta.setdefault("section_title", section)
            doc.metadata = meta

        logger.info("DocumentProcessor gerou %d chunks.", len(chunks))
        return chunks

