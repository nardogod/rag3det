"""
Expansão de query usando o grafo de conhecimento e a taxonomia.

- Filtros: fragmentos ("e ar", "de "), termos genéricos, números isolados.
- Prioridade: (1) targets is_a/element/school que são entidades (0.9); (2) cluster coerente (0.7); (3) cost_pm/effect (0.8).
- Fallback: se <2 termos válidos, usa retrieval padrão e loga.
"""
from __future__ import annotations

import logging
import re
from typing import List, Set, Tuple

from src.knowledge.base import (
    get_entity_cluster,
    get_cluster_entities,
    get_relations_for_entity,
    load_entities,
    load_taxonomy,
)
from src.ml.taxonomy.portuguese_stopwords import is_stopword

logger = logging.getLogger(__name__)

WEIGHT_ORIGINAL = 1.0
WEIGHT_P1_GRAPH_ENTITY = 0.9
WEIGHT_P2_CLUSTER = 0.7
WEIGHT_P3_RELATION = 0.8
MIN_WORDS_OR_KNOWN_ENTITY = 2
MIN_VALID_TERMS_FOR_EXPANSION = 2

# Fragmentos: não pode começar com isso
FRAGMENT_PREFIXES = ("e ", "ou ", "de ", "da ", "do ", "e\t", "ou\t", "de\t")
# Termos/frases genéricos demais (não expandir para isso)
GENERIC_BLOCKLIST = frozenset({
    "clericato ou paladino", "paladino ou clericato",
    "magia ou habilidade", "vantagem ou desvantagem",
})
# Número isolado
ONLY_DIGITS = re.compile(r"^\d+$")


def _normalize_key(name: str) -> str:
    return " ".join((name or "").strip().split())


def _is_fragment(term: str) -> bool:
    """Não pode começar com 'e ', 'ou ', 'de ', 'da ', 'do '."""
    t = (term or "").strip().lower()
    return any(t.startswith(p.rstrip()) for p in FRAGMENT_PREFIXES)


def _is_isolated_number(term: str) -> bool:
    return bool(ONLY_DIGITS.match((term or "").strip()))


def _has_min_words_or_is_entity(term: str, known_entities: Set[str]) -> bool:
    """Mínimo 2 palavras OU ser nome de entidade conhecida (evita fragmentos de 1 palavra genérica)."""
    t = (term or "").strip()
    if t.lower() in known_entities:
        return True
    words = [w for w in t.split() if w]
    return len(words) >= MIN_WORDS_OR_KNOWN_ENTITY


def _is_only_stopwords(term: str) -> bool:
    words = (term or "").strip().split()
    return all(is_stopword(w) for w in words)


def _is_too_generic(term: str) -> bool:
    return (term or "").strip().lower() in GENERIC_BLOCKLIST


def _term_appears_in_too_many_entities(term: str, entity_names: List[str], threshold: float = 0.3) -> bool:
    """True se termo aparece como palavra inteira em mais que threshold das entidades (genérico demais)."""
    if not term or not entity_names:
        return False
    t_lower = term.strip().lower()
    if not t_lower:
        return True
    # Conta entidades cujo nome contém o termo como palavra inteira
    pattern = re.compile(r"\b" + re.escape(t_lower) + r"\b", re.IGNORECASE)
    count = sum(1 for name in entity_names if pattern.search(name.lower()))
    return count > threshold * len(entity_names)


def _is_valid_expansion_term(
    term: str,
    known_entity_names: Set[str],
    all_entity_names: List[str],
) -> bool:
    """
    Filtro de qualidade: mínimo 3 palavras OU entidade conhecida;
    não fragmento; não só stopwords; não número isolado; não genérico;
    não termo que aparece em >30% das entidades (genérico demais).
    """
    t = (term or "").strip()
    if len(t) < 2:
        return False
    if _is_fragment(t):
        return False
    if _is_isolated_number(t):
        return False
    if _is_only_stopwords(t):
        return False
    if _is_too_generic(t):
        return False
    if not _has_min_words_or_is_entity(t, known_entities=known_entities):
        return False
    if _term_appears_in_too_many_entities(t, all_entity_names, threshold=0.3):
        return False
    return True


def _cluster_has_coherence(cid: str) -> bool:
    """Cluster não pode ser só stopwords (ex.: de_nao_que_os_ou)."""
    if not cid or len(cid) < 4:
        return False
    parts = cid.lower().replace("_", " ").split()
    if not parts:
        return False
    stop_count = sum(1 for p in parts if is_stopword(p))
    return stop_count < len(parts)  # pelo menos uma parte não é stopword


