"""
Gera dataset de triplas (anchor, positive, negative) para fine-tuning de embeddings no domínio 3D&T.

Estratégias:
  a) Pares do Grafo (40%): anchor=nome, positive=descrição+propriedades, negative=entidade de cluster distante. weight 1.0
  b) Pares de Similaridade (30%): anchor=entidade, positive=mesmo cluster, negative=cluster distante. weight 0.8
  c) Pares de Relação (20%): anchor=entidade, positive=tipo/categoria (is_a), negative=tipo oposto. weight 0.9
  d) Hard Negatives (10%): anchor=entidade, positive=mesmo tema outro tipo, negative=diferenciação sutil. weight 0.7

Formato saída: {"anchor": "...", "positive": "...", "negative": "...", "weight": float}
Mínimo 1500 triplas; divisão 85% train, 15% val.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from src.config import paths

DATA = paths.data_dir
ENTITIES_PATH = DATA / "entities" / "extracted_entities.json"
TAXONOMY_PATH = DATA / "taxonomy" / "auto_taxonomy.json"
RELATIONS_PATH = DATA / "knowledge_graph" / "relations.json"
PROPERTIES_PATH = DATA / "properties" / "entity_properties.json"
OUT_DIR = DATA / "training"

MIN_TRIPLES = 1500
RATIO_GRAPH = 0.40
RATIO_SIMILARITY = 0.30
RATIO_RELATION = 0.20
RATIO_HARD = 0.10
WEIGHT_GRAPH = 1.0
WEIGHT_SIMILARITY = 0.8
WEIGHT_RELATION = 0.9
WEIGHT_HARD = 0.7
TRAIN_RATIO = 0.85

# Nomes de tipo/categoria para pares de relação (positive para is_a)
TYPE_LABELS: Dict[str, str] = {
    "MAGIA": "Magia Elemental",
    "MONSTRO": "Monstro",
    "ITEM": "Item",
    "VANTAGEM": "Vantagem",
    "DESVANTAGEM": "Desvantagem",
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {} if path.suffix == ".json" else []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_entities() -> Tuple[Dict[str, Dict], Set[str]]:
    """Retorna (entidades dict, set de nomes válidos para anchor)."""
    data = _load_json(ENTITIES_PATH)
    if not data:
        return {}, set()
    valid = {n for n, d in data.items() if isinstance(d, dict) and d.get("type")}
    return data, valid


def _load_taxonomy() -> Tuple[Dict[str, List[str]], Dict[str, Set[str]]]:
    """Retorna (cluster_id -> list(entities), entity -> set(cluster_ids))."""
    data = _load_json(TAXONOMY_PATH)
    clusters = data.get("clusters") or {}
    cluster_entities: Dict[str, List[str]] = {}
    entity_to_clusters: Dict[str, Set[str]] = defaultdict(set)
    for cid, cinfo in clusters.items():
        if not isinstance(cinfo, dict):
            continue
        ents = cinfo.get("entities") or []
        cluster_entities[cid] = ents
        for e in ents:
            entity_to_clusters[e].add(cid)
    return cluster_entities, dict(entity_to_clusters)


def _load_properties() -> Dict[str, Dict]:
    return _load_json(PROPERTIES_PATH) or {}


def _make_description(name: str, entities: Dict, properties: Dict, max_context_chars: int = 500) -> str:
    """Descrição completa: tipo + contextos (extracted_entities) + propriedades (evidence)."""
    parts = [name]
    if name in entities and isinstance(entities[name], dict):
        e = entities[name]
        t = e.get("type", "")
        if t:
            parts.append(f"Tipo: {t}.")
        ctx = e.get("contexts") or []
        if ctx:
            combined = " ".join(ctx)[:max_context_chars]
            parts.append(combined)
    if name in properties and isinstance(properties[name], dict):
        ev = (properties[name].get("evidence") or {})
        if isinstance(ev, dict) and ev:
            parts.append("Propriedades: " + " ".join(str(v) for v in ev.values() if v))
    return " ".join(parts).strip() or name


def _entities_by_type(entities: Dict[str, Dict]) -> Dict[str, List[str]]:
    by_type: Dict[str, List[str]] = defaultdict(list)
    for name, data in entities.items():
        if not isinstance(data, dict):
            continue
        t = data.get("type")
        if t:
            by_type[t].append(name)
    return dict(by_type)


def _get_entity_type(name: str, entities: Dict[str, Dict]) -> str | None:
    d = entities.get(name)
    return d.get("type") if isinstance(d, dict) else None


def generate_graph_pairs(
    valid_names: Set[str],
    entities: Dict,
    properties: Dict,
    entity_to_clusters: Dict[str, Set[str]],
    cluster_entities: Dict[str, List[str]],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Pares do grafo: anchor=nome, positive=descrição, negative=entidade de cluster diferente."""
    out: List[Dict[str, Any]] = []
    valid_list = [n for n in valid_names if n in entities]
    if not valid_list:
        return out
    for _ in range(n_target):
        anchor = rng.choice(valid_list)
        positive = _make_description(anchor, entities, properties)
        anchor_clusters = entity_to_clusters.get(anchor) or set()
        # negative: entidade que não está em nenhum cluster do anchor (ou de outro tipo)
        other_entities = [
            e for cid, elist in cluster_entities.items()
            if cid not in anchor_clusters for e in elist if e in valid_names and e != anchor
        ]
        if not other_entities:
            other_entities = [n for n in valid_list if n != anchor]
        if not other_entities:
            continue
        neg_entity = rng.choice(other_entities)
        negative = _make_description(neg_entity, entities, properties)
        out.append({
            "anchor": anchor,
            "positive": positive,
            "negative": negative,
            "weight": WEIGHT_GRAPH,
            "strategy": "graph",
        })
    return out


