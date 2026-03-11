from __future__ import annotations

import logging
from typing import Optional

from langchain_core.vectorstores import VectorStoreRetriever

from src.config import retrieval_config
from src.vectorstore.chroma_store import get_vectorstore


logger = logging.getLogger(__name__)


def get_retriever(k: Optional[int] = None) -> VectorStoreRetriever:
    """
    Cria um retriever semântico em cima do Chroma.

    - `k` controla quantos documentos retornar (padrão vem de `RetrievalConfig`).
    - Se você quiser mudar o tipo de busca (similarity, mmr, etc.),
      este é o lugar para mexer.
    """
    vectorstore = get_vectorstore()
    k_value = k or retrieval_config.k

    logger.info("Criando retriever com k=%d", k_value)

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k_value},
    )
    return retriever

