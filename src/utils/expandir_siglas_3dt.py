"""
Expande siglas 3D&T para nomes completos com sigla ao lado (padrão: Nome(Sigla)).
Mantém a lógica interna intacta; apenas a apresentação muda.

Ex.: F5, H6, R7, A6, PdF8, 30 PEs → Força(F) 5, Habilidade(H) 6, Resistência(R) 7, Armadura(A) 6, Poder de Fogo(PdF) 8, 30 Pontos de Energia(PE)
"""

from __future__ import annotations

import re


# Ordem importa: PdF antes de F, FA/FD antes de F; com valor antes de standalone
_SUBSTITUICOES: list[tuple[re.Pattern, str]] = [
    # PdF = Poder de Fogo (em stats de criaturas)
    (re.compile(r"\bPdF\s*(\d+(?:\s*[-–]\s*\d+)?)", re.IGNORECASE), r"Poder de Fogo(PdF) \1"),
    (re.compile(r"\bPdF\b(?!\s*\))", re.IGNORECASE), "Poder de Fogo(PdF)"),
    # FA = Força de Ataque (com valor primeiro, depois standalone)
    (re.compile(r"\bFA\s*[=:]?\s*(\d+)", re.IGNORECASE), r"Força de Ataque(FA) \1"),
    (re.compile(r"\bFA\s*[=:]?\s*([FHRA]\+[\d+d+\s]+)", re.IGNORECASE), r"Força de Ataque(FA) \1"),
    (re.compile(r"\bFA\b(?!\s*\))", re.IGNORECASE), "Força de Ataque(FA)"),
    # FD = Força de Defesa (com valor primeiro, depois standalone)
    (re.compile(r"\bFD\s*[=:]?\s*(\d+)", re.IGNORECASE), r"Força de Defesa(FD) \1"),
    (re.compile(r"\bFD\s*[=:]?\s*([FHRA+=\d\s]+)", re.IGNORECASE), r"Força de Defesa(FD) \1"),
    (re.compile(r"\bFD\b(?!\s*\))", re.IGNORECASE), "Força de Defesa(FD)"),
    # Atributos: F, H, R, A + número ou faixa (evita Fênix, Fogo, etc.)
    (re.compile(r"\bF(\d+(?:\s*[-–]\s*\d+)?)\b"), r"Força(F) \1"),
    (re.compile(r"\bH(\d+(?:\s*[-–]\s*\d+)?)\b"), r"Habilidade(H) \1"),
    (re.compile(r"\bR(\d+(?:\s*[-–]\s*\d+)?)\b"), r"Resistência(R) \1"),
    (re.compile(r"\bA(\d+(?:\s*[-–]\s*\d+)?)\b"), r"Armadura(A) \1"),
    # Atributos standalone (F, H, R, A sem número) — evita (F) já expandido com negative lookahead
    (re.compile(r"\bF\b(?!\s*\))"), "Força(F)"),
    (re.compile(r"\bH\b(?!\s*\))"), "Habilidade(H)"),
    (re.compile(r"\bR\b(?!\s*\))"), "Resistência(R)"),
    (re.compile(r"\bA\b(?!\s*\))"), "Armadura(A)"),
    # PV e PM (com valor primeiro, plural PMs/PVs, depois standalone)
    (re.compile(r"\bPV\s*[=:]?\s*(\d+)", re.IGNORECASE), r"Pontos de Vida(PV) \1"),
    (re.compile(r"\bPVs\b(?!\s*\))", re.IGNORECASE), "Pontos de Vida(PV)"),
    (re.compile(r"\bPV\b(?!\s*\))", re.IGNORECASE), "Pontos de Vida(PV)"),
    (re.compile(r"\bPM\s*[=:]?\s*(\d+)", re.IGNORECASE), r"Pontos de Magia(PM) \1"),
    (re.compile(r"\bPMs\b(?!\s*\))", re.IGNORECASE), "Pontos de Magia(PM)"),
    (re.compile(r"\bPM\b(?!\s*\))", re.IGNORECASE), "Pontos de Magia(PM)"),
    # PE = Pontos de Energia (preço de itens; com valor primeiro)
    (re.compile(r"\b(\d+)\s*PEs?\b", re.IGNORECASE), r"\1 Pontos de Energia(PE)"),
    (re.compile(r"\bPEs\b(?!\s*\))", re.IGNORECASE), "Pontos de Energia(PE)"),
    (re.compile(r"\bPE\b(?!\s*\))", re.IGNORECASE), "Pontos de Energia(PE)"),
    # CD = Classe de Dificuldade (standalone evita (CD) já expandido)
    (re.compile(r"\bCD\s*[=:]?\s*(\d+)", re.IGNORECASE), r"Classe de Dificuldade(CD) \1"),
    (re.compile(r"\bCD\b(?!\s*\))", re.IGNORECASE), "Classe de Dificuldade(CD)"),
]


def expandir_siglas_3dt(texto: str) -> str:
    """
    Substitui siglas 3D&T por nomes completos com sigla ao lado (padrão: Nome(Sigla)).

    - F5 → Força(F) 5
    - H6 → Habilidade(H) 6
    - R7 → Resistência(R) 7
    - A6 → Armadura(A) 6
    - PdF8 → Poder de Fogo(PdF) 8
    - FA 14 → Força de Ataque(FA) 14
    - FD → Força de Defesa(FD)
    - 30 PEs / 30 PE → 30 Pontos de Energia(PE)
    """
    if not texto or not isinstance(texto, str):
        return texto
    result = texto
    for padrao, substituicao in _SUBSTITUICOES:
        result = padrao.sub(substituicao, result)
    return result
