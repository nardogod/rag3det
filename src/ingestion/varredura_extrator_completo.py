"""
Varredura completa da descrição: extrai o máximo possível de campos.
Usa padrões ampliados para monstros longos (ex.: Minotauro).
Complementa extrator_descricao_automatico.py com regras adicionais.
"""

from __future__ import annotations

import re
from typing import Any

from src.ingestion.extrator_descricao_automatico import extrair_enriquecimento_automatico


def _normalizar_ocr(texto: str) -> str:
    """Corrige erros OCR comuns para melhor matching."""
    t = texto
    t = re.sub(r"1\s*\\\s*", "", t)
    t = re.sub(r"l\\|r\\|J\\|I\\", "", t)
    t = re.sub(r"~", "", t)
    t = re.sub(r"con1prar", "comprar", t, flags=re.I)
    t = re.sub(r"perden1|perdem1", "perdem", t, flags=re.I)
    t = re.sub(r"nunc:a|nunca\s*:", "nunca", t, flags=re.I)  # OCR: NUNC:A
    t = re.sub(r"en1\s", "em ", t, flags=re.I)  # "en1 " = "em "
    t = re.sub(r"catacu1nbas", "catacumbas", t, flags=re.I)
    t = re.sub(r"n1(?!\d)", "n", t, flags=re.I)  # n1→n exceto em números
    return t


def _extrair_altura_tamanho_varredura(desc: str) -> str | None:
    """Varredura ampliada para tamanho/altura."""
    desc_lower = desc.lower()
    # Qualificadores de tamanho (kobold "corpos diminutos", etc.)
    if "corpos diminutos" in desc_lower or "corpo diminuto" in desc_lower:
        return "Diminuto"
    if re.search(r"modelo\s+especial\s*\([^)]*grande", desc_lower):
        return "Grande"
    if re.search(r"modelo\s+especial\s*\([^)]*pequeno", desc_lower):
        return "Pequeno"
    if re.search(r"modelo\s+especial\s*\([^)]*diminuto", desc_lower):
        return "Diminuto"
    if re.search(r"\btamanho\s+humano\b", desc_lower):
        return "Tamanho humano"
    # "em média 1,90 m de altura", "1,901n" (OCR: 1n=m)
    m = re.search(
        r"(?:em\s+m[eé]dia\s+)?(\d+[,.]?\d*)\s*(?:m|metros?|n1|1n)\s*(?:de\s+)?(?:altura|comprimento)",
        desc,
        re.I,
    )
    if m:
        num = m.group(1).replace(",", ".")
        return f"{num} m de altura"
    # "entre X e Y m"
    m = re.search(r"entre\s+(\d+[,.]?\d*)\s*(?:m|n1)\s+e\s+(\d+)\s*(?:m|metros?)", desc, re.I)
    if m:
        return f"entre {m.group(1)} e {m.group(2)} m"
    # "grande estatura (em média X m)"
    m = re.search(r"grande\s+estatura\s*\([^)]*?(\d+[,.]?\d*)\s*(?:m|n1)[^)]*\)", desc, re.I)
    if m:
        return f"Grande estatura (em média {m.group(1)} m)"
    return None


def _extrair_habitat_varredura(desc: str) -> str | None:
    """Varredura ampliada para habitat/reino/nação."""
    desc_norm = _normalizar_ocr(desc)
    desc_lower = desc_norm.lower()
    # "Tapista", "Reino dos Minotauros", "em Tapista"
    m = re.search(r"(?:em\s+)?(Tapista)(?:\s*[,\-]?\s*(?:o\s+)?[Rr]eino\s+dos\s+[\w\-]+)?", desc, re.I)
    if m:
        return "Tapista (Reino dos Minotauros)"
    # "sua própria nação", "Reino de X"
    m = re.search(r"[Rr]eino\s+(?:de\s+)?([^.;,]+?)(?:\.|;|,|$)", desc)
    if m:
        return m.group(1).strip()
    # "habitam X", "vivem em X"
    m = re.search(r"(?:habitam|vivem\s+em)\s+([^.;]{5,80}?)(?:\.|;|$)", desc_lower)
    if m:
        return m.group(1).strip()
    return None


