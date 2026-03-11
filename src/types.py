from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict

from langchain_core.documents import Document


class SourceMetadata(TypedDict, total=False):
    """Metadados básicos anexados a cada chunk/documento."""

    source: str
    page: int
    book_title: str
    section: str
    section_title: str
    content_type: str  # ex.: "regra", "magia", "vantagem", "monstro", "tabela"


DocumentList = List[Document]
Metadata = Dict[str, Any]


@dataclass
class RetrievedChunk:
    """Representa um trecho recuperado para compor a resposta do LLM."""

    content: str
    metadata: SourceMetadata
    score: float | None = None


@dataclass
class QAResult:
    """Resposta final do RAG: texto gerado pelo LLM + fontes usadas."""

    answer: str
    sources: List[SourceMetadata]

