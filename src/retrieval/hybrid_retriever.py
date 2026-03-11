"""
Pipeline explícito: Vector Retrieval (20 docs) → Reranking → Top 5.

- Opcional: expansão por grafo (entidades + relações + cluster) e agregação com peso.
- Log de scores para análise (evitar Fênix → Solar/Pégaso).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Dict, List, Tuple

from langchain_core.documents import Document

from src.retrieval.graph_expansion import expand_query_with_graph
from src.retrieval.reranker import CrossEncoderReranker
from src.types import RetrievedChunk, SourceMetadata
from src.vectorstore.chroma_store import get_vectorstore


logger = logging.getLogger(__name__)

VECTOR_K = 20
TOP_K = 5


def _distance_to_similarity(distance: float) -> float:
    """Converte distância Chroma em score tipo similaridade (maior = melhor)."""
    return 1.0 / (1.0 + float(distance))


def _doc_key(doc: Document) -> str:
    meta = doc.metadata or {}
    raw = (doc.page_content, meta.get("source"), meta.get("page"))
    return hashlib.sha256(str(raw).encode("utf-8")).hexdigest()


def hybrid_retrieve(
    query: str,
    vector_k: int = VECTOR_K,
    top_k: int = TOP_K,
    use_graph_expansion: bool = False,
) -> List[RetrievedChunk]:
    """
    Pipeline: Vector Retrieval (vector_k docs) → Reranking → Top top_k.

    Se use_graph_expansion=True, expande a query com o grafo (entidades, relações, cluster),
    busca cada termo com peso e agrega resultados antes do rerank.
    """
    vectorstore = get_vectorstore()
    if use_graph_expansion:
        weighted_terms = expand_query_with_graph(query, max_terms=5)
        aggregated: Dict[str, Tuple[Document, float]] = {}
        for term, weight in weighted_terms:
            try:
                raw = vectorstore.similarity_search_with_score(term, k=vector_k)
            except Exception as e:
                logger.debug("Falha na busca para %r: %s", term[:30], e)
                continue
            for doc, dist in raw:
                key = _doc_key(doc)
                sim = _distance_to_similarity(dist) * weight
                if key not in aggregated or aggregated[key][1] < sim:
                    aggregated[key] = (doc, sim)
        if not aggregated:
            docs = []
            scores_before = []
        else:
            sorted_docs = sorted(aggregated.values(), key=lambda x: -x[1])
            docs = [d for d, _ in sorted_docs[:vector_k]]
            scores_before = [s for _, s in sorted_docs[:vector_k]]
    else:
        try:
            raw = vectorstore.similarity_search_with_score(query, k=vector_k)
        except Exception as e:
            logger.exception("Falha na busca vetorial: %s", e)
            return []
        docs = [doc for doc, _ in raw]
        scores_before = [_distance_to_similarity(dist) for _, dist in raw]

    if not docs:
        return []

    logger.info(
        "Scores ANTES (vector retrieval, top %d): %s",
        min(5, len(scores_before)),
        [round(s, 4) for s in scores_before[:5]],
    )

    reranker = CrossEncoderReranker()
    scored = reranker.rerank(query, docs, top_k=top_k)
    scores_after = [s for _, s in scored]

    logger.info(
        "Scores DEPOIS (cross-encoder rerank, top %d): %s",
        len(scores_after),
        [round(s, 4) for s in scores_after],
    )

    chunks: List[RetrievedChunk] = []
    for doc, score in scored:
        meta: SourceMetadata = doc.metadata or {}
        chunks.append(RetrievedChunk(content=doc.page_content, metadata=meta, score=float(score)))
    return chunks
