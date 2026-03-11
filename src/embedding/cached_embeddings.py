"""
Cache persistente para embeddings: evita recomputar vetores para textos já processados.

- Chave de cache: hash do texto + identificador do modelo (trocar modelo = novo cache).
- Armazenamento: diretório em `data/embedding_cache` (shelve por modelo).
"""
from __future__ import annotations

import hashlib
import logging
import shelve
import threading
from pathlib import Path
from typing import Dict, List

from langchain_core.embeddings import Embeddings

from src.config import embedding_config, paths


logger = logging.getLogger(__name__)

_CACHE_DIR = Path(paths.data_dir) / "embedding_cache"
_LOCK = threading.Lock()


def _cache_key(text: str) -> str:
    """Chave estável para um texto (normalizado)."""
    normalized = text.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _model_prefix(model_id: str | None = None) -> str:
    """Prefixo do cache por modelo (mudar modelo = novo cache)."""
    base = (model_id or getattr(embedding_config, "model_name", None) or "default")
    safe = "".join(c if c.isalnum() or c in "-_./" else "_" for c in str(base))
    return safe[:64]


def _get_shelf(mode: str = "c", model_id: str | None = None):
    """Abre o shelve do cache para o modelo atual. mode: 'c' read/write, 'r' read-only."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _CACHE_DIR / _model_prefix(model_id)
    return shelve.open(str(path), flag=mode, protocol=4)


class CachedEmbeddings(Embeddings):
    """
    Wrapper que persiste embeddings em disco e só chama o modelo para textos novos.
    """

    def __init__(self, underlying: Embeddings, model_id: str | None = None) -> None:
        self._underlying = underlying
        self._model_id = model_id

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        cached: Dict[int, List[float]] = {}
        to_compute: List[tuple[int, str]] = []

        with _LOCK:
            try:
                with _get_shelf("r", self._model_id) as db:
                    for i, text in enumerate(texts):
                        key = _cache_key(text)
                        if key in db:
                            cached[i] = db[key]
                        else:
                            to_compute.append((i, text))
            except Exception as e:
                logger.warning("Cache de embeddings indisponível (%s), recalculando tudo.", e)
                to_compute = [(i, t) for i, t in enumerate(texts)]

        if to_compute:
            texts_to_embed = [t for _, t in to_compute]
            computed = self._underlying.embed_documents(texts_to_embed)
            with _LOCK:
                try:
                    with _get_shelf("c", self._model_id) as db:
                        for (i, text), vec in zip(to_compute, computed):
                            cached[i] = vec
                            db[_cache_key(text)] = vec
                except Exception as e:
                    logger.warning("Não foi possível gravar no cache de embeddings: %s", e)
                    for (i, _), vec in zip(to_compute, computed):
                        cached[i] = vec

        return [cached[i] for i in range(len(texts))]

    def embed_query(self, text: str) -> List[float]:
        key = _cache_key(text)
        with _LOCK:
            try:
                with _get_shelf("r", self._model_id) as db:
                    if key in db:
                        return db[key]
            except Exception:
                pass

        vec = self._underlying.embed_query(text)
        with _LOCK:
            try:
                with _get_shelf("c", self._model_id) as db:
                    db[key] = vec
            except Exception as e:
                logger.debug("Não foi possível gravar query no cache: %s", e)
        return vec
