from __future__ import annotations

"""
Funções auxiliares para busca baseada em entidades NER.

Uso típico:
- Perguntas como: "monstros do tipo morto-vivo"
- Buscar por chunks que tenham, nos metadados, entidades específicas (ex.: `ner_RACA`, `ner_MAGIA`).
"""

from typing import List, Optional

from langchain_core.documents import Document

from src.retrieval.pipeline import retrieve_relevant_chunks
from src.types import RetrievedChunk, SourceMetadata


def retrieve_chunks_by_entity(
    entity_text: str,
    label: Optional[str] = None,
    k: int = 20,
) -> List[RetrievedChunk]:
    """
    Busca chunks que contenham uma entidade específica nos metadados de NER.

    - `entity_text`: texto da entidade (ex.: "morto-vivo", "elfo", "Invocação da Fênix").
    - `label`: rótulo opcional (ex.: "RACA", "MAGIA"); se None, procura em todas.
    - `k`: quantos trechos considerar na busca inicial.

    Implementação:
    - Usa o pipeline de retrieval normal com a entidade como query (para pegar
      trechos semanticamente próximos).
    - Filtra em Python olhando para os campos `ner_*` dos metadados.
    """
    base_results = retrieve_relevant_chunks(entity_text, k=k)
    target = entity_text.lower()

    filtered: List[RetrievedChunk] = []

    for chunk in base_results:
        meta: SourceMetadata = chunk.metadata or {}

        # Verificar campos ner_LABEL específicos
        if label is not None:
            key = f"ner_{label}"
            values = [v.lower() for v in meta.get(key, [])]
            if any(target in v for v in values):
                filtered.append(chunk)
            continue

        # Caso não tenha label: olhar todas as listas `ner_*`
        matched = False
        for m_key, m_value in meta.items():
            if not m_key.startswith("ner_"):
                continue
            if isinstance(m_value, list):
                values = [str(v).lower() for v in m_value]
                if any(target in v for v in values):
                    matched = True
                    break
        if matched:
            filtered.append(chunk)

    return filtered

