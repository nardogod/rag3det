from __future__ import annotations

import logging
import re
from typing import Iterable

from langchain_core.documents import Document

from src.types import DocumentList


logger = logging.getLogger(__name__)

_MULTIPLE_SPACES_RE = re.compile(r"[ \t]{2,}")
_BROKEN_HYPHEN_RE = re.compile(r"(\w+)-\n(\w+)")


def _clean_text(text: str) -> str:
    """
    Aplica limpezas simples que já ajudam bastante em PDFs de livros de RPG.

    - Junta palavras quebradas por hífen no fim da linha.
    - Normaliza espaços em branco.
    - Remove espaços extras no início/fim.
    """
    # Junta "magia-\nelemental" -> "magiaelemental"
    text = _BROKEN_HYPHEN_RE.sub(r"\1\2", text)

    # Normaliza múltiplos espaços em branco para um só (preservando quebras de linha)
    lines = [line.rstrip() for line in text.splitlines()]
    normalized_lines = [_MULTIPLE_SPACES_RE.sub(" ", line) for line in lines]

    cleaned = "\n".join(normalized_lines).strip()
    return cleaned


def clean_documents(documents: Iterable[Document]) -> DocumentList:
    """
    Limpa uma lista de Documents.

    - Se você quiser adicionar mais regras de limpeza específicas para 3D&T,
      este é o melhor lugar para fazê-lo.
    """
    cleaned_docs: DocumentList = []

    for doc in documents:
        original_len = len(doc.page_content)
        doc.page_content = _clean_text(doc.page_content)
        cleaned_len = len(doc.page_content)

        logger.debug(
            "Documento limpo (source=%s, page=%s, %d -> %d caracteres)",
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            original_len,
            cleaned_len,
        )

        cleaned_docs.append(doc)

    logger.info("Limpeza concluída para %d documentos", len(cleaned_docs))
    return cleaned_docs

