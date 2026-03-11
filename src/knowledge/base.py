"""
Base de conhecimento descoberta: carrega entidades, grafo, taxonomia e propriedades.

Uso no RAG: retrieval, expansão de query, resposta estruturada.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import paths


logger = logging.getLogger(__name__)

ENTITIES_PATH = paths.data_dir / "entities" / "extracted_entities.json"
ENTITIES_CLEAN_PATH = paths.data_dir / "entities" / "extracted_entities_clean.json"
RELATIONS_PATH = paths.data_dir / "knowledge_graph" / "relations.json"
TAXONOMY_PATH = paths.data_dir / "taxonomy" / "auto_taxonomy.json"
PROPERTIES_PATH = paths.data_dir / "properties" / "entity_properties.json"


def load_entities(use_clean: bool = True) -> Dict[str, Dict[str, Any]]:
    """Carrega entidades. Prefere extracted_entities_clean.json se use_clean e existir."""
    path = ENTITIES_CLEAN_PATH if (use_clean and ENTITIES_CLEAN_PATH.exists()) else ENTITIES_PATH
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Falha ao carregar entidades: %s", e)
        return {}


def load_relations() -> List[Dict[str, Any]]:
    """Carrega relations.json (grafo)."""
    if not RELATIONS_PATH.exists():
        return []
    try:
        with RELATIONS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("relations", [])
    except Exception as e:
        logger.warning("Falha ao carregar relações: %s", e)
        return []


def load_taxonomy() -> Dict[str, Dict[str, Any]]:
    """Carrega auto_taxonomy.json (clusters)."""
    if not TAXONOMY_PATH.exists():
        return {}
    try:
        with TAXONOMY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("clusters", {})
    except Exception as e:
        logger.warning("Falha ao carregar taxonomia: %s", e)
        return {}


def load_properties() -> Dict[str, Dict[str, Any]]:
    """Carrega entity_properties.json."""
    if not PROPERTIES_PATH.exists():
        return {}
    try:
        with PROPERTIES_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Falha ao carregar propriedades: %s", e)
        return {}


def get_relations_for_entity(entity_name: str, relations: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Retorna relações onde a entidade é source (normalizada: case-insensitive)."""
    if relations is None:
        relations = load_relations()
    entity_upper = entity_name.strip().upper()
    out = []
    for r in relations:
        src = (r.get("source") or "").strip().upper()
        if src == entity_upper or entity_name.strip().lower() in src.lower():
            out.append(r)
    return out


def get_entity_cluster(entity_name: str, taxonomy: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[str]:
    """Retorna o id do cluster ao qual a entidade pertence."""
    if taxonomy is None:
        taxonomy = load_taxonomy()
    entity_upper = entity_name.strip().upper()
    for cid, data in taxonomy.items():
        for e in data.get("entities", []):
            if (e or "").strip().upper() == entity_upper:
                return cid
    return None


def get_cluster_entities(cluster_id: str, taxonomy: Optional[Dict[str, Dict[str, Any]]] = None) -> List[str]:
    """Retorna lista de entidades do cluster."""
    if taxonomy is None:
        taxonomy = load_taxonomy()
    return (taxonomy.get(cluster_id) or {}).get("entities", [])
