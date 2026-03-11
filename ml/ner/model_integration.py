from __future__ import annotations

"""
Integração do modelo de NER (spaCy) com o pipeline de RAG.

Funções principais:
- `get_ner_model()` – carrega o modelo spaCy (treinado ou base) com cache.
- `enrich_documents_with_ner()` – adiciona entidades como metadados nos chunks.

Configuração:
- Defina `NER_MODEL_PATH` no `.env` (ex.: `models/ner_3det`).
- Se não definido, usa `pt_core_news_lg` como base (zero-shot).
"""

import logging
import os
from functools import lru_cache
from typing import Dict, List

import spacy
from langchain_core.documents import Document

from src.types import DocumentList, Metadata


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ner_model():
    model_path = os.getenv("NER_MODEL_PATH", "pt_core_news_lg")
    logger.info("Carregando modelo spaCy de NER: %s", model_path)
    try:
        nlp = spacy.load(model_path)
    except OSError as e:
        raise RuntimeError(
            f"Não foi possível carregar o modelo spaCy '{model_path}'. "
            "Certifique-se de ter rodado `python -m spacy download pt_core_news_lg` "
            "ou treinado seu modelo customizado."
        ) from e
    return nlp


def _entities_to_metadata(doc: Document, ents) -> Metadata:
    """
    Converte as entidades spaCy em estrutura simples de metadados.

    - Lista geral em `ner_entities`.
    - Campos específicos por tipo (ex.: `ner_ATTRIB`, `ner_RACA`, `ner_CLASSE`, `ner_MAGIA`).
    """
    meta: Metadata = dict(doc.metadata or {})

    entities_info: List[Dict[str, str]] = []
    by_label: Dict[str, List[str]] = {}

    for ent in ents:
        text = ent.text.strip()
        label = ent.label_
        if not text:
            continue

        entities_info.append({"text": text, "label": label})
        key = f"ner_{label}"
        by_label.setdefault(key, [])
        if text not in by_label[key]:
            by_label[key].append(text)

    if entities_info:
        meta["ner_entities"] = entities_info
        for key, values in by_label.items():
            meta[key] = values

    return meta


def enrich_documents_with_ner(documents: DocumentList) -> DocumentList:
    """
    Enriquece cada chunk com metadados de NER (se houver entidades detectadas).

    - Roda o modelo spaCy em batch para melhor desempenho.
    - Atualiza `doc.metadata` com:
      - `ner_entities`: lista de {text, label}
      - `ner_LABEL`: listas por tipo (ex.: `ner_MAGIA` = ["Invocação da Fênix", ...])
    """
    if not documents:
        return documents

    nlp = get_ner_model()
    texts = [doc.page_content for doc in documents]

    logger.info("Rodando NER spaCy em %d chunks...", len(documents))

    for doc_obj, spacy_doc in zip(documents, nlp.pipe(texts, batch_size=32)):
        ents = [ent for ent in spacy_doc.ents]
        if not ents:
            continue
        doc_obj.metadata = _entities_to_metadata(doc_obj, ents)

    logger.info("Enriquecimento de NER concluído.")
    return documents

