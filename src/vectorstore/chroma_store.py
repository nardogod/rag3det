from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import paths
from src.embedding.pipeline import get_embedding_function
from src.logging_config import setup_logging
from src.types import DocumentList


logger = logging.getLogger(__name__)

_COLLECTION_NAME = "3det_rag"
_COLLECTION_BASELINE = "3det_rag_baseline"


def _get_persist_directory() -> str:
    """Retorna o diretório onde o Chroma vai salvar o índice."""
    chroma_path = Path(paths.chroma_dir)
    chroma_path.mkdir(parents=True, exist_ok=True)
    return str(chroma_path)


def build_or_update_vectorstore(
    documents: DocumentList,
    use_baseline: bool = False,
) -> Chroma:
    """
    Cria (ou recria) o índice vetorial em Chroma a partir de uma lista de chunks.

    - use_baseline=False: usa embedding fine-tuned (collection 3det_rag).
    - use_baseline=True: usa embedding genérico (collection 3det_rag_baseline), para A/B.
    """
    setup_logging()

    if not documents:
        logger.warning("Nenhum documento recebido para indexar no Chroma.")
        raise ValueError("Lista de documentos vazia ao tentar criar índice vetorial.")

    persist_dir = _get_persist_directory()
    if use_baseline:
        from src.embedding.pipeline import get_embedding_function_baseline
        embeddings = get_embedding_function_baseline()
        collection = _COLLECTION_BASELINE
    else:
        embeddings = get_embedding_function()
        collection = _COLLECTION_NAME

    logger.info(
        "Construindo índice Chroma em %s (collection=%s) com %d documentos",
        persist_dir,
        collection,
        len(documents),
    )

    # Remove a collection existente para evitar erro de dimensão (768 vs 384).
    # Chroma não permite alterar a dimensão de uma collection já criada.
    try:
        import chromadb
        client = chromadb.PersistentClient(path=persist_dir)
        client.delete_collection(collection)
        logger.info("Collection %s removida para recriação com nova dimensão.", collection)
    except Exception as e:
        logger.debug("Ao remover collection %s (pode não existir): %s", collection, e)

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=collection,
    )
    logger.info("Índice Chroma construído com sucesso.")
    return vectorstore


def get_vectorstore(use_baseline: bool = False) -> Chroma:
    """
    Carrega o índice vetorial existente do Chroma.

    - use_baseline=False: índice com embedding fine-tuned (padrão).
    - use_baseline=True: índice com embedding genérico (para A/B).
    """
    persist_dir = _get_persist_directory()
    if use_baseline:
        from src.embedding.pipeline import get_embedding_function_baseline
        embeddings = get_embedding_function_baseline()
        collection = _COLLECTION_BASELINE
    else:
        embeddings = get_embedding_function()
        collection = _COLLECTION_NAME

    logger.info(
        "Carregando índice Chroma de %s (collection=%s)",
        persist_dir,
        collection,
    )

    return Chroma(
        persist_directory=persist_dir,
        collection_name=collection,
        embedding_function=embeddings,
    )


def get_all_documents(vectorstore: Optional[Chroma] = None) -> DocumentList:
    """
    Retorna todos os documentos da collection (para índice BM25 / busca híbrida).

    - Se o índice estiver vazio, retorna lista vazia.
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()
    try:
        coll = vectorstore._collection
        result = coll.get(include=["documents", "metadatas"])
    except Exception as e:
        logger.warning("Não foi possível obter documentos do Chroma: %s", e)
        return []

    ids_list = result.get("ids") or []
    documents_list = result.get("documents") or []
    metadatas_list = result.get("metadatas") or [{}] * len(ids_list)

    out: List[Document] = []
    for i, doc_content in enumerate(documents_list):
        meta = metadatas_list[i] if i < len(metadatas_list) else {}
        out.append(Document(page_content=doc_content or "", metadata=meta or {}))
    logger.debug("get_all_documents: %d documentos", len(out))
    return out

