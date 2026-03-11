from __future__ import annotations

import logging
import re
from typing import Iterable, List, Tuple

from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.config import chunking_config
from src.types import DocumentList, SourceMetadata


logger = logging.getLogger(__name__)


SECTION_HEADER_RE = re.compile(
    r"^(Cap[ií]tulo\b.*|Magias\b.*|Vantagens\b.*|Desvantagens\b.*|Per[ií]cias\b.*|Monstros\b.*)",
    re.IGNORECASE,
)


def _is_table_line(line: str) -> bool:
    """Heurística simples para identificar linhas de tabela."""
    stripped = line.strip()
    if not stripped:
        return False
    if "|" in stripped:
        return True
    # Muitas colunas separadas por ponto e vírgula também são comuns em tabelas
    if stripped.count(";") >= 2:
        return True
    return False


def _preprocess_tables(text: str) -> str:
    """
    Agrupa blocos de linhas que parecem tabela para reduzir chance de corte no meio.

    Não evita 100% das quebras, mas já ajuda bastante.
    """
    lines = text.splitlines()
    blocks: List[str] = []

    current_block: List[str] = []
    current_is_table = False

    for line in lines:
        line_is_table = _is_table_line(line)

        if not current_block:
            current_block = [line]
            current_is_table = line_is_table
            continue

        # Continua no mesmo bloco se o "tipo" de linha não mudou
        if line_is_table == current_is_table:
            current_block.append(line)
        else:
            blocks.append("\n".join(current_block))
            current_block = [line]
            current_is_table = line_is_table

    if current_block:
        blocks.append("\n".join(current_block))

    return "\n\n".join(blocks)


def _infer_section_from_chunk(text: str, fallback: str | None = None) -> str:
    """
    Tenta identificar o título de seção mais relevante dentro de um chunk.
    """
    for line in text.splitlines():
        match = SECTION_HEADER_RE.match(line.strip())
        if match:
            return match.group(1).strip()
    return fallback or "Desconhecida"


def _build_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Cria um splitter recursivo razoável para textos de RPG.

    - `chunk_size` e `chunk_overlap` vêm de `chunking_config`
      (ajustável em `config/settings.yaml`).
    - São bons pontos de partida para respostas baseadas em regras,
      listas de vantagens, magias, etc.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunking_config.chunk_size,
        chunk_overlap=chunking_config.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_documents(documents: Iterable[Document]) -> DocumentList:
    """
    Divide documentos em chunks “inteligentes”:

    - Pré-processa linhas que parecem tabela para diminuir o risco de corte.
    - Usa `RecursiveCharacterTextSplitter` com sobreposição.
    - Tenta inferir uma seção aproximada para cada chunk (ex.: "Magias", "Vantagens").
    """
    splitter = _build_text_splitter()
    chunked_docs: DocumentList = []

    for doc in documents:
        meta: SourceMetadata = doc.metadata or {}

        preprocessed_text = _preprocess_tables(doc.page_content)
        raw_chunks = splitter.split_text(preprocessed_text)

        for chunk_text in raw_chunks:
            section = _infer_section_from_chunk(chunk_text, fallback=meta.get("section"))
            new_meta: SourceMetadata = {
                **meta,
                "section": section,
            }

            chunked_docs.append(
                Document(
                    page_content=chunk_text,
                    metadata=new_meta,
                )
            )

    logger.info(
        "Chunking concluído: %d documentos de entrada -> %d chunks",
        len(list(documents)),
        len(chunked_docs),
    )

    return chunked_docs

