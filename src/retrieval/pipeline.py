from __future__ import annotations

import hashlib
import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document

from src.config import retrieval_config
from src.retrieval.query_expansion import expand_query_variants
from src.retrieval.reranker import rerank_results_with_scores
from src.types import RetrievedChunk, SourceMetadata
from src.vectorstore.chroma_store import get_all_documents, get_vectorstore


logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize_for_bm25(text: str) -> List[str]:
    """Lista de tokens em minúsculas para BM25."""
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def _doc_key(doc: Document) -> str:
    """Chave estável para deduplicação (content + source + page)."""
    meta = doc.metadata or {}
    raw = (doc.page_content, meta.get("source"), meta.get("page"))
    return hashlib.sha256(str(raw).encode("utf-8")).hexdigest()


def _normalize_semantic_score(distance: float) -> float:
    """Converte distância do Chroma em score tipo similaridade (maior = melhor)."""
    return 1.0 / (1.0 + float(distance))


def _normalize_scores(scores: List[float]) -> List[float]:
    """Min-max normalização para [0, 1]; se todos iguais retorna 0.5."""
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi <= lo:
        return [0.5] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


@lru_cache(maxsize=1)
def _get_bm25_index() -> Tuple[Optional[object], List[Document]]:
    """
    Índice BM25 sobre todos os documentos do Chroma.
    Retorna (BM25Okapi ou None, lista de documentos na mesma ordem do corpus).
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 não instalado; busca híbrida usará só semântica.")
        return (None, [])

    all_docs = get_all_documents()
    if not all_docs:
        return (None, [])

    corpus = [_tokenize_for_bm25(d.page_content) for d in all_docs]
    bm25 = BM25Okapi(corpus)
    return (bm25, all_docs)


def _bm25_scores_for_query(
    query: str, bm25_index: object, doc_list: List[Document]
) -> List[Tuple[Document, float]]:
    """Scores BM25 da query para cada documento (mesma ordem que doc_list)."""
    tokenized = _tokenize_for_bm25(query)
    scores = bm25_index.get_scores(tokenized)
    return [(doc, float(s)) for doc, s in zip(doc_list, scores)]


def retrieve_relevant_chunks(
    query: str,
    k: Optional[int] = None,
    use_baseline: bool = False,
) -> List[RetrievedChunk]:
    """
    Ponto de entrada único para buscar trechos relevantes nos livros 3D&T.

    - use_baseline: se True, usa índice com embedding genérico (para A/B test).
    """
    final_k = k if k is not None else retrieval_config.k
    candidate_k = retrieval_config.candidate_k
    use_hybrid = retrieval_config.hybrid_enabled
    use_expansion = retrieval_config.query_expansion_enabled
    use_rerank = retrieval_config.reranking_enabled

    if use_expansion:
        queries = expand_query_variants(query)
    else:
        queries = [query.strip()]

    vectorstore = get_vectorstore(use_baseline=use_baseline)

    # Mapa: doc_key -> (doc, best_semantic, best_bm25)
    aggregated: Dict[str, Tuple[Document, float, float]] = {}

    for q in queries:
        if not q:
            continue
        # Semântica: top candidate_k por variante
        try:
            sem_results = vectorstore.similarity_search_with_score(q, k=candidate_k)
        except Exception as e:
            logger.warning("Falha na busca semântica para %r: %s", q[:50], e)
            sem_results = []

        for doc, distance in sem_results:
            key = _doc_key(doc)
            sim = _normalize_semantic_score(distance)
            if key not in aggregated:
                aggregated[key] = (doc, sim, 0.0)
            else:
                old_doc, old_sem, old_bm25 = aggregated[key]
                aggregated[key] = (old_doc, max(old_sem, sim), old_bm25)

        # BM25 (se híbrido e índice disponível)
        if use_hybrid:
            bm25_obj, doc_list = _get_bm25_index()
            if bm25_obj is not None and doc_list:
                bm25_pairs = _bm25_scores_for_query(q, bm25_obj, doc_list)
                # Top candidate_k por BM25
                bm25_pairs.sort(key=lambda x: x[1], reverse=True)
                for doc, score in bm25_pairs[:candidate_k]:
                    key = _doc_key(doc)
                    if key not in aggregated:
                        aggregated[key] = (doc, 0.0, score)
                    else:
                        old_doc, old_sem, old_bm25 = aggregated[key]
                        aggregated[key] = (old_doc, old_sem, max(old_bm25, score))

    if not aggregated:
        logger.warning("Nenhum candidato agregado para a pergunta.")
        return []

    # Ordenar por combinação de scores
    doc_list_ordered = list(aggregated.values())
    sem_vals = [x[1] for x in doc_list_ordered]
    bm25_vals = [x[2] for x in doc_list_ordered]
    norm_sem = _normalize_scores(sem_vals)
    norm_bm25 = _normalize_scores(bm25_vals) if use_hybrid else [0.0] * len(doc_list_ordered)
    w_sem = retrieval_config.hybrid_semantic_weight
    w_bm25 = retrieval_config.hybrid_bm25_weight if use_hybrid else 0.0
    combined = [
        (doc, w_sem * ns + w_bm25 * nb)
        for (doc, _, _), ns, nb in zip(doc_list_ordered, norm_sem, norm_bm25)
    ]
    combined.sort(key=lambda x: x[1], reverse=True)

    # Limitar candidatos antes do rerank
    candidates_for_rerank = [doc for doc, _ in combined[: candidate_k * 2]]
    scores_before = [s for _, s in combined[: len(candidates_for_rerank)]]

    # Reranking (ou pular se fast_mode)
    if use_rerank:
        reranked_with_scores = rerank_results_with_scores(
            query, candidates_for_rerank, top_k=final_k
        )
        if scores_before and reranked_with_scores:
            logger.info(
                "Scores ANTES (combined): top5 = %s",
                [round(s, 4) for s in scores_before[:5]],
            )
            logger.info(
                "Scores DEPOIS (cross-encoder): top%d = %s",
                len(reranked_with_scores),
                [round(s, 4) for _, s in reranked_with_scores],
            )
    else:
        reranked_with_scores = [
            (doc, float(score))
            for doc, score in combined[:final_k]
        ]

    chunks: List[RetrievedChunk] = []
    for doc, score in reranked_with_scores:
        meta: SourceMetadata = doc.metadata or {}
        chunks.append(
            RetrievedChunk(content=doc.page_content, metadata=meta, score=float(score))
        )

    logger.info(
        "Retorno: %d chunks (candidatos agregados: %d, após rerank top %d).",
        len(chunks),
        len(aggregated),
        final_k,
    )
    return chunks
