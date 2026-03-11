"""
Carrega modelo de embeddings fine-tuned (caminho local) ou fallback.

- Tenta primeiro o modelo em EMBEDDING_MODEL (ex.: models/embeddings/3dt_finetuned/).
- Se falhar (não existe ou corrompido), usa EMBEDDING_FALLBACK com warning.
- Modelo em cache em memória (não recarrega a cada query).
- Opcional: normalização L2 no pipeline (fallback se o modelo não retornar norma 1).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import embedding_config, paths

logger = logging.getLogger(__name__)


def normalize_l2(embeddings: List[List[float]]) -> List[List[float]]:
    """L2-normaliza embeddings (norma 1 por vetor). Evita div por zero."""
    import numpy as np
    arr = np.asarray(embeddings, dtype=np.float64)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms < 1e-8, 1.0, norms)
    out = (arr / norms).tolist()
    return out


def _normalize_l2_single(vec: List[float]) -> List[float]:
    import numpy as np
    arr = np.asarray(vec, dtype=np.float64)
    norm = np.linalg.norm(arr)
    if norm < 1e-8:
        return vec
    return (arr / norm).tolist()


class NormalizedEmbeddings(Embeddings):
    """Wrapper que aplica L2-normalização aos embeddings (fallback se o modelo não normalizar)."""

    def __init__(self, underlying: Embeddings):
        self._underlying = underlying

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        emb = self._underlying.embed_documents(texts)
        return normalize_l2(emb)

    def embed_query(self, text: str) -> List[float]:
        vec = self._underlying.embed_query(text)
        return _normalize_l2_single(vec)

# Modelo efetivamente carregado (path ou nome) para cache de disco.
_effective_model_id: Optional[str] = None


def _resolve_model_path() -> Optional[Path]:
    """Retorna path absoluto do modelo fine-tuned se existir e for válido."""
    raw = embedding_config.embedding_model
    if not raw or not raw.strip():
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = paths.project_root / p
    config_file = p / "config_sentence_transformers.json"
    if config_file.exists():
        return p
    return None


def _get_embeddings_model_uncached() -> Embeddings:
    """Carrega o modelo (fine-tuned ou fallback) sem usar cache de função."""
    global _effective_model_id
    model_path = _resolve_model_path()
    fallback = embedding_config.embedding_fallback

    if model_path is not None:
        try:
            model_name_or_path = str(model_path)
            logger.info("Carregando embeddings fine-tuned: %s", model_name_or_path)
            emb = HuggingFaceEmbeddings(
                model_name=model_name_or_path,
                model_kwargs={"local_files_only": True},
                show_progress=False,
            )
            _effective_model_id = model_name_or_path
            # Garantir L2 no pipeline (idempotente se o modelo já normalizar)
            return NormalizedEmbeddings(emb)
        except Exception as e:
            logger.warning(
                "Falha ao carregar modelo fine-tuned %s: %s. Usando fallback: %s",
                model_path,
                e,
                fallback,
            )

    logger.info("Usando embeddings fallback: %s", fallback)
    _effective_model_id = fallback
    return HuggingFaceEmbeddings(model_name=fallback, show_progress=False)


@lru_cache(maxsize=1)
def get_embeddings_model() -> Embeddings:
    """
    Retorna o modelo de embeddings (fine-tuned se disponível, senão fallback).
    Resultado em cache em memória (não recarrega a cada query).
    """
    return _get_embeddings_model_uncached()


def get_effective_embedding_model_id() -> str:
    """Retorna o identificador do modelo atualmente em uso (para cache de disco)."""
    if _effective_model_id is not None:
        return _effective_model_id
    # Força carregamento uma vez para preencher _effective_model_id
    get_embeddings_model()
    return _effective_model_id or embedding_config.embedding_fallback


@lru_cache(maxsize=1)
def get_baseline_embeddings_model() -> Embeddings:
    """Sempre retorna o modelo fallback (genérico), para A/B test ou índice baseline."""
    return HuggingFaceEmbeddings(
        model_name=embedding_config.embedding_fallback,
        show_progress=False,
    )