def generate_similarity_pairs(
    valid_names: Set[str],
    entity_to_clusters: Dict[str, Set[str]],
    cluster_entities: Dict[str, List[str]],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Positive = mesmo cluster, negative = cluster distante."""
    out: List[Dict[str, Any]] = []
    # Só entidades que aparecem em pelo menos um cluster com outro válido
    candidates = [
        n for n in valid_names
        if entity_to_clusters.get(n) and any(
            e in valid_names and e != n
            for cid in entity_to_clusters[n]
            for e in cluster_entities.get(cid, [])
        )
    ]
    if not candidates:
        return out
    valid_list = list(valid_names)
    for _ in range(n_target):
        anchor = rng.choice(candidates)
        anchor_clusters = entity_to_clusters.get(anchor) or set()
        same_cluster = []
        for cid in anchor_clusters:
            for e in cluster_entities.get(cid, []):
                if e in valid_names and e != anchor:
                    same_cluster.append(e)
        if not same_cluster:
            continue
        positive = rng.choice(same_cluster)
        other_entities = [
            e for cid, elist in cluster_entities.items()
            if cid not in anchor_clusters for e in elist if e in valid_names and e != anchor
        ]
        if not other_entities:
            other_entities = [n for n in valid_list if n != anchor and n != positive]
        if not other_entities:
            continue
        negative = rng.choice(other_entities)
        out.append({
            "anchor": anchor,
            "positive": positive,
            "negative": negative,
            "weight": WEIGHT_SIMILARITY,
            "strategy": "similarity",
        })
    return out


def generate_relation_pairs(
    valid_names: Set[str],
    entities: Dict,
    by_type: Dict[str, List[str]],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Anchor=entidade, positive=tipo/categoria (is_a), negative=entidade de tipo oposto."""
    out: List[Dict[str, Any]] = []
    type_names = list(TYPE_LABELS.keys())
    for _ in range(n_target):
        anchor = rng.choice(list(valid_names))
        t = _get_entity_type(anchor, entities)
        if not t or t not in TYPE_LABELS:
            continue
        positive = TYPE_LABELS[t]
        # negative: outro tipo (preferir oposto: MAGIA<->MONSTRO, ITEM<->VANTAGEM)
        opposite = {"MAGIA": "MONSTRO", "MONSTRO": "MAGIA", "ITEM": "VANTAGEM", "VANTAGEM": "ITEM"}.get(t)
        if opposite and by_type.get(opposite):
            negative = rng.choice(by_type[opposite])
        else:
            other_types = [x for x in type_names if x != t and by_type.get(x)]
            if not other_types:
                continue
            other_t = rng.choice(other_types)
            negative = rng.choice(by_type[other_t])
        out.append({
            "anchor": anchor,
            "positive": positive,
            "negative": negative,
            "weight": WEIGHT_RELATION,
            "strategy": "relation",
        })
    return out


def generate_hard_negative_pairs(
    valid_names: Set[str],
    entities: Dict,
    by_type: Dict[str, List[str]],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Anchor e positive = mesmo tema (ex. fogo) tipos diferentes; negative = entidade distinta."""
    out: List[Dict[str, Any]] = []
    # Simplificação: anchor MAGIA, positive MONSTRO (ou ITEM) que compartilha tema por nome; negative outro tipo
    magia_list = by_type.get("MAGIA") or []
    monstro_list = by_type.get("MONSTRO") or []
    for _ in range(n_target):
        if not magia_list:
            break
        anchor = rng.choice(magia_list)
        if not monstro_list:
            break
        positive = rng.choice(monstro_list)
        # negative: outra magia ou item (diferenciação sutil)
        other = (by_type.get("MAGIA") or []) + (by_type.get("ITEM") or [])
        other = [x for x in other if x != anchor]
        if not other:
            continue
        negative = rng.choice(other)
        out.append({
            "anchor": anchor,
            "positive": positive,
            "negative": negative,
            "weight": WEIGHT_HARD,
            "strategy": "hard_negative",
        })
    return out


def generate_all_triples(seed: int = 42, min_triples: int = MIN_TRIPLES) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    entities, valid_names = _load_entities()
    if not valid_names:
        return []
    properties = _load_properties()
    cluster_entities, entity_to_clusters = _load_taxonomy()
    by_type = _entities_by_type(entities)

    # Garantir pelo menos min_triples; arredondar para cima para compensar amostras descartadas
    target = max(min_triples, MIN_TRIPLES)
    n_graph = max(1, int(target * RATIO_GRAPH) + 10)
    n_sim = max(1, int(target * RATIO_SIMILARITY) + 10)
    n_rel = max(1, int(target * RATIO_RELATION) + 10)
    n_hard = max(1, int(target * RATIO_HARD) + 10)

    triples: List[Dict[str, Any]] = []
    triples.extend(generate_graph_pairs(
        valid_names, entities, properties,
        entity_to_clusters, cluster_entities, n_graph, rng,
    ))
    triples.extend(generate_similarity_pairs(
        valid_names, entity_to_clusters, cluster_entities, n_sim, rng,
    ))
    triples.extend(generate_relation_pairs(
        valid_names, entities, by_type, n_rel, rng,
    ))
    triples.extend(generate_hard_negative_pairs(
        valid_names, entities, by_type, n_hard, rng,
    ))
    return triples


def validate_anchors(triples: List[Dict[str, Any]], valid_names: Set[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Remove triplas cujo anchor não está em valid_names; retorna (triplas válidas, erros)."""
    errors = []
    out = []
    for t in triples:
        a = t.get("anchor")
        if a not in valid_names:
            errors.append(f"Anchor não é entidade real: {a!r}")
            continue
        out.append(t)
    return out, errors


def split_train_val(triples: List[Dict[str, Any]], train_ratio: float = TRAIN_RATIO, seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(triples)
    rng.shuffle(shuffled)
    n = len(shuffled)
    cut = int(n * train_ratio)
    return shuffled[:cut], shuffled[cut:]


def save_jsonl(items: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            # Salvar só anchor, positive, negative, weight (formato pedido)
            row = {
                "anchor": item.get("anchor", ""),
                "positive": item.get("positive", ""),
                "negative": item.get("negative", ""),
                "weight": item.get("weight", 1.0),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(
    seed: int = 42,
    out_dir: Path | None = None,
    min_triples: int = MIN_TRIPLES,
) -> Dict[str, Any]:
    """
    Gera triplas, valida anchors, divide train/val e salva arquivos.
    Retorna estatísticas.
    """
    out_dir = out_dir or OUT_DIR
    entities, valid_names = _load_entities()
    if not valid_names:
        return {"error": "Nenhuma entidade em extracted_entities.json", "triples": 0}

    triples = generate_all_triples(seed=seed, min_triples=min_triples)
    triples, validation_errors = validate_anchors(triples, valid_names)
    if validation_errors:
        for e in validation_errors[:10]:
            print(f"[WARN] {e}")
        if len(validation_errors) > 10:
            print(f"[WARN] ... e mais {len(validation_errors) - 10} erros de anchor.")

    if len(triples) < min_triples:
        print(f"[WARN] Triplas geradas ({len(triples)}) abaixo do mínimo ({min_triples}).")

    train, val = split_train_val(triples, seed=seed)
    all_path = out_dir / "embedding_triples.jsonl"
    train_path = out_dir / "train_triples.jsonl"
    val_path = out_dir / "val_triples.jsonl"
    save_jsonl(triples, all_path)
    save_jsonl(train, train_path)
    save_jsonl(val, val_path)

    by_strategy = defaultdict(int)
    for t in triples:
        by_strategy[t.get("strategy", "?")] += 1
    stats = {
        "total_triples": len(triples),
        "train": len(train),
        "val": len(val),
        "by_strategy": dict(by_strategy),
        "paths": {
            "embedding_triples": str(all_path),
            "train_triples": str(train_path),
            "val_triples": str(val_path),
        },
    }
    return stats
