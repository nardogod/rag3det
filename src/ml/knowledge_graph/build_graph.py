"""
Grafo de conhecimento a partir dos textos: extração de relações entre entidades.

Padrões:
  - "X é Y", "X são Y", "X é um tipo de Y" → is_a
  - "X custa Y", "X gasta Y" → cost
  - "X requer Y", "X necessita Y" → requires
  - "X causa Y", "X inflige Y" → effect
  - "X é fraco contra Y" → weakness
  - "escola: X", "elemento: X" → school / element
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

logger = None

def _logger():
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
    return logger


# Padrões de relação (regex, grupo 1 = sujeito, grupo 2 = objeto, relation type)
RELATION_PATTERNS = [
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+é\s+(?:um|uma|uns|umas)?\s*(?:tipo\s+de\s+)?([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "is_a"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+são\s+([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "is_a"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+custa\s+(\d+)\s*PM", re.IGNORECASE), "cost_pm"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+gasta\s+(\d+)\s*PM", re.IGNORECASE), "cost_pm"),
    (re.compile(r"custo\s*:?\s*(\d+)\s*PM", re.IGNORECASE), "cost_pm_value"),  # usa entidade do contexto
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+requer\s+([A-Za-záéíóúâêôãõçÀ-ÿ0-9\s\-'+]+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "requires"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+necessita\s+([A-Za-záéíóúâêôãõçÀ-ÿ0-9\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "requires"),
    (re.compile(r"escola\s*:?\s*([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "school"),
    (re.compile(r"elemento\s*:?\s*([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "element"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+é\s+fraco\s+contra\s+([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "weakness"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+causa\s+([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "effect"),
    (re.compile(r"([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)\s+inflige\s+([A-Za-záéíóúâêôãõçÀ-ÿ\s\-']+?)(?:\.|,|;|\n|$)", re.IGNORECASE), "effect"),
]


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().split())[:80]


def _extract_relations_from_text(
    text: str, entity_names: List[str], context_entity: str | None = None
) -> List[Dict[str, Any]]:
    """Extrai relações a partir de um texto. context_entity = entidade a que o texto se refere."""
    relations = []
    seen = set()
    text_lower = text.lower()
    for pattern, rel_type in RELATION_PATTERNS:
        for m in pattern.finditer(text):
            if rel_type == "cost_pm_value":
                source = context_entity
                if not source:
                    for name in entity_names:
                        if name.lower() in text_lower and len(name) > 3:
                            source = name
                            break
                if source:
                    key = (source, "cost_pm", m.group(1))
                    if key not in seen:
                        seen.add(key)
                        relations.append({
                            "source": _normalize(source),
                            "relation": "cost_pm",
                            "target": m.group(1).strip(),
                            "evidence": text[max(0, m.start() - 30) : m.end() + 30].replace("\n", " "),
                        })
                continue
            if pattern.groups >= 1:
                if pattern.groups >= 2:
                    g1, g2 = m.group(1), m.group(2)
                    source = _normalize(g1)
                    target = _normalize(g2)
                else:
                    source = _normalize(context_entity or "")
                    target = _normalize(m.group(1))
                if len(source) < 2 or len(target) < 2:
                    continue
                key = (source, rel_type, target)
                if key not in seen:
                    seen.add(key)
                    relations.append({
                        "source": source,
                        "relation": rel_type,
                        "target": target,
                        "evidence": text[max(0, m.start() - 20) : m.end() + 40].replace("\n", " "),
                    })
    return relations


def build_relations(
    entities_path: Path,
    output_path: Path,
    contexts_from_entities: bool = True,
) -> List[Dict[str, Any]]:
    """
    Lê entities.json e extrai relações dos contexts de cada entidade.
    Salva em relations.json.
    """
    if not entities_path.exists():
        _logger().warning("Arquivo de entidades não encontrado: %s", entities_path)
        return []

    with entities_path.open("r", encoding="utf-8") as f:
        entities = json.load(f)

    entity_names = list(entities.keys())
    all_relations: List[Dict[str, Any]] = []
    seen_keys = set()

    for name, data in entities.items():
        contexts = data.get("contexts") or []
        for ctx in contexts:
            for rel in _extract_relations_from_text(ctx, entity_names, context_entity=name):
                rkey = (rel["source"], rel["relation"], rel["target"])
                if rkey not in seen_keys:
                    seen_keys.add(rkey)
                    all_relations.append(rel)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out = {"relations": all_relations}
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    _logger().info("Grafo: %d relações salvas em %s", len(all_relations), output_path)
    return all_relations
