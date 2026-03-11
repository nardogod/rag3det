from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Iterable, List, Tuple

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from src.config import retrieval_config, paths


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

FINETUNED_PATH = paths.project_root / "models" / "reranker" / "3dt_finetuned"

_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Prefixos comuns de pergunta em PT-BR; ao rerankar, usamos o resto como "frase chave"
_QUERY_PREFIXES = (
    "o que é ",
    "o que e ",
    "o que o ",
    "o que a ",
    "o que os ",
    "o que as ",
    "como funciona ",
    "quais ",
    "qual ",
    "quem é ",
    "quem e ",
    "explique ",
    "o que são ",
    "o que sao ",
)


def _tokenize(text: str) -> set[str]:
    """Tokeniza um texto em palavras minúsculas (heurística bem simples)."""
    return {m.group(0).lower() for m in _WORD_RE.finditer(text)}


def _normalize_for_phrase(s: str) -> str:
    """Minúsculas, sem pontuação extra, espaços colapsados. Normaliza • e · para espaço."""
    s = s.lower().strip()
    for c in "?.!,•·—()":
        s = s.replace(c, " ")
    return " ".join(s.split())


def _key_phrase_from_query(query: str) -> str:
    """
    Extrai a parte da pergunta que provavelmente é o "nome" do que se busca
    (ex.: "O que é Invocação da Fênix?" -> "invocação da fênix").
    """
    key = _normalize_for_phrase(query)
    for prefix in _QUERY_PREFIXES:
        if key.startswith(prefix):
            key = key[len(prefix) :].strip()
            break
    return key


class CrossEncoderReranker:
    """
    Re-ranking por relevância real (query, documento) com cross-encoder.

    Modelo: ms-marco-MiniLM-L-6-v2 (leve, roda local com sentence-transformers).
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, max_length: int = 512):
        self.model_name = model_name
        self.max_length = max_length
        self._model: CrossEncoder | None = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            logger.info("Carregando cross-encoder para reranking: %s", self.model_name)
            self._model = CrossEncoder(self.model_name, max_length=self.max_length)
        return self._model

    def rerank(
        self,
        query: str,
        docs: List[Document],
        top_k: int = 5,
    ) -> List[Tuple[Document, float]]:
        """
        Reordena documentos por score de relevância (query, doc) e retorna top_k.

        Retorna lista de (Document, score) em ordem decrescente de relevância.
        """
        if not docs:
            return []
        if len(docs) <= 1:
            return [(d, 1.0) for d in docs]

        pairs = [[query, doc.page_content] for doc in docs]
        try:
            scores = self.model.predict(pairs)
        except Exception as e:
            logger.exception("Falha ao aplicar cross-encoder: %s", e)
            return [(doc, 0.0) for doc in docs]

        scored = list(zip(docs, [float(s) for s in scores]))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoderReranker:
    model_name: str
    if FINETUNED_PATH.exists():
        model_name = str(FINETUNED_PATH)
        logger.info("Usando reranker fine-tuned em %s", model_name)
    else:
        model_name = DEFAULT_MODEL
        logger.info("Usando reranker baseline genérico: %s", model_name)
    return CrossEncoderReranker(model_name=model_name, max_length=512)


def rerank_results(query: str, docs: Iterable[Document]) -> List[Document]:
    """
    Reordena os resultados de acordo com a relevância estimada para a pergunta.

    - Se `RERANKING_ENABLED=false`, apenas retorna na ordem original.
    - Se `true`, usa CrossEncoderReranker para pontuar (query, chunk) e ordenar.
    """
    docs_list = list(docs)

    if not retrieval_config.reranking_enabled or len(docs_list) <= 1:
        logger.info(
            "Reranking desabilitado ou lista com poucos docs. Mantendo ordem original (%d docs).",
            len(docs_list),
        )
        return docs_list

    reranker = _get_reranker()
    top_k = len(docs_list)  # reordenar todos
    scored = reranker.rerank(query, docs_list, top_k=top_k)
    reranked_docs = [doc for doc, _ in scored]
    logger.info(
        "Reranking via cross-encoder concluído. %d documentos reordenados.", len(reranked_docs)
    )
    return reranked_docs


def rerank_results_with_scores(
    query: str, docs: Iterable[Document], top_k: int | None = None
) -> List[Tuple[Document, float]]:
    """
    Igual a rerank_results, mas retorna (Document, score) para logging/comparação.
    """
    docs_list = list(docs)
    if not docs_list:
        return []
    k = top_k if top_k is not None else len(docs_list)
    if not retrieval_config.reranking_enabled or len(docs_list) <= 1:
        return [(d, 0.5) for d in docs_list[:k]]

    reranker = _get_reranker()
    return reranker.rerank(query, docs_list, top_k=k)

