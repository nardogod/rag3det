"""
Extração automática de campos enriquecidos a partir da descrição e habilidades_combate.
Usado para monstros do Livro de Arton sem dados manuais (PILOTO_EXTRA/PILOTO_ARTON).
"""

from __future__ import annotations

import re
from typing import Any


def _extrair_imunidades_de_habilidades(hc: list[dict]) -> list[str] | None:
    """Extrai imunidades de habilidades_combate com tipo 'imunidade'."""
    items = []
    for h in hc or []:
        if h.get("tipo") != "imunidade":
            continue
        nome = (h.get("nome") or "").strip()
        detalhes = (h.get("detalhes") or "").strip()
        texto = f"{nome}: {detalhes}".strip() if detalhes else nome
        if texto and texto not in items:
            items.append(texto)
    return items if items else None


def _extrair_fraquezas_de_habilidades(hc: list[dict]) -> list[str] | None:
    """Extrai fraquezas de habilidades_combate com tipo 'vulnerabilidade'."""
    items = []
    for h in hc or []:
        if h.get("tipo") != "vulnerabilidade":
            continue
        nome = (h.get("nome") or "").strip()
        detalhes = (h.get("detalhes") or "").strip()
        texto = f"{nome}: {detalhes}".strip() if detalhes else nome
        if texto and texto not in items:
            items.append(texto)
    return items if items else None


def _extrair_imunidades_da_descricao(desc: str) -> list[str]:
    """Busca padrões de imunidade na descrição."""
    items = []
    desc_lower = desc.lower()
    # imunes a X, imune a X
    for m in re.finditer(
        r"imunes?\s+a\s+([^.;]+?)(?:\.|;|,|$)",
        desc_lower,
        re.IGNORECASE | re.DOTALL,
    ):
        txt = m.group(1).strip()
        if len(txt) < 80 and txt not in items:
            items.append(txt)
    # invulnerável a X
    for m in re.finditer(
        r"invulner[aá]vel\s+(?:a\s+)?([^.;]+?)(?:\.|;|,|$)",
        desc_lower,
        re.IGNORECASE | re.DOTALL,
    ):
        txt = m.group(1).strip()
        if len(txt) < 80 and txt not in items:
            items.append(txt)
    return items


def _extrair_fraquezas_da_descricao(desc: str) -> list[str]:
    """Busca padrões de fraqueza na descrição."""
    items = []
    desc_lower = desc.lower()
    for m in re.finditer(
        r"(?:fraqueza|vulner[aá]vel)\s*[:\s]+([^.;]+?)(?:\.|;|$)",
        desc_lower,
        re.IGNORECASE | re.DOTALL,
    ):
        txt = m.group(1).strip()
        if len(txt) < 100 and txt not in items:
            items.append(txt)
    return items


def _extrair_habitat_da_descricao(desc: str) -> str | None:
    """Extrai habitat a partir de padrões comuns na descrição."""
    desc_lower = desc.lower()
    # Padrões mais específicos primeiro (rondando X, podem ser vistos em X)
    patterns = [
        r"rondando\s+([^.;]+?)(?:\.|;|$)",
        r"podem\s+ser\s+vistos?\s+rondando\s+([^.;]+?)(?:\.|;|$)",
        r"encontrados?\s+em\s+([^.;]+?)(?:\.|;|$)",
        r"habita(?:m|m)?\s+([^.;]+?)(?:\.|;|$)",
        r"vivem\s+(?:em\s+)?([^.;]+?)(?:\.|;|$)",
        r"habitam\s+([^.;]+?)(?:\.|;|$)",
        r"encontra(?:m|-se)?\s+(?:em\s+)?([^.;]+?)(?:\.|;|$)",
    ]
    for pat in patterns:
        m = re.search(pat, desc_lower, re.IGNORECASE | re.DOTALL)
        if m:
            txt = m.group(1).strip() if m.lastindex else m.group(0).strip()
            # Evitar capturar "5 a 8 indivíduos" ou trechos que não são locais
            if len(txt) > 5 and len(txt) < 150 and "indivíduos" not in txt and "vítima" not in txt:
                return txt
    # Fallback: procurar palavras-chave de local e contexto
    locais = [
        "cemitérios, casas assombradas",
        "cemitérios", "florestas", "selvas", "pântanos", "cavernas",
        "masmorras", "subterrâneos", "montanhas", "rios", "lagos",
        "casas assombradas", "vales", "desertos", "templos",
    ]
    for loc in locais:
        if loc in desc_lower:
            # Expandir se houver mais contexto (ex: "cemitérios, casas assombradas e outros lugares")
            m = re.search(re.escape(loc) + r"[^.;]{0,80}", desc_lower)
            if m:
                return m.group(0).strip().rstrip(",")
            return loc
    return None


def _extrair_comportamento_da_descricao(desc: str, max_chars: int = 350) -> str | None:
    """Extrai as primeiras frases como comportamento."""
    if not desc or not desc.strip():
        return None
    # Remove quebras excessivas e normaliza
    texto = re.sub(r"\s+", " ", desc.strip())
    # Primeira frase até ponto ou limite
    match = re.match(r"^([^.]{20,}?\.)", texto)
    if match:
        return match.group(1).strip()[:max_chars]
    # Fallback: primeiros N caracteres
    if len(texto) > 30:
        return texto[:max_chars].strip()
    return None


