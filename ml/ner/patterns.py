from __future__ import annotations

import re
from typing import Iterable, List, Tuple


EntitySpan = Tuple[int, int, str]


# Atributos clássicos de 3D&T
ATTRIBUTES = [
    "Força",
    "Habilidade",
    "Resistência",
    "Armadura",
    "Poder de Fogo",
    "Poder-de-Fogo",
    "Poder de fogo",
]

# Exemplos de raças comuns (pode ser expandido)
RACES = [
    "Humano",
    "Elfo",
    "Anão",
    "Halfling",
    "Orc",
    "Meio-elfo",
    "Meio-orc",
    "Goblin",
]

# Classes / arquétipos típicos
CLASSES = [
    "Guerreiro",
    "Mago",
    "Feiticeiro",
    "Clérigo",
    "Ladino",
    "Paladino",
    "Druida",
    "Bárbaro",
]

# Padrões de magias: nomes capitalizados seguidos por parênteses ou travessão
MAGIC_HINT = re.compile(
    r"([A-ZÁÂÃÀÉÊÍÓÔÕÚÇ][\wÁÂÃÀÉÊÍÓÔÕÚÇãáâàêéíóôõúç ]{2,}?)\s*(?:\(|–|-)\s*",
    flags=re.UNICODE,
)


def _find_terms(text: str, terms: Iterable[str], label: str) -> List[EntitySpan]:
    spans: List[EntitySpan] = []
    for term in terms:
        start = 0
        while True:
            idx = text.find(term, start)
            if idx == -1:
                break
            spans.append((idx, idx + len(term), label))
            start = idx + len(term)
    return spans


def weak_ner_patterns(text: str) -> List[EntitySpan]:
    """
    Aplica padrões simples (regex / listas) para gerar rótulos fracos de NER.

    Entidades marcadas:
    - ATTRIB: atributos clássicos (Força, Habilidade, etc.).
    - RACA: raças típicas (Humano, Elfo, etc.).
    - CLASSE: classes / arquétipos.
    - MAGIA: "nomes que parecem magias" (heurística).
    """
    spans: List[EntitySpan] = []

    spans += _find_terms(text, ATTRIBUTES, "ATTRIB")
    spans += _find_terms(text, RACES, "RACA")
    spans += _find_terms(text, CLASSES, "CLASSE")

    for match in MAGIC_HINT.finditer(text):
        start, end = match.span(1)
        spans.append((start, end, "MAGIA"))

    # Remover overlaps grosseiros: manter o maior span quando se sobrepõem
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    non_overlapping: List[EntitySpan] = []
    last_end = -1
    for start, end, label in spans:
        if start < last_end:
            continue
        non_overlapping.append((start, end, label))
        last_end = end

    return non_overlapping

