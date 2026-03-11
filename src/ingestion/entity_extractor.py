"""
Extrator de entidades (magias, itens) para indexacao com metadados.
Preserva contexto completo e permite busca por nome exato.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def extrair_nome_magia(query: str) -> str | None:
    """
    Extrai nome de magia de perguntas como:
    - "o que e Portal para o Saber?"
    - "como funciona Bola de Fogo?"
    - "qual e a magia Teleportacao?"
    """
    padroes = [
        r"o que [eé]\s+([^?]+)\??",
        r"como funciona\s+([^?]+)\??",
        r"qual e\s+(?:a\s+)?(?:magia\s+)?([^?]+)\??",
        r"magia\s+([A-Za-z][A-Za-z\s]+?)(?:\?|$)",
        r"([A-Za-z][A-Za-z\s]+)\s+(?:e uma|funciona como|permite)",
    ]
    for padrao in padroes:
        match = re.search(padrao, query, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            if len(nome) >= 3 and nome.lower() not in ("a", "o", "e", "um", "uma"):
                return nome
    return None


def extrair_magias_de_texto(texto: str) -> List[Dict[str, Any]]:
    """
    Extrai magias de texto 3D&T com regex.
    Padrao: Nome + Escola (+ Exigencias opcional) + Custo + Alcance + Duracao + Descricao
    """
    # Permite Exigencias opcional entre Escola e Custo; "por Autor" opcional entre Nome e Escola
    padrao = re.compile(
        r"(?P<nome>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*\n"
        r"(?:por\s+[^\n]+\n\s*)?"  # opcional: "por Eduardo Kawamoto"
        r"Escola:\s*(?P<escola>[^\n.]+)\.\s*\n"
        r"(?:Exig[eê]ncias:[^\n.]+\n\s*)?"  # opcional
        r"Custo:\s*(?P<custo>[^\n.]+)\.\s*\n"
        r"Alcance:\s*(?P<alcance>[^;]+);\s*"
        r"Dura[çc][aã]o:\s*(?P<duracao>[^\n.]+)\.\s*\n"
        r"(?P<descricao>.+?)(?=\n[A-Za-zÁÉÍÓÚ][^\n]*\nEscola:|\n\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    magias = []
    for match in padrao.finditer(texto):
        magia = {
            "nome": match.group("nome").strip(),
            "escola": match.group("escola").strip(),
            "custo": match.group("custo").strip(),
            "alcance": match.group("alcance").strip(),
            "duracao": match.group("duracao").strip(),
            "descricao": match.group("descricao").strip(),
            "texto_completo": match.group(0),
        }
        magias.append(magia)
    return magias


def indicadores_busca_magia(query: str) -> bool:
    """Verifica se a query indica busca por magia."""
    q = query.lower()
    return any(
        kw in q
        for kw in [
            "magia", "feitico", "feitico", "encantamento", "conjuracao",
            "pm", "pontos de mana", "escola", "elemental", "divina", "arcana",
            "circulo", "custo", "alcance", "duracao",
        ]
    )


def extrair_nome_item(query: str) -> str | None:
    """
    Extrai nome de item mágico de perguntas como:
    - "o que e arma Vorpal?"
    - "como funciona Afiada?"
    - "qual e o item Poção de Cura?"
    """
    padroes = [
        r"o que [eé]\s+(?:o\s+)?(?:item\s+)?(?:arma\s+)?([^?]+)\??",
        r"como funciona\s+(?:a\s+)?(?:arma\s+)?([^?]+)\??",
        r"qual e\s+(?:o\s+)?(?:item\s+)?(?:poder\s+)?([^?]+)\??",
        r"(?:item|arma|poder|poção|pergaminho)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)(?:\?|$)",
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+)\s+(?:e um|funciona como|permite|custa)",
    ]
    for padrao in padroes:
        match = re.search(padrao, query, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            if len(nome) >= 3 and nome.lower() not in ("a", "o", "e", "um", "uma"):
                return nome
    return None


def indicadores_busca_item(query: str) -> bool:
    """Verifica se a query indica busca por item mágico."""
    q = query.lower()
    return any(
        kw in q
        for kw in [
            "item mágico", "item magico", "objeto mágico", "arma mágica",
            "armadura mágica", "poção", "pergaminho", "elixir",
            "vorpal", "afiada", "agonizante", "sagrada", "profana",
            "pes", "pontos de experiência", "bônus", "bonus",
        ]
    )