def _extrair_fraquezas_varredura(desc: str) -> list[str] | None:
    """Varredura ampliada para fraquezas."""
    items = []
    desc_lower = desc.lower()
    # "medo de altura", "qualquer altura superior a Xm provoca Magia Pânico"
    if "medo de altura" in desc_lower or "medo de altu" in desc_lower:
        m = re.search(
            r"(?:qualquer\s+)?altura\s+superior\s+a\s+(\d+)\s*m[^.]*?(?:Pânico|pânico)[^.]*?\.?",
            desc_lower,
            re.I | re.DOTALL,
        )
        if m:
            items.append(f"Medo de altura: acima de {m.group(1)} m provoca Magia Pânico (Teste de R+2)")
        else:
            items.append("Medo de altura")
    # "Fraqueza: X"
    for m in re.finditer(r"[Ff]raqueza\s*[:\s]+([^.;]{10,120}?)(?:\.|;|$)", desc):
        items.append(m.group(1).strip())
    # "vulnerável a X"
    for m in re.finditer(r"vulner[aá]vel\s+(?:a\s+)?([^.;]{5,80}?)(?:\.|;|$)", desc_lower):
        items.append(m.group(1).strip())
    return items if items else None


def _extrair_comportamento_combate_varredura(desc: str) -> str | None:
    """Varredura ampliada para regras de combate/honra."""
    desc_lower = desc.lower()
    partes = []
    # "nunca usam armas superiores", "nunca atacam caídos"
    m = re.search(
        r"([^.]{10,}?nunca\s+(?:usam|atacam|montam)[^.]{20,}?\.)",
        desc_lower,
        re.I,
    )
    if m:
        partes.append(m.group(1).strip())
    # "grande senso de honra em combate"
    m = re.search(
        r"([^.]{10,}?senso\s+de\s+honra\s+em\s+combate[^.]{0,150}?\.)",
        desc_lower,
        re.I,
    )
    if m:
        partes.append(m.group(1).strip())
    # "Código de Honra do Combate"
    if "código de honra" in desc_lower or "c~ódigo de honra" in desc_lower:
        m = re.search(
            r"([^.]{5,}?nunca\s+(?:usam|atacam)[^.]{0,100}?\.)",
            desc_lower,
            re.I,
        )
        if m and m.group(1) not in str(partes):
            partes.append(m.group(1).strip())
    return "; ".join(partes)[:400] if partes else None


def _extrair_habilidades_extra_varredura(desc: str) -> str | None:
    """Varredura ampliada para habilidades especiais."""
    desc_norm = _normalizar_ocr(desc)
    desc_lower = desc_norm.lower()
    partes = []
    # "nunca se perdem em catacumbas/labirintos" (OCR: perden1→perdem)
    if "nunca se perdem" in desc_lower or "nunca se perde" in desc_lower:
        m = re.search(
            r"([^.]{10,}?nunca\s+se\s+perdem?\s+(?:em\s+)?[^.]{15,}?(?:catacumbas|labirintos|t[uú]neis)[^.]{0,80}?\.)",
            desc_norm,
            re.I,
        )
        if m:
            partes.append(m.group(1).strip())
        else:
            m = re.search(r"([^.]{10,}?nunca\s+se\s+perdem[^.]{20,}?\.)", desc_norm, re.I)
            if m:
                partes.append(m.group(1).strip())
    # "memorizar o trajeto", "achar o caminho de volta"
    if "memorizar" in desc_lower and ("trajeto" in desc_lower or "túneis" in desc_lower):
        m = re.search(
            r"([^.]{15,}?memorizar[^.]{0,80}?\.)",
            desc_lower,
            re.I,
        )
        if m:
            partes.append(m.group(1).strip())
    # "Invulnerabilidade", "Paralisia" (já em habilidades, mas pode ter detalhes)
    if "invulnerabilidade" in desc_lower and "invulnerabilidade" not in str(partes).lower():
        m = re.search(r"[Ii]nvulnerabilidade\s*(?:a\s+)?[^.]{0,60}", desc)
        if m:
            partes.append(m.group(0).strip())
    return "; ".join(partes)[:350] if partes else None


def _extrair_uso_cultural_varredura(desc: str) -> str | None:
    """Varredura para uso como Vantagem Única / PJ."""
    desc_norm = _normalizar_ocr(desc)
    desc_lower = desc_norm.lower()
    # "Personagens Jogadores podem comprar X como Vantagem Única" (OCR: con1prar)
    m = re.search(
        r"[Pp]ersonagens?\s+[Jj]ogadores?\s+podem\s+comprar\s+.{5,150}?[Vv]antagem\s+[Uuú]nica",
        desc_norm,
        re.I | re.DOTALL,
    )
    if m:
        return m.group(0).strip()[:300]
    # Fallback: só "Personagens Jogadores podem comprar"
    if "personagens" in desc_lower and "jogadores" in desc_lower and "comprar" in desc_lower and "vantagem" in desc_lower:
        m = re.search(r"[Pp]ersonagens?\s+[Jj]ogadores?\s+podem\s+comprar\s+.{5,200}?[Vv]antagem", desc_norm, re.I | re.DOTALL)
        if m:
            return m.group(0).strip()[:300]
    # "Vantagem Única", "custa N pontos"
    if "vantagem única" in desc_lower:
        m = re.search(
            r"([^.]{10,}?[Vv]antagem\s+[Uu]nica[^.]{0,80}?\.?)",
            desc,
            re.I,
        )
        if m:
            return m.group(1).strip()
    return None


