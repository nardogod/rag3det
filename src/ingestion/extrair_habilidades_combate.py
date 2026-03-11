"""
Extrai habilidades de combate relevantes da descrição de monstros.
Converte texto em habilidades estruturadas para uso em combate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HabilidadeCombate:
    """Habilidade de combate extraída da descrição."""

    nome: str
    detalhes: str
    tipo: str  # veneno, teste, imunidade, restricao, efeito_especial, ataque


# Padrões para extração (ordem importa — mais específicos primeiro)
PADROES_VENENO = [
    # veneno(XdY) ou veneno (XdY), Z PVs por turno
    re.compile(
        r"veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?\s*(?:,|\s+e\s+)?\s*(?:a\s+vítima\s+)?(?:perde\s+)?(\d+)\s*P[Vv]s?\s*por\s*(?:turno|rodada)",
        re.I,
    ),
    # "3 PVs por turno... 10d6 no sistema Daemon" ou "perde 3 PVs por turno, em vez de 1 (10d6)"
    re.compile(
        r"(?:perde\s+)?(\d+)\s*P[Vv]s?\s*por\s*(?:turno|rodada)(?:[^.]*?(\d+d\d+))?",
        re.I,
    ),
    re.compile(
        r"(?:\(|\s)(\d+d\d+)\s*(?:no\s+sistema\s+Daemon|dano)",
        re.I,
    ),
    re.compile(r"veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?", re.I),
    re.compile(r"dano\s+\d+d\d+\s*\+\s*veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?", re.I),
    re.compile(r"mordida\s+\d+/\d+\s*dano\s+(\d+d\d+)\s*\+\s*veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?", re.I),
]

PADROES_TESTE_ATACAR = [
    re.compile(
        r"(?:oponentes?|inimigos?)\s+precisam?\s+passar\s+em\s+um?\s+[Tt]este\s+de\s+(WILL|Resist[eê]ncia|R)\s+antes\s+de\s+(?:poderem\s+)?atac[aá]r",
        re.I,
    ),
    re.compile(
        r"[Tt]este\s+de\s+(WILL|R|Resist[eê]ncia)\s+(?:para\s+)?(?:poder\s+)?atac[aá]r",
        re.I,
    ),
    re.compile(
        r"imposs[ií]vel\s+(?:para\s+)?(?:um?\s+)?(?:homem|human[oó]ide).*?atac[aá]r",
        re.I,
    ),
]

PADROES_TESTE_AGREDIR = [
    re.compile(
        r"(?:até\s+mesmo\s+)?(?:mulheres?|personagens?)\s+devem\s+(?:,?\s+antes\s+de\s+ferir[^.]*\.)?\s+ter\s+sucesso\s+em\s+um?\s+[Tt]este\s+de\s+Resistência",
        re.I,
    ),
    re.compile(
        r"[Tt]este\s+(?:deve\s+ser\s+feito\s+)?cada\s+vez\s+que\s+(?:a\s+)?[Pp]ersonagem\s+tenta\s+realizar\s+qualquer\s+agress[aã]o",
        re.I,
    ),
]

PADROES_COMA_BELEZA = [
    re.compile(
        r"(?:vis[aã]o|visão)\s+de\s+uma?\s+(?:ninfa\s+)?nua\s+.*?(?:exige|provoca).*?[Tt]este\s+de\s+Resistência.*?(?:falha|fracasso)\s+provoca.*?(?:efeito\s+da\s+)?[Mm]agia\s+Coma",
        re.I,
    ),
    re.compile(
        r"(?:falha|fracasso)\s+provoca.*?(?:efeito\s+da\s+)?[Mm]agia\s+Coma",
        re.I,
    ),
]

PADROES_IMUNIDADE = [
    # "Construtos ou Mortos-Vivos são imunes à beleza" → Imune: Construtos, Mortos-Vivos
    re.compile(
        r"((?:Construtos?|Mortos?-Vivos?|Mortos?\s+Vivos?)(?:\s+ou\s+(?:Construtos?|Mortos?-Vivos?|Mortos?\s+Vivos?))?)\s+(?:s[aã]o\s+)?[Ii]munes?",
        re.I,
    ),
    re.compile(
        r"(?:apenas\s+)?(?:criaturas?|seres?)\s+(?:totalmente\s+)?(?:sem\s+alma|sem\s+emoções).*?(?:como\s+)?(?:Construtos?|Mortos?-Vivos?|Mortos?\s+Vivos?)",
        re.I,
    ),
    re.compile(
        r"[Ii]munes?\s*(?:a|à)?\s*[:\s]*(.+?)(?:\.|;|$)",
        re.I,
    ),
]

PADROES_INCAPAZ_LUTAR = [
    re.compile(r"totalmente\s+incapaz\s+de\s+lutar", re.I),
    re.compile(r"nunca\s+(?:usará\s+armas|atacará)\s+por\s+motivo\s+algum", re.I),
]

PADROES_DEFINHAR = [
    re.compile(
        r"(?:arrastada?|tirada?)\s+para\s+fora\s+de\s+seu\s+ambiente\s+.*?(?:definhar|morrer[aá])\s+(?:em\s+)?(\d+)\s*(hora|minuto)",
        re.I,
    ),
]

PADROES_CONSTRICAO = [
    re.compile(
        r"(?:constri[cç][aã]o|esmagamento)\s*[:\s]*dano\s+de\s+(\d+d\d+\s*\+\s*\d+|\d+d\d+)\s*por\s*(?:rodada|turno)",
        re.I,
    ),
]

PADROES_VOZ_MELODIOSA = [
    re.compile(r"[Vv]oz\s+[Mm]elodiosa", re.I),
]

PADROES_INVULNERABILIDADE = [
    re.compile(
        r"[Ii]nvulnerabilidade\s*(?:a|à)?\s*[:\s]*(.+?)(?:\.|,|;|\))",
        re.I,
    ),
]

PADROES_VULNERABILIDADE = [
    re.compile(
        r"[Vv]ulnerabilidade\s*(?:a|à)?\s*[:\s]*(.+?)(?:\.|,|;|\))",
        re.I,
    ),
]


def _limpar_detalhes(s: str) -> str:
    """Remove excesso de espaços e normaliza."""
    return re.sub(r"\s+", " ", s.strip())[:200]


def extrair_veneno(texto: str) -> list[HabilidadeCombate]:
    """Extrai informações de veneno da descrição."""
    dano_veneno: str | None = None
    pvs_turno: str | None = None

    # Padrão: perde N PVs por turno... (XdY)
    m = re.search(
        r"(?:perde|perda\s+de)\s+(\d+)\s*P[Vv]s?\s*por\s*(?:turno|rodada)[^.]*?\((\d+d\d+)\)",
        texto,
        re.I,
    )
    if m:
        pvs_turno, dano_veneno = m.group(1), m.group(2)

    # Padrão: veneno(XdY), N PVs/turno
    if not dano_veneno:
        m = re.search(
            r"veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?\s*(?:.*?(\d+)\s*P[Vv]s?\s*por\s*(?:turno|rodada))?",
            texto,
            re.I,
        )
        if m:
            dano_veneno = m.group(1)
            pvs_turno = m.group(2) if m.lastindex >= 2 else pvs_turno

    # Padrão: Mordida X/Y dano ZdW+veneno(NdM)
    if not dano_veneno:
        m = re.search(r"veneno\s*[\(\[]?\s*(\d+d\d+)\s*[\)\]]?", texto, re.I)
        if m:
            dano_veneno = m.group(1)

    if dano_veneno:
        detalhes = f"{dano_veneno} dano"
        if pvs_turno:
            detalhes += f", {pvs_turno} PVs por turno"
        return [HabilidadeCombate("Veneno", detalhes, "veneno")]
    return []


def extrair_testes(texto: str) -> list[HabilidadeCombate]:
    """Extrai testes obrigatórios (WILL, R) para atacar/agredir."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_TESTE_ATACAR:
        if m := pat.search(texto):
            teste = m.group(1) if m.lastindex and m.group(1) else "WILL"
            if teste in ("WILL", "R", "Resistência", "Resistencia"):
                resultado.append(
                    HabilidadeCombate("Teste para atacar", f"Teste de {teste} antes de atacar", "teste")
                )
            else:
                resultado.append(
                    HabilidadeCombate("Teste para atacar", "Impossível atacar sem teste (ver descrição)", "teste")
                )
            break
    for pat in PADROES_TESTE_AGREDIR:
        if m := pat.search(texto):
            resultado.append(
                HabilidadeCombate(
                    "Teste para agredir",
                    "Teste de R cada vez que tenta agredir",
                    "teste",
                )
            )
            break
    return resultado