def _extrair_comportamento_combate_da_descricao(desc: str) -> str | None:
    """Extrai trechos relacionados a combate."""
    desc_lower = desc.lower()
    # Procurar seção "Combate:" ou trechos com "ataca", "ataque", "dano"
    m = re.search(r"combate\s*[:\s]+([^.]{20,}?)(?:\.|$)", desc_lower, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()[:300]
    # Garras e bico (ataques típicos)
    m = re.search(r"([^.]{10,}?garras?\s+e\s+bico[^.]{0,100}?\.)", desc_lower)
    if m:
        return m.group(1).strip()[:300]
    # Frase com ataca/ataque (evitar "encontrados" ou "podem atacar" sem contexto de combate)
    m = re.search(r"([^.]{15,}?(?:ataca(?:m|r)?|ataque|dano|mordida|garras?|bico|ferir)[^.]{0,80}?\.)", desc_lower)
    if m:
        txt = m.group(1).strip()
        if "encontrados" not in txt[:30] and "indivíduos" not in txt[:30]:
            return txt[:300]
    return None


def _extrair_altura_tamanho_da_descricao(desc: str) -> str | None:
    """Extrai menções a tamanho/altura."""
    desc_lower = desc.lower()
    # Qualificadores de tamanho (ex.: kobold "corpos diminutos", Modelo Especial)
    if "corpos diminutos" in desc_lower or "corpo diminuto" in desc_lower:
        return "Diminuto"
    if re.search(r"\bmodelo\s+especial\s*\([^)]*grande", desc_lower):
        return "Grande"
    if re.search(r"\bmodelo\s+especial\s*\([^)]*pequeno", desc_lower):
        return "Pequeno"
    if re.search(r"\bmodelo\s+especial\s*\([^)]*diminuto", desc_lower):
        return "Diminuto"
    if re.search(r"\bdiminuto[s]?\b", desc_lower) and "corpo" in desc_lower:
        return "Diminuto"
    if re.search(r"\btamanho\s+humano\b", desc_lower):
        return "Tamanho humano"
    # Padrões: "X m de comprimento", "X cm de altura", "tamanho de X", "mede X"
    patterns = [
        r"(\d+\s*(?:m|metros?|cm|centímetros?)\s+[^.;]{5,50}?)(?:\.|;|$)",
        r"tamanho\s+(?:de\s+)?(?:um\s+)?([^.;]{5,60}?)(?:\.|;|$)",
        r"mede\s+([^.;]{5,60}?)(?:\.|;|$)",
        r"aproximadamente\s+(\d+\s*m[^.;]{0,40}?)(?:\.|;|$)",
        r"at[eé]\s+(\d+\s*m[^.;]{0,40}?)(?:\.|;|$)",
    ]
    for pat in patterns:
        m = re.search(pat, desc, re.IGNORECASE | re.DOTALL)
        if m:
            txt = m.group(1).strip()
            if 5 < len(txt) < 100:
                return txt
    return None


def _extrair_movimento_de_habilidades(monstro: dict) -> str | None:
    """Extrai movimento de habilidades (Levitação, Vôo) ou descrição."""
    habs = monstro.get("habilidades") or []
    hab_str = " ".join(str(h) for h in habs).lower()
    desc = (monstro.get("descricao") or "").lower()
    partes = []
    if "levitação" in hab_str or "levitação" in desc:
        partes.append("Levitação")
    if "vôo" in desc or "voo" in desc or "voando" in desc:
        m = re.search(r"(?:v[oô]o|voando)[^.]{0,80}(?:\d+\s*(?:km/h|m/s|m/turno)[^.]*)?", desc)
        if m:
            partes.append(m.group(0).strip()[:80])
        elif "vôo" in desc or "voo" in desc:
            partes.append("Vôo")
    if "nadar" in desc or "nado" in desc:
        m = re.search(r"nad(?:a|ar)[^.]{0,60}", desc)
        if m:
            partes.append(m.group(0).strip()[:60])
    return "; ".join(partes) if partes else None


def extrair_enriquecimento_automatico(monstro: dict[str, Any]) -> dict[str, Any]:
    """
    Extrai campos enriquecidos automaticamente da descrição e habilidades_combate.
    Retorna apenas os campos que conseguiu extrair (não sobrescreve None com vazio).
    """
    out: dict[str, Any] = {}
    desc = (monstro.get("descricao") or "").strip()
    hc = monstro.get("habilidades_combate") or []

    # 1. Imunidades: prioridade habilidades_combate, depois descrição
    imm = _extrair_imunidades_de_habilidades(hc)
    if imm:
        out["imunidades"] = imm
    else:
        imm_desc = _extrair_imunidades_da_descricao(desc)
        if imm_desc:
            out["imunidades"] = imm_desc

    # 2. Fraquezas: prioridade habilidades_combate, depois descrição
    frq = _extrair_fraquezas_de_habilidades(hc)
    if frq:
        out["fraquezas"] = frq
    else:
        frq_desc = _extrair_fraquezas_da_descricao(desc)
        if frq_desc:
            out["fraquezas"] = frq_desc

    # 3. Comportamento
    comp = _extrair_comportamento_da_descricao(desc)
    if comp:
        out["comportamento"] = comp

    # 4. Habitat
    hab = _extrair_habitat_da_descricao(desc)
    if hab:
        out["habitat"] = hab

    # 5. Comportamento em combate
    comb = _extrair_comportamento_combate_da_descricao(desc)
    if comb:
        out["comportamento_combate"] = comb

    # 6. Altura/tamanho
    alt = _extrair_altura_tamanho_da_descricao(desc)
    if alt:
        out["altura_tamanho"] = alt

    # 7. Movimento
    mov = _extrair_movimento_de_habilidades(monstro)
    if mov:
        out["movimento"] = mov

    return out
