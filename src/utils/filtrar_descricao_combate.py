"""
Filtra descrições de monstros mantendo apenas conteúdo relevante para combate.
Remove lore, habitat, personalidade e aparência pura.
Preserva: fórmulas (FA, FD), sopro, magias, ataques, resistências, vulnerabilidades, etc.
"""

from __future__ import annotations

import re


# Padrões que indicam conteúdo de combate
_COMBATE_PATTERNS = [
    # Fórmulas
    r"FA\s*[=\(]",
    r"FD\s*[=\(]",
    r"\d+d\s*[\+\-]?\s*\d*",  # 1d+3, 2d, 3d6
    r"PdF\s*\d",
    r"[FHRA]\s*[\+\-]\s*\d*d?",
    # Seções típicas
    r"Combate\s*:",
    r"Sopro\s*:",
    r"Magias?\s*:",
    r"Voo\s*:",
    r"Voô\s*:",
    r"Ataque\s*:",
    r"Habilidades?\s*:",
    r"Invulnerabilidade",
    r"Vulnerabilidade",
    r"Resistência",
    r"Paralisia",
    r"Veneno",
    r"Constrição",
    r"Mordida",
    r"Garras",
    r"Sopro",
    # Termos de combate
    r"ataca\w*",
    r"golpeia",
    r"causa\s+dano",
    r"teste\s+de\s+[RHF]",
    r"falhar\s+em",
    r"PV\s*[:\s]",
    r"PM\s*[:\s]",
    r"rodada",
    r"turno",
    r"imune",
    r"imunidade",
    r"fraqueza",
    r"ferir",
    r"acertar",
    r"velocidade",
    r"km/h",
    r"m/s",
    r"dano\s+(por|instantâneo|automático)",
    r"morte\s+(se|ao)",
    r"redutor\s+(temporário|de)",
    r"vantagem\s+\w+",
    r"desvantagem",
    r"armadura\s+extra",
    r"membros\s+elásticos",
    r"magia\s+(de|elemental)",
    r"escola\s+\w+",
    r"em combate",
    r"combate\s+(corporal|aéreo)",
    r"abençoados?\s+com\s+sorte",
    r"fazem\s+\d+\s+ataques?",
    r"ataques?\s+por\s+turno",
    r"mordida\s*\(|garras\s*\(",
    r"ferrão",
    r"agarrar",
    r"presa",
]

_COMBATE_REGEX = re.compile(
    "|".join(f"({p})" for p in _COMBATE_PATTERNS),
    re.IGNORECASE,
)

# Frases/blocos que são intro genérica ou lore puro (remover)
_LORE_MARKERS = (
    "são criaturas",
    "são uma raça",
    "medem ",
    "pesam ",
    "têm cerca de",
    "cheira a",
    "brilham como",
    "se assemelham",
    "lembram ",
    "podem viver em",
    "habitam ",
    "vivem em",
    "encontrados em",
    "geralmente se disfarçam",
    "odeiam ",
    "adoram ",
    "preferem ",
    "costumam se sustentar",
    "— ",  # citações de personagens no início
)


def _bloco_relevante_combate(bloco: str) -> bool:
    """Retorna True se o bloco contém informação relevante para combate."""
    if not bloco or len(bloco.strip()) < 15:
        return False
    bloco_lower = bloco.lower()
    # Contém padrão de combate
    if _COMBATE_REGEX.search(bloco):
        return True
    # É seção explícita de combate
    if any(
        bloco_lower.strip().startswith(s)
        for s in ("combate:", "sopro:", "magias:", "voo:", "voô:", "ataque:", "habilidades:")
    ):
        return True
    return False


def _bloco_e_lore_puro(bloco: str) -> bool:
    """Retorna True se o bloco é apenas lore/descrição física, sem combate."""
    if not bloco or len(bloco.strip()) < 20:
        return True  # blocos muito curtos descartar
    bloco_lower = bloco.lower()
    if _COMBATE_REGEX.search(bloco):
        return False  # tem combate
    # Começa com marcador de lore
    if any(bloco_lower.strip().startswith(m) for m in _LORE_MARKERS):
        return True
    # Frase muito curta sobre aparência
    if len(bloco.split()) < 12 and any(
        w in bloco_lower for w in ["cor ", "olhos", "escamas", "chifres", "asas", "cauda"]
    ):
        return True
    return False


def filtrar_descricao_combate(descricao: str) -> str:
    """
    Filtra a descrição mantendo apenas trechos relevantes para combate.
    Remove lore, habitat, personalidade e descrição física pura.
    Preserva fórmulas, ataques, sopro, magias, resistências, etc.
    """
    if not descricao or not descricao.strip():
        return ""

    texto = re.sub(r"\s+", " ", descricao.strip())
    texto = re.sub(r"\s*\.\s*", ". ", texto)

    # 1. Extrair seções explícitas (Combate:, Sopro:, Magias:, Voo:) — até a próxima seção ou fim
    section_headers = r"(Combate\s*:|Sopro\s*:|Magias?\s*:|Voo\s*:|Voô\s*:|Ataque\s*:|Habilidades?\s*:)"
    partes = re.split(rf"({section_headers})", texto, flags=re.IGNORECASE)
    blocos = []
    i = 1
    while i < len(partes):
        if re.match(section_headers, partes[i], re.IGNORECASE):
            header = partes[i].strip()
            conteudo = (partes[i + 1] if i + 1 < len(partes) else "").strip()
            # Pegar até próximo header ou fim
            next_header = re.search(rf"(?={section_headers})", conteudo, re.IGNORECASE)
            if next_header:
                conteudo = conteudo[: next_header.start()].strip()
            if conteudo:
                blocos.append(header + " " + conteudo)
            i += 2
        else:
            i += 1

    # 2. Resto do texto: frases que contêm indicadores de combate
    texto_sem_secoes = texto
    for b in blocos:
        texto_sem_secoes = texto_sem_secoes.replace(b, " ", 1)
    frases = [f.strip() for f in re.split(r"\.\s+", texto_sem_secoes) if f.strip()]

    for frase in frases:
        if len(frase) < 15:
            continue
        if _COMBATE_REGEX.search(frase) and not _bloco_e_lore_puro(frase):
            txt = frase + "." if not frase.endswith(".") else frase
            if txt not in blocos:
                blocos.append(txt)

    # Desduplicar mantendo ordem
    seen = set()
    resultado = []
    for b in blocos:
        bn = re.sub(r"\s+", " ", b).strip()
        if bn and bn not in seen:
            seen.add(bn)
            resultado.append(bn)

    saida = " ".join(resultado)
    saida = re.sub(r"\s+", " ", saida).strip()
    if len(saida) > 12000:
        saida = saida[:12000].rsplit(". ", 1)[0] + "."
    return saida