def extrair_efeitos_especiais(texto: str) -> list[HabilidadeCombate]:
    """Extrai efeitos como Coma, Voz Melodiosa."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_COMA_BELEZA:
        if pat.search(texto):
            resultado.append(
                HabilidadeCombate(
                    "Beleza atordoante",
                    "Falha em Teste de R: efeito da Magia Coma (PVs a zero)",
                    "efeito_especial",
                )
            )
            break
    for pat in PADROES_VOZ_MELODIOSA:
        if pat.search(texto):
            resultado.append(HabilidadeCombate("Voz Melodiosa", "Ver descrição no livro", "efeito_especial"))
            break
    return resultado


def extrair_imunidades(texto: str) -> list[HabilidadeCombate]:
    """Extrai imunidades (Construtos, Mortos-Vivos, etc.)."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_IMUNIDADE:
        for m in pat.finditer(texto):
            if m.lastindex and m.group(1):
                alvos = _limpar_detalhes(m.group(1))
                # "Construtos ou Mortos-Vivos" → normalizar
                if "mortos" in alvos.lower() or "construtos" in alvos.lower():
                    alvos = "Construtos, Mortos-Vivos"
            else:
                alvos = "Construtos, Mortos-Vivos"
            resultado.append(HabilidadeCombate("Imune", alvos, "imunidade"))
            break
    return resultado


