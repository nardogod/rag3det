"""
Geração de variações da pergunta do usuário para melhor recall na busca.

- Expande a query em até 3 variantes: original, frase-chave e termos do domínio 3D&T
  (ex.: "Fênix" → "Fênix magia elemental fogo", "ave Fênix conjuração chamas").
- Resolve casos em que o livro usa "Ave Fênix", "Magias Elementais de Fogo", etc.
"""
from __future__ import annotations

import logging
from typing import List

from src.retrieval.reranker import _key_phrase_from_query


logger = logging.getLogger(__name__)

NUM_VARIANTS = 3

# Sinônimos e expansões do domínio 3D&T para melhor recall (evita Solar/Pégaso para "Fênix").
# Chave: termo na pergunta (minúsculas); valor: frases alternativas para buscar no índice.
DOMAIN_3DET: dict[str, list[str]] = {
    "fênix": [
        "Fênix magia elemental fogo",
        "ave Fênix conjuração renascimento chamas",
    ],
    "fenix": [
        "Fênix magia elemental fogo",
        "ave Fênix conjuração renascimento chamas",
    ],
    "invocação da fênix": [
        "Fênix magia fogo conjuração criatura lendária",
    ],
    "mortos-vivos": [
        "mortos-vivos necromancia criaturas mortas",
        "morto-vivo esqueleto zumbi",
    ],
    "morto-vivo": [
        "mortos-vivos necromancia criaturas mortas",
    ],
    "insano megalomaníaco": [
        "Insano Megalomaníaco criatura bestiário",
        "Megalomaníaco bestiário",
    ],
    "megalomaníaco": [
        "Insano Megalomaníaco bestiário",
    ],
    "magia elemental": [
        "magia elemental fogo água terra vento",
    ],
    "conjuração": [
        "conjurar criatura invocação magia",
    ],
}


def _domain_expansions_for_query(query: str) -> List[str]:
    """Retorna frases de expansão 3D&T cujo termo aparece na query (minúsculas)."""
    q_lower = query.lower()
    out: List[str] = []
    for term, phrases in DOMAIN_3DET.items():
        if term in q_lower:
            for p in phrases:
                if p.strip() and p.strip().lower() not in (x.lower() for x in out):
                    out.append(p.strip())
    return out[: NUM_VARIANTS - 1]  # deixa espaço para original + key_phrase


def expand_query_variants(query: str) -> List[str]:
    """
    Gera até 3 variações da pergunta para buscar com todas e agregar resultados.

    - Primeira: a pergunta original.
    - Segunda: frase-chave (ex.: "Invocação da Fênix") ou expansão 3D&T se houver match.
    - Terceira: expansão de domínio (ex.: "Fênix magia elemental fogo") ou "regra de X".
    """
    query = query.strip()
    if not query:
        return [query]

    key = _key_phrase_from_query(query)
    domain = _domain_expansions_for_query(query)

    variants: List[str] = [query]

    # Incluir frase-chave se for relevante e diferente da query
    if len(key) >= 2 and key.strip().lower() not in (q.strip().lower() for q in variants):
        variants.append(key)

    # Preencher com expansões 3D&T (prioridade) e depois fallback "regra de X"
    for phrase in domain:
        if len(variants) >= NUM_VARIANTS:
            break
        if phrase and phrase.strip().lower() not in (q.strip().lower() for q in variants):
            variants.append(phrase)
    if key and len(variants) < NUM_VARIANTS:
        extra = f"regra de {key}" if len(key) < 30 else f"explicar {key[:40]}"
        if extra.strip().lower() not in (q.strip().lower() for q in variants):
            variants.append(extra)

    unique: List[str] = []
    seen_lower: set[str] = set()
    for v in variants:
        vn = (v or "").strip().lower()
        if vn and vn not in seen_lower:
            seen_lower.add(vn)
            unique.append((v or "").strip())
    result = unique[:NUM_VARIANTS]
    logger.debug("Query expansion: %d variantes (domínio 3D&T: %s)", len(result), bool(domain))
    return result
