"""
Métricas de qualidade do conhecimento extraído (entidades, propriedades, grafo, taxonomia).

- Completeness: % de propriedades esperadas preenchidas por tipo (MAGIA, MONSTRO).
- Consistency: mesma propriedade mesmo valor em múltiplas fontes (quando aplicável).
- Connectivity: entidades isoladas no grafo (poucas relações).
- Cluster quality: nomes de cluster genéricos (stopwords) ou muito pequenos.
- Gera recommendations e alertas se métricas abaixo de threshold.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.config import paths
from src.knowledge.base import load_entities, load_relations, load_properties, load_taxonomy
from src.ml.taxonomy.portuguese_stopwords import is_stopword

DATA_DIR = paths.data_dir
ENTITIES_CLEAN = DATA_DIR / "entities" / "extracted_entities_clean.json"
SUSPECT = DATA_DIR / "entities" / "suspect_entities.json"
PRECISION_THRESHOLD = 0.7

EXPECTED_PROPERTIES = {
    "MAGIA": ["cost_pm", "school", "element", "duration"],
    "MONSTRO": ["stats", "pv", "immunities"],
}


def _completeness(entities: dict, properties: dict) -> Dict[str, float]:
    """Por tipo, % de entidades que têm as propriedades esperadas preenchidas."""
    by_type: Dict[str, List[float]] = {}
    for name, data in entities.items():
        etype = data.get("type", "ENTIDADE")
        if etype not in EXPECTED_PROPERTIES:
            continue
        expected = EXPECTED_PROPERTIES[etype]
        props = (properties.get(name) or {}).get("properties") or {}
        filled = sum(1 for p in expected if props.get(p) not in (None, "", []))
        ratio = filled / len(expected) if expected else 0.0
        by_type.setdefault(etype, []).append(ratio)
    return {t: sum(ratios) / len(ratios) if ratios else 0.0 for t, ratios in by_type.items()}


def _connectivity(relations: list, entities: dict) -> tuple[Dict[str, int], List[str]]:
    """Conta relações por entidade (como source); retorna top isolated (0 ou 1 relação)."""
    count: Dict[str, int] = {e: 0 for e in entities}
    entity_lower = {e.lower(): e for e in entities}
    for r in relations:
        src = (r.get("source") or "").strip()
        if not src:
            continue
        key = entity_lower.get(src.lower()) or (src if src in entities else None)
        if key:
            count[key] += 1
    isolated = [e for e, n in count.items() if n <= 1]
    isolated.sort(key=lambda e: count[e])
    return count, isolated[:20]


def _cluster_quality(taxonomy: dict) -> List[str]:
    """Identifica clusters com nomes genéricos (só stopwords) ou muito pequenos."""
    bad = []
    for cid, data in taxonomy.items():
        terms = data.get("terms", data.get("common_terms", []))
        if len(data.get("entities", [])) < 2:
            bad.append(f"Cluster '{cid}' tem menos de 2 entidades")
        elif terms and all(is_stopword(t) for t in terms[:3]):
            bad.append(f"Cluster '{cid}' tem termos genéricos: {terms[:3]}")
    return bad


def evaluate_knowledge() -> Dict[str, Any]:
    """
    Calcula métricas e monta relatório de qualidade.
    """
    entities = load_entities(use_clean=True)
    if not entities and ENTITIES_CLEAN.exists():
        with ENTITIES_CLEAN.open("r", encoding="utf-8") as f:
            entities = json.load(f)
    if not entities and (DATA_DIR / "entities" / "extracted_entities.json").exists():
        with (DATA_DIR / "entities" / "extracted_entities.json").open("r", encoding="utf-8") as f:
            entities = json.load(f)
    relations = load_relations()
    properties = load_properties()
    taxonomy = load_taxonomy()
    suspect_count = 0
    if SUSPECT.exists():
        with SUSPECT.open("r", encoding="utf-8") as f:
            suspect_count = len(json.load(f))

    entities_by_type: Dict[str, int] = {}
    for data in entities.values():
        t = data.get("type", "ENTIDADE")
        entities_by_type[t] = entities_by_type.get(t, 0) + 1

    properties_coverage = _completeness(entities, properties)
    _, top_isolated = _connectivity(relations, entities)
    cluster_issues = _cluster_quality(taxonomy)

    recommendations: List[str] = []
    if properties_coverage.get("MAGIA", 0) < 0.6:
        recommendations.append("Adicionar mais regex para custo PM e escola em magias")
    if properties_coverage.get("MONSTRO", 0) < 0.5:
        recommendations.append("Adicionar mais regex para stats (F: H: R: A:) de monstros")
    if top_isolated:
        recommendations.append(f"Revisar entidades isoladas no grafo (ex.: {top_isolated[:3]})")
    for issue in cluster_issues[:3]:
        recommendations.append(issue)
    if suspect_count > len(entities):
        recommendations.append("Muitas entidades suspeitas; revisar filtros em entity_cleaner")

    precision_heuristic = 1.0 - (suspect_count / (len(entities) + suspect_count)) if (entities or suspect_count) else 0.0
    if precision_heuristic < PRECISION_THRESHOLD:
        recommendations.append(f"Precision heurística ({precision_heuristic:.2f}) abaixo de {PRECISION_THRESHOLD}")

    report = {
        "total_entities": len(entities),
        "valid_entities": len(entities),
        "suspect_entities": suspect_count,
        "entities_by_type": entities_by_type,
        "properties_coverage": properties_coverage,
        "relations_count": len(relations),
        "top_isolated_entities": top_isolated,
        "cluster_issues": cluster_issues,
        "recommendations": recommendations,
        "precision_heuristic": round(precision_heuristic, 2),
    }
    return report


def save_quality_report(report: Dict[str, Any], output_path: Path | None = None) -> Path:
    if output_path is None:
        output_path = DATA_DIR / "quality_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path
