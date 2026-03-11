from __future__ import annotations

from functools import lru_cache
from langchain_core.embeddings import Embeddings

from src.embedding.cached_embeddings import CachedEmbeddings
from src.embedding.local_embeddings import (
    get_embeddings_model,
    get_effective_embedding_model_id,
    get_baseline_embeddings_model,
)


@lru_cache(maxsize=1)
def get_embedding_function() -> Embeddings:
    """
    Ponto de acesso para a função de embedding (com cache em disco).

    - Usa modelo fine-tuned (models/embeddings/3dt_finetuned/) se existir; senão fallback.
    - Persiste embeddings em `data/embedding_cache` por modelo (evita recomputar).
    """
    model = get_embeddings_model()
    model_id = get_effective_embedding_model_id()
    return CachedEmbeddings(model, model_id=model_id)


@lru_cache(maxsize=1)
def get_embedding_function_baseline() -> Embeddings:
    """Embedding genérico (fallback) para A/B test ou índice baseline."""
    from src.config import embedding_config
    model = get_baseline_embeddings_model()
    return CachedEmbeddings(model, model_id=embedding_config.embedding_fallback)

