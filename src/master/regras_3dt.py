"""
Regras 3D&T Alpha para testes e CDs.
Mapeamento literal das tabelas do manual: dificuldade -> CD, atributos F/H/R/A.
"""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional

# --- Dificuldade e CD (tabela 3D&T) ---
# Tarefas Fáceis: sucesso automático com especialidade; H-1 sem
# Tarefas Médias: H+1 com especialidade; H-3 sem
# Tarefas Difíceis: H-2 com especialidade; falha automática sem
# CD base para 1d6 + atributo (atributos 1-5, d6 1-6 => total 2-11)
DIFICULDADE_CD = {
    "facil": 3,
    "normal": 4,
    "dificil": 5,
    "muito_dificil": 6,
}


class Dificuldade3DT(str, Enum):
    """Níveis de dificuldade conforme manual 3D&T."""
    FACIL = "facil"
    NORMAL = "normal"
    DIFICIL = "dificil"
    MUITO_DIFICIL = "muito_dificil"


DIFICULDADE_FROM_LEGIVEL = {
    "facil": "facil",
    "Fácil": "facil",
    "Facil": "facil",
    "normal": "normal",
    "Normal": "normal",
    "dificil": "dificil",
    "Difícil": "dificil",
    "Dificil": "dificil",
    "muito_dificil": "muito_dificil",
    "Muito Difícil": "muito_dificil",
    "Muito Dificil": "muito_dificil",
}

ATRIBUTO_FROM_LEGIVEL = {
    "Forca": "F",
    "Força": "F",
    "Força(F)": "F",
    "Habilidade": "H",
    "Habilidade(H)": "H",
    "Resistencia": "R",
    "Resistência": "R",
    "Resistência(R)": "R",
    "Armadura": "A",
    "Armadura(A)": "A",
}


def cd_por_dificuldade(dificuldade: str | Dificuldade3DT) -> int:
    """Retorna CD numérico para a dificuldade dada."""
    if isinstance(dificuldade, Dificuldade3DT):
        dificuldade = dificuldade.value
    norm = DIFICULDADE_FROM_LEGIVEL.get(str(dificuldade), str(dificuldade).lower())
    return DIFICULDADE_CD.get(norm, 4)


def atributo_interno(nome_legivel: str) -> str:
    """Converte nome legivel (Forca, Habilidade) para sigla interna (F, H)."""
    return ATRIBUTO_FROM_LEGIVEL.get(str(nome_legivel), "H")


# --- Atributos 3D&T (F, H, R, A) - lógica interna usa siglas ---
ATRIBUTOS_3DT = ("F", "H", "R", "A")
ATRIBUTO_NOME = {
    "F": "Força(F)",
    "H": "Habilidade(H)",
    "R": "Resistência(R)",
    "A": "Armadura(A)",
}

# Termos legíveis para o usuário (padrão: Nome(Sigla))
TERMOS_LEGIVEIS = {
    "F": "Força(F)",
    "H": "Habilidade(H)",
    "R": "Resistência(R)",
    "A": "Armadura(A)",
    "PV": "Pontos de Vida(PV)",
    "PM": "Pontos de Magia(PM)",
    "PdF": "Poder de Fogo(PdF)",
    "FA": "Força de Ataque(FA)",
    "FD": "Força de Defesa(FD)",
    "CD": "Classe de Dificuldade(CD)",
}

# Mapeamento: tipo de teste -> atributo base
ATRIBUTO_POR_TIPO = {
    "iniciativa": "H",
    "ataque": "F",  # ou H para ataques à distância
    "defesa": "H",
    "percepcao": "H",
    "investigacao": "H",
    "social": "H",
    "lábia": "H",
    "seducao": "H",
    "intimidacao": "H",
    "forca": "F",
    "resistencia": "R",
}


def atributo_para_teste(tipo_teste: str) -> str:
    """Retorna atributo 3D&T (F/H/R/A) para o tipo de teste."""
    return ATRIBUTO_POR_TIPO.get(tipo_teste.lower(), "H")


def nome_atributo_completo(atributo: str, contexto: str = "") -> str:
    """Ex: H -> 'Habilidade (Percepção)' se contexto=percepcao."""
    nome = ATRIBUTO_NOME.get(atributo.upper(), atributo)
    if contexto:
        return f"{nome} ({contexto})"
    return nome


def rolar_d6() -> int:
    """Rola 1d6 conforme regras 3D&T."""
    return random.randint(1, 6)


def resolver_teste(
    cd: int,
    modificador: int = 0,
    atributo: str = "H",
) -> tuple[int, int, bool]:
    """
    Resolve teste 3D&T: 1d6 + modificador >= CD.
    Retorna (rolagem_d6, total, sucesso).
    """
    d6 = rolar_d6()
    total = d6 + modificador
    sucesso = total >= cd
    return d6, total, sucesso


def descricao_teste_3dt(
    atributo: str,
    cd: int,
    d6: int,
    total: int,
    sucesso: bool,
    modificador: int = 0,
    contexto: str = "",
) -> str:
    """Gera descrição legível: 'Teste de Habilidade (Percepção): 1d6+2=7 vs Classe de Dificuldade 4 — Sucesso'."""
    nome = nome_atributo_completo(atributo, contexto)
    mod_str = f"+{modificador}" if modificador > 0 else (f"-{-modificador}" if modificador < 0 else "")
    resultado = "Sucesso" if sucesso else "Falha"
    cd_label = TERMOS_LEGIVEIS.get("CD", "CD")
    return f"Teste de {nome}{' ' + mod_str if mod_str else ''}: 1d6={d6}, total={total} vs {cd_label} {cd} — {resultado}"
