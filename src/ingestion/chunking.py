from __future__ import annotations

import logging
import re
from typing import Iterable, List

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


def _split_large_piece(piece: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Divide um bloco maior que `chunk_size` usando cortes simples com overlap.

    Mantemos esta lógica local para evitar dependências pesadas no runtime
    do Streamlit Cloud.
    """
    if len(piece) <= chunk_size:
        return [piece]

    chunks: List[str] = []
    start = 0
    step = max(1, chunk_size - chunk_overlap)

    while start < len(piece):
        end = min(len(piece), start + chunk_size)
        chunk = piece[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(piece):
            break
        start += step

    return chunks


def _split_text_recursively(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: List[str],
) -> List[str]:
    """
    Splitter local inspirado no comportamento do RecursiveCharacterTextSplitter.
    """
    clean_text = text.strip()
    if not clean_text:
        return []
    if len(clean_text) <= chunk_size:
        return [clean_text]

    if not separators:
        return _split_large_piece(clean_text, chunk_size, chunk_overlap)

    separator = separators[0]
    remainder = separators[1:]

    if separator == "":
        return _split_large_piece(clean_text, chunk_size, chunk_overlap)

    pieces = clean_text.split(separator)
    if len(pieces) == 1:
        return _split_text_recursively(clean_text, chunk_size, chunk_overlap, remainder)

    chunks: List[str] = []
    current = ""

    for piece in pieces:
        candidate = piece if not current else current + separator + piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.extend(_split_text_recursively(current, chunk_size, chunk_overlap, remainder))

        if len(piece) <= chunk_size:
            current = piece
        else:
            chunks.extend(_split_text_recursively(piece, chunk_size, chunk_overlap, remainder))
            current = ""

    if current:
        chunks.extend(_split_text_recursively(current, chunk_size, chunk_overlap, remainder))

    # Remove duplicatas vazias e reaplica overlap simples entre chunks vizinhos.
    filtered = [chunk.strip() for chunk in chunks if chunk.strip()]
    if not filtered or chunk_overlap <= 0:
        return filtered

    with_overlap: List[str] = [filtered[0]]
    for chunk in filtered[1:]:
        previous_tail = with_overlap[-1][-chunk_overlap:].strip()
        if previous_tail and not chunk.startswith(previous_tail):
            merged = f"{previous_tail} {chunk}".strip()
            with_overlap.append(merged[:chunk_size])
        else:
            with_overlap.append(chunk)
    return with_overlap


def chunk_documents(documents: Iterable[Document]) -> DocumentList:
    """
    Divide documentos em chunks “inteligentes”:

    - Pré-processa linhas que parecem tabela para diminuir o risco de corte.
    - Usa `RecursiveCharacterTextSplitter` com sobreposição.
    - Tenta inferir uma seção aproximada para cada chunk (ex.: "Magias", "Vantagens").
    """
    chunked_docs: DocumentList = []
    source_docs = list(documents)
    separators = ["\n\n", "\n", ". ", " ", ""]

    for doc in source_docs:
        meta: SourceMetadata = doc.metadata or {}

        preprocessed_text = _preprocess_tables(doc.page_content)
        raw_chunks = _split_text_recursively(
            preprocessed_text,
            chunk_size=chunking_config.chunk_size,
            chunk_overlap=chunking_config.chunk_overlap,
            separators=separators,
        )

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
        len(source_docs),
        len(chunked_docs),
    )

    return chunked_docs