def _match_entity(query: str, entities: dict) -> str | None:
    """Encontra entidade que case-insensitive match ou contém a query."""
    q = query.strip().lower()
    if not q:
        return None
    for name in entities:
        if name.lower() == q or q in name.lower() or name.lower() in q:
            return name
    return None


def expand_query_with_graph(
    query: str,
    max_terms: int = 5,
    include_cluster_entities: bool = True,
) -> List[Tuple[str, float]]:
    """
    Expande a query com prioridades e filtros.
    P1: targets is_a/element/school que são entidades conhecidas (0.9).
    P2: entidades do mesmo cluster se cluster coerente (0.7).
    P3: cost_pm (não número isolado), effect (0.8).
    Fallback: se <2 termos válidos, retorna só query e loga.
    """
    entities = load_entities()
    if not entities:
        return [(query.strip(), WEIGHT_ORIGINAL)]

    entity_names_list = list(entities.keys())
    known_entity_names_lower = {n.lower() for n in entity_names_list}

    entity_name = _match_entity(query, entities)
    if not entity_name:
        return [(query.strip(), WEIGHT_ORIGINAL)]

    terms: List[Tuple[str, float]] = [(query.strip(), WEIGHT_ORIGINAL)]
    seen_lower = {query.strip().lower()}

    def _add(t: str, w: float) -> bool:
        if not t or t.lower() in seen_lower:
            return False
        if not _is_valid_expansion_term(t, known_entity_names_lower, entity_names_list):
            return False
        seen_lower.add(t.lower())
        terms.append((t, w))
        return True

    relations = get_relations_for_entity(entity_name)

    # Prioridade 1: target de is_a, element, school só se for entidade conhecida (0.9)
    for r in relations:
        rel_type = r.get("relation", "")
        if rel_type not in ("is_a", "school", "element"):
            continue
        target = _normalize_key(r.get("target", ""))
        if target.lower() in known_entity_names_lower:
            if _add(target, WEIGHT_P1_GRAPH_ENTITY):
                if len(terms) >= max_terms:
                    break
    if len(terms) >= max_terms:
        return terms

    # Prioridade 2: entidades do mesmo cluster (0.7) só se cluster coerente
    if include_cluster_entities:
        cid = get_entity_cluster(entity_name)
        if cid and _cluster_has_coherence(cid):
            taxonomy = load_taxonomy()
            for e in get_cluster_entities(cid, taxonomy):
                if e != entity_name and _add(e, WEIGHT_P2_CLUSTER):
                    if len(terms) >= max_terms:
                        break
    if len(terms) >= max_terms:
        return terms

    # Prioridade 3: cost_pm (valor + " PM"), effect (0.8)
    for r in relations:
        rel_type = r.get("relation", "")
        target = _normalize_key(r.get("target", ""))
        if rel_type == "cost_pm":
            if not _is_isolated_number(target):
                term = f"{target} PM"
                if _add(term, WEIGHT_P3_RELATION) and len(terms) >= max_terms:
                    break
        elif rel_type == "effect" and _is_valid_expansion_term(target, known_entity_names_lower, entity_names_list):
            if _add(target, WEIGHT_P3_RELATION) and len(terms) >= max_terms:
                break

    # Incluir targets is_a/element/school que não são entidade mas passam no filtro (ex.: "Magia Elemental", "Fogo")
    for r in relations:
        rel_type = r.get("relation", "")
        if rel_type not in ("is_a", "school", "element"):
            continue
        target = _normalize_key(r.get("target", ""))
        if target.lower() in seen_lower:
            continue
        if _is_valid_expansion_term(target, known_entity_names_lower, entity_names_list):
            w = WEIGHT_P1_GRAPH_ENTITY if target.lower() in known_entity_names_lower else WEIGHT_P3_RELATION
            _add(target, w)
        if len(terms) >= max_terms:
            break

    result = [terms[0]]
    for t, w in terms[1:]:
        if t.lower() not in {x[0].lower() for x in result}:
            result.append((t, w))
    result = result[:max_terms]

    if len(result) < MIN_VALID_TERMS_FOR_EXPANSION:
        logger.info(
            "Expansão insuficiente para %r (%d termos válidos), usando retrieval padrão",
            query.strip(),
            len(result),
        )
        return [(query.strip(), WEIGHT_ORIGINAL)]
    return result


def get_expanded_queries_flat(query: str, max_terms: int = 5) -> List[str]:
    """Retorna apenas a lista de strings para passar ao retriever (sem pesos)."""
    weighted = expand_query_with_graph(query, max_terms=max_terms)
    return [t[0] for t in weighted]