def _extrair_recuperacao_varredura(desc: str) -> str | None:
    """Varredura para recuperação de PVs (dissolvem, reformam)."""
    desc_lower = desc.lower()
    m = re.search(
        r"([^.]{10,}?dissolv(?:em|em na)[^.]{0,80}?\.)",
        desc_lower,
        re.I,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r"([^.]{10,}?reform(?:am|am em)[^.]{0,80}?\.)",
        desc_lower,
        re.I,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r"([^.]{10,}?jamais\s+destru[ií]dos[^.]{0,60}?\.)",
        desc_lower,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def _extrair_origem_varredura(desc: str) -> str | None:
    """Varredura para origem/criação."""
    desc_lower = desc.lower()
    # "apenas a gentil Deusa da Cura poderia ter sido responsável pela criação"
    m = re.search(
        r"([^.]{15,}?(?:criação|criados?|criou)[^.]{0,80}?\.)",
        desc,
        re.I,
    )
    if m:
        return m.group(1).strip()
    # "nascem em X", "formam-se em X"
    m = re.search(
        r"(?:nascem|formam-se)\s+em\s+([^.;]{10,80}?)(?:\.|;|$)",
        desc_lower,
        re.I,
    )
    if m:
        return m.group(0).strip()
    return None


def _extrair_comportamento_varredura_longa(desc: str, max_chars: int = 800) -> str | None:
    """Comportamento: usa mais da descrição (2-4 frases ou parágrafos)."""
    if not desc or len(desc.strip()) < 30:
        return None
    texto = re.sub(r"\s+", " ", desc.strip())
    # Primeiras 2-4 frases (até ~800 chars)
    frases = re.findall(r"[^.]{15,}?\.", texto)
    if frases:
        acum = ""
        for f in frases[:4]:
            if len(acum) + len(f) <= max_chars:
                acum += f
            else:
                break
        if acum:
            return acum.strip()
    return texto[:max_chars].strip() if len(texto) > 30 else None


def varredura_completa(monstro: dict[str, Any]) -> dict[str, Any]:
    """
    Executa varredura completa na descrição.
    Primeiro roda o extrator automático; depois complementa com padrões adicionais.
    """
    # 1. Extração base
    out = extrair_enriquecimento_automatico(monstro)
    desc = (monstro.get("descricao") or "").strip()
    if not desc:
        return out

    # 2. Comportamento: usar mais texto para descrições longas
    if len(desc) > 500:
        comp_longo = _extrair_comportamento_varredura_longa(desc)
        if comp_longo and (not out.get("comportamento") or len(out.get("comportamento", "")) < 200):
            out["comportamento"] = comp_longo

    # 3. Altura/tamanho: padrões ampliados
    if not out.get("altura_tamanho"):
        alt = _extrair_altura_tamanho_varredura(desc)
        if alt:
            out["altura_tamanho"] = alt

    # 4. Habitat: reinos, nações (Tapista tem prioridade sobre "florestas, pântanos")
    hab = _extrair_habitat_varredura(desc)
    if hab:
        out["habitat"] = hab

    # 5. Fraquezas: medo de altura, etc.
    if not out.get("fraquezas"):
        frq = _extrair_fraquezas_varredura(desc)
        if frq:
            out["fraquezas"] = frq

    # 6. Comportamento combate: honra, nunca atacam
    if not out.get("comportamento_combate"):
        comb = _extrair_comportamento_combate_varredura(desc)
        if comb:
            out["comportamento_combate"] = comb

    # 7. Habilidades extra: nunca se perdem, etc.
    if not out.get("habilidades_extra"):
        hab_extra = _extrair_habilidades_extra_varredura(desc)
        if hab_extra:
            out["habilidades_extra"] = hab_extra

    # 8. Uso cultural: Vantagem Única
    uso = _extrair_uso_cultural_varredura(desc)
    if uso:
        out["uso_cultural"] = uso

    # 9. Origem criação
    if not out.get("origem_criacao"):
        orig = _extrair_origem_varredura(desc)
        if orig:
            out["origem_criacao"] = orig

    # 10. Recuperação PV
    if not out.get("recuperacao_pv"):
        rec = _extrair_recuperacao_varredura(desc)
        if rec:
            out["recuperacao_pv"] = rec

    return out
