"""
Inferência de propriedades por TIPO de entidade (3D&T).

- MAGIA: cost_pm, school, element, duration, range, damage — NUNCA stats F/H/R/A.
- MONSTRO: stats (F/H/R/A), PV, PM, iniciativa, immunities, weaknesses.
- ITEM: preço PE, bônus; pode ter stats se arma/armadura (FA/FD).

Validação cruzada: remove stats de MAGIA; limpa valores (artefatos de parsing).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

# Trechos que indicam descrição/regra, não definição de entidade
PHANTOM_PATTERNS = re.compile(
    r"\b(teste\s+de|deve\s+ser|se\s+falhar|se\s+passar|rolagem\s+de|jogador\s+deve)\b",
    re.IGNORECASE,
)

# Padrões só para MONSTRO (seção Monstros/Bestiário)
PATTERNS_MONSTRO = {
    "stats": re.compile(
        r"\bF[:\s]*(\d+)[\- ]*H[:\s]*(\d+)[\- ]*R[:\s]*(\d+)[\- ]*A[:\s]*(\d+)\b",
        re.IGNORECASE,
    ),
    "pv": re.compile(r"\bPV[:\s]*(\d+)\b", re.IGNORECASE),
    "pm": re.compile(r"\bPM[:\s]*(\d+)\b", re.IGNORECASE),
    "initiative": re.compile(r"iniciativa[:\s]*([^\n,.]{3,30})", re.IGNORECASE),
    "immunities": re.compile(r"imune[s]?\s+a[:\s]*([^\n,.]{3,50})", re.IGNORECASE),
    "weaknesses": re.compile(
        r"(?:fraqueza[s]?|vulnerabilidade[s]?)[:\s]*([^\n,.]{3,50})",
        re.IGNORECASE,
    ),
}

# Padrões só para MAGIA (seção Magias ou contexto com custa/PM/duração)
PATTERNS_MAGIA = {
    "cost_pm": re.compile(r"custa?[:\s]*(\d+)\s*PM", re.IGNORECASE),
    "school": re.compile(r"escola[:\s]*([^\n,.]{3,20})", re.IGNORECASE),
    "element": re.compile(r"elemento[:\s]*([^\n,.]{3,20})", re.IGNORECASE),
    "duration": re.compile(r"dura[cç][aã]o[:\s]*([^\n,.]{3,30})", re.IGNORECASE),
    "range": re.compile(r"alcance[:\s]*([^\n,.]{3,30})", re.IGNORECASE),
    "damage": re.compile(r"(\d+)d(\d+)(?:\s*\+\s*(\d+))?", re.IGNORECASE),
}

# Padrões para ITEM (Equipamentos/Tesouros)
PATTERNS_ITEM = {
    "preco_pe": re.compile(r"(\d+)\s*PEs?", re.IGNORECASE),
    "bonus": re.compile(r"bônus[:\s]*([+-]?\d+)\s*(?:em\s)?([^\n,.]{3,20})?", re.IGNORECASE),
    "stats": re.compile(
        r"\bF[:\s]*(\d+)[\- ]*H[:\s]*(\d+)[\- ]*R[:\s]*(\d+)[\- ]*A[:\s]*(\d+)\b",
        re.IGNORECASE,
    ),
}

# Valor que parece número de página → ignorar
PAGE_LIKE = re.compile(r"^\s*(?:pg\.?|pág\.?)\s*\d+\s*$", re.IGNORECASE)
# Artefatos de parsing: "a 8", "a 20"
ARTIFACT_PREFIX = re.compile(r"^\s*a\s+(\d+)\s*$", re.IGNORECASE)


def _is_phantom_context(ctx: str) -> bool:
    return bool(PHANTOM_PATTERNS.search(ctx))


def _clean_value(val: str, max_len: int = 50) -> str | None:
    """Remove artefatos ('a 8'), ignora valor tipo página ('pg 45'), normaliza espaço."""
    if not val or not isinstance(val, str):
        return None
    s = val.strip()
    if not s or len(s) > max_len:
        return None
    if PAGE_LIKE.match(s):
        return None
    m = ARTIFACT_PREFIX.match(s)
    if m:
        s = m.group(1)
    return " ".join(s.split()) or None


def _normalize_number(val: str) -> int | None:
    """Extrai número; 'F: 4' -> 4, '1-2' pode retornar primeiro ou média."""
    if val is None:
        return None
    s = str(val).strip()
    m = re.search(r"(\d+)", s)
    if m:
        return int(m.group(1))
    return None


def _extract_by_type(
    text: str,
    etype: str,
) -> tuple[Dict[str, Any], Dict[str, str]]:
    """
    Extrai propriedades aplicando apenas os padrões do tipo.
    Retorna (properties, evidence).
    """
    props: Dict[str, Any] = {}
    evidence: Dict[str, str] = {}

    if etype == "MONSTRO":
        for key, pattern in PATTERNS_MONSTRO.items():
            m = pattern.search(text)
            if m:
                if key == "stats" and len(m.groups()) >= 4:
                    f, h, r, a = m.group(1), m.group(2), m.group(3), m.group(4)
                    props["stats"] = f"F:{f} H:{h} R:{r} A:{a}"
                    evidence["stats"] = m.group(0)
                elif key in ("pv", "pm"):
                    props[key] = int(m.group(1))
                    evidence[key] = m.group(0)
                elif key == "initiative":
                    v = _clean_value(m.group(1).strip(), 30)
                    if v:
                        props[key] = v
                        evidence[key] = m.group(0)
                elif key in ("immunities", "weaknesses"):
                    v = _clean_value(m.group(1).strip(), 50)
                    if v:
                        props[key] = [x.strip() for x in re.split(r"[,;]", v) if x.strip()]
                        evidence[key] = m.group(0)
    elif etype == "MAGIA":
        for key, pattern in PATTERNS_MAGIA.items():
            m = pattern.search(text)
            if m:
                if key == "cost_pm":
                    props["cost_pm"] = int(m.group(1))
                    evidence["cost_pm"] = m.group(0)
                elif key == "damage":
                    x, y = m.group(1), m.group(2)
                    plus = m.group(3)
                    props["damage"] = f"{x}d{y}" + (f"+{plus}" if plus else "")
                    evidence["damage"] = m.group(0)
                else:
                    v = _clean_value(m.group(1).strip(), 30)
                    if v:
                        props[key] = v
                        evidence[key] = m.group(0)
    elif etype == "ITEM":
        for key, pattern in PATTERNS_ITEM.items():
            m = pattern.search(text)
            if m:
                if key == "preco_pe":
                    props["preco_pe"] = int(m.group(1))
                    evidence["preco_pe"] = m.group(0)
                elif key == "bonus":
                    num = m.group(1)
                    rest = m.group(2).strip() if m.lastindex >= 2 and m.group(2) else ""
                    props["bonus"] = num + (" " + rest if rest else "")
                    evidence["bonus"] = m.group(0)
                elif key == "stats" and len(m.groups()) >= 4:
                    props["stats"] = f"F:{m.group(1)} H:{m.group(2)} R:{m.group(3)} A:{m.group(4)}"
                    evidence["stats"] = m.group(0)
    else:
        # ENTIDADE ou outro: só propriedades que não são exclusivas (ex.: cost_pm pode aparecer em texto de magia)
        for key, pattern in PATTERNS_MAGIA.items():
            if key == "stats":
                continue
            m = pattern.search(text)
            if m:
                if key == "cost_pm":
                    props["cost_pm"] = int(m.group(1))
                    evidence["cost_pm"] = m.group(0)
                else:
                    v = _clean_value(m.group(1).strip(), 30)
                    if v:
                        props[key] = v
                        evidence[key] = m.group(0)

    return props, evidence


def _cross_validate(etype: str, props: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validação cruzada: MAGIA não pode ter stats F/H/R/A (remove se presente).
    """
    out = {k: v for k, v in props.items() if not k.startswith("_")}
    if etype == "MAGIA":
        out.pop("stats", None)
        out.setdefault("stats", None)
    if etype == "MONSTRO":
        out.setdefault("pv", None)
        out.setdefault("pm", None)
    return out