def extrair_restricoes(texto: str) -> list[HabilidadeCombate]:
    """Extrai restrições (incapaz de lutar, definhar)."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_INCAPAZ_LUTAR:
        if pat.search(texto):
            resultado.append(HabilidadeCombate("Incapaz de lutar", "Nunca ataca", "restricao"))
            break
    for pat in PADROES_DEFINHAR:
        if m := pat.search(texto):
            qtd = m.group(1) if m.lastindex >= 1 else "1"
            unidade = m.group(2) if m.lastindex >= 2 else "hora"
            resultado.append(
                HabilidadeCombate(
                    "Definhar fora do habitat",
                    f"Morre em {qtd} {unidade} fora do ambiente natural",
                    "restricao",
                )
            )
            break
    return resultado


def extrair_constricao(texto: str) -> list[HabilidadeCombate]:
    """Extrai constrição/esmagamento."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_CONSTRICAO:
        if m := pat.search(texto):
            dano = m.group(1) if m.lastindex else "1d6"
            resultado.append(
                HabilidadeCombate("Constrição", f"{dano} dano por rodada", "ataque")
            )
            break
    return resultado


def extrair_invulnerabilidade(texto: str) -> list[HabilidadeCombate]:
    """Extrai Invulnerabilidade (tipos de dano)."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_INVULNERABILIDADE:
        for m in pat.finditer(texto):
            if m.lastindex:
                tipos = _limpar_detalhes(m.group(1))
                resultado.append(HabilidadeCombate("Invulnerabilidade", tipos, "imunidade"))
            break
    return resultado


def extrair_vulnerabilidade(texto: str) -> list[HabilidadeCombate]:
    """Extrai Vulnerabilidade (tipos de dano)."""
    resultado: list[HabilidadeCombate] = []
    for pat in PADROES_VULNERABILIDADE:
        for m in pat.finditer(texto):
            if m.lastindex:
                tipos = _limpar_detalhes(m.group(1))
                resultado.append(HabilidadeCombate("Vulnerabilidade", tipos, "vulnerabilidade"))
            break
    return resultado


def extrair_habilidades_combate(descricao: str) -> list[dict[str, Any]]:
    """
    Extrai todas as habilidades de combate relevantes da descrição.
    Retorna lista de dicts serializáveis: {"nome": str, "detalhes": str, "tipo": str}
    """
    texto = descricao or ""
    habilidades: list[HabilidadeCombate] = []

    habilidades.extend(extrair_veneno(texto))
    habilidades.extend(extrair_testes(texto))
    habilidades.extend(extrair_efeitos_especiais(texto))
    habilidades.extend(extrair_imunidades(texto))
    habilidades.extend(extrair_restricoes(texto))
    habilidades.extend(extrair_constricao(texto))
    habilidades.extend(extrair_invulnerabilidade(texto))
    habilidades.extend(extrair_vulnerabilidade(texto))

    # Deduplicar por nome
    vistos: set[str] = set()
    unicos: list[HabilidadeCombate] = []
    for h in habilidades:
        chave = f"{h.nome}:{h.detalhes[:50]}"
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(h)

    return [{"nome": h.nome, "detalhes": h.detalhes, "tipo": h.tipo} for h in unicos]
