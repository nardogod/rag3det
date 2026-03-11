from __future__ import annotations

import logging
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from src.config import embedding_config


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embeddings_model() -> Embeddings:
    """
    Cria (e faz cache) do modelo de embeddings HuggingFace.

    - Usa um modelo multilíngue adequado para português (configurado em `.env`).
    - Roda 100% local e gratuito (desde que você tenha o `sentence-transformers` instalado).

    Se você quiser trocar o modelo padrão:
    - ajuste `EMBEDDING_MODEL_NAME` no `.env` ou
    - altere `embedding_config.model_name` em `src/config.py`.
    """
    model_name = embedding_config.model_name
    logger.info("Carregando modelo de embeddings: %s", model_name)

    return HuggingFaceEmbeddings(
        model_name=model_name,
        show_progress=True,
    )