def infer_properties_from_entities(
    entities_path: Path,
    output_path: Path,
) -> Dict[str, Dict[str, Any]]:
    """
    Lê entidades e infere propriedades SOMENTE pelos padrões do tipo.
    MAGIA nunca recebe stats; MONSTRO recebe stats, PV, PM, etc.
    """
    if not entities_path.exists():
        return {}

    with entities_path.open("r", encoding="utf-8") as f:
        entities = json.load(f)

    out: Dict[str, Dict[str, Any]] = {}
    for name, data in entities.items():
        etype = (data.get("type") or "ENTIDADE").upper()
        if etype not in ("MAGIA", "MONSTRO", "ITEM", "ENTIDADE", "VANTAGEM", "DESVANTAGEM", "PERÍCIA", "ATRIBUTO", "CAPÍTULO"):
            etype = "ENTIDADE"
        contexts = data.get("contexts") or []
        all_props: Dict[str, Any] = {}
        all_evidence: Dict[str, str] = {}
        for ctx in contexts:
            if _is_phantom_context(ctx):
                continue
            props, ev = _extract_by_type(ctx, etype)
            for k, v in props.items():
                if k.startswith("_"):
                    continue
                if k not in all_props:
                    all_props[k] = v
                    if k in ev:
                        all_evidence[k] = ev[k]
        if data.get("stats") and etype == "MONSTRO" and "stats" not in all_props:
            all_props["stats"] = data["stats"]
        all_props = _cross_validate(etype, all_props)
        entry: Dict[str, Any] = {
            "type": etype,
            "properties": all_props,
            "evidence": all_evidence,
        }
        sources = data.get("sources") or []
        if sources:
            entry["stats_source"] = sources[0] if isinstance(sources[0], str) else str(sources[0])
        out[name] = entry

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out
