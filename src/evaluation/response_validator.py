from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from src.types import RetrievedChunk, SourceMetadata


@dataclass
class ValidationResult:
    citacao_presente: bool
    fonte_valida: bool
    numeros_ancorados: bool
    sem_hedge: bool
    needs_review: bool
    violated_rules: List[str]


def _extract_citations(text: str) -> List[str]:
    """Retorna todas as sequências entre aspas duplas."""
    return re.findall(r'"([^"]+)"', text)


def _extract_numbers(text: str) -> List[str]:
    return re.findall(r"\d+", text)


def validate_response(
    answer: str,
    chunks: List[RetrievedChunk],
) -> ValidationResult:
    """
    Aplica regras de validação à resposta estruturada.

    Regras:
    1. Deve citar pelo menos um trecho entre aspas.
    2. Fonte primária deve ser um dos livros realmente usados nos chunks.
    3. Se mencionar números (dano, custo, atributo), deve haver ao menos um número
       também em alguma citação literal.
    4. Não pode conter "eu acho que", "provavelmente", "talvez".
    """
    violated: List[str] = []
    text_lower = answer.lower()

    citations = _extract_citations(answer)
    citacao_presente = len(citations) > 0
    if not citacao_presente:
        violated.append("REGRA_1_SEM_CITACAO")

    # Regra 2: fonte primária deve bater com algum book_title dos chunks
    fonte_valida = False
    fonte_line_match = re.search(r"📖 FONTE PRIMÁRIA:(.+)", answer)
    if fonte_line_match:
        fonte_line = fonte_line_match.group(1).lower()
        books = {
            (c.metadata or {}).get("book_title", "").lower()
            for c in chunks
            if (c.metadata or {}).get("book_title")
        }
        fonte_valida = any(b and b in fonte_line for b in books)
    else:
        fonte_valida = False

    if not fonte_valida:
        violated.append("REGRA_2_FONTE_INVALIDA")

    # Regra 3: se houver número na resposta, ao menos um deve aparecer dentro de alguma citação
    all_numbers = _extract_numbers(answer)
    numeros_ancorados = True
    if all_numbers:
        nums_in_citations = []
        for cit in citations:
            nums_in_citations.extend(_extract_numbers(cit))
        if not nums_in_citations:
            numeros_ancorados = False
            violated.append("REGRA_3_NUMEROS_FORA_DA_CITACAO")

    # Regra 4: evitar linguagem vaga
    hedge_terms = ["eu acho que", "provavelmente", "talvez"]
    sem_hedge = not any(term in text_lower for term in hedge_terms)
    if not sem_hedge:
        violated.append("REGRA_4_HEDGE_LANGUAGE")

    needs_review = len(violated) > 0

    return ValidationResult(
        citacao_presente=citacao_presente,
        fonte_valida=fonte_valida,
        numeros_ancorados=numeros_ancorados,
        sem_hedge=sem_hedge,
        needs_review=needs_review,
        violated_rules=violated,
    )

