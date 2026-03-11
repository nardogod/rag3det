"""
Pipeline completo de descoberta de conhecimento 3D&T.

Uso (na raiz do projeto):
  python scripts/discover_knowledge.py --full    # executa todos os passos
  python scripts/discover_knowledge.py --update  # só extração (como se fossem novos PDFs)

Ordem: extract_entities → infer_properties → build_knowledge_graph → discover_taxonomy
       (opcional: prepare_ner_data + train_corpus_ner)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths

DATA = paths.data_dir
ENTITIES_JSON = DATA / "entities" / "extracted_entities.json"
ENTITIES_CLEAN_JSON = DATA / "entities" / "extracted_entities_clean.json"
PROPERTIES_JSON = DATA / "properties" / "entity_properties.json"
RELATIONS_JSON = DATA / "knowledge_graph" / "relations.json"
TAXONOMY_JSON = DATA / "taxonomy" / "auto_taxonomy.json"


def run_extract_entities() -> bool:
    from src.ingestion.pipeline import run_ingestion
    from src.ml.ner.extract_entities_from_corpus import load_chunks_from_processed_dir, run_extraction
    processed_dir = DATA / "processed"
    chunks = load_chunks_from_processed_dir(processed_dir)
    if not chunks:
        chunks = run_ingestion()
        if not chunks:
            return False
    run_extraction(chunks, ENTITIES_JSON, min_mentions=3, save_chunks_path=processed_dir)
    return ENTITIES_JSON.exists()


def run_infer_properties() -> bool:
    from src.ml.inference.infer_properties import infer_properties_from_entities
    path = ENTITIES_CLEAN_JSON if ENTITIES_CLEAN_JSON.exists() else ENTITIES_JSON
    if not path.exists():
        return False
    infer_properties_from_entities(path, PROPERTIES_JSON)
    return PROPERTIES_JSON.exists()


def run_build_graph() -> bool:
    from src.ml.knowledge_graph.build_graph import build_relations
    path = ENTITIES_CLEAN_JSON if ENTITIES_CLEAN_JSON.exists() else ENTITIES_JSON
    if not path.exists():
        return False
    build_relations(path, RELATIONS_JSON)
    return RELATIONS_JSON.exists()


def run_discover_taxonomy() -> bool:
    try:
        from src.ml.taxonomy.discover_types import discover_taxonomy
    except ImportError:
        print("scikit-learn não instalado. Pulando taxonomia.")
        return False
    path = ENTITIES_CLEAN_JSON if ENTITIES_CLEAN_JSON.exists() else ENTITIES_JSON
    if not path.exists():
        return False
    discover_taxonomy(path, TAXONOMY_JSON)
    return TAXONOMY_JSON.exists()


def write_coverage_report() -> None:
    report = {
        "entities_file": ENTITIES_JSON.exists() or ENTITIES_CLEAN_JSON.exists(),
        "entities_count": 0,
        "properties_file": PROPERTIES_JSON.exists(),
        "relations_file": RELATIONS_JSON.exists(),
        "relations_count": 0,
        "taxonomy_file": TAXONOMY_JSON.exists(),
        "clusters_count": 0,
    }
    entities_path = ENTITIES_CLEAN_JSON if ENTITIES_CLEAN_JSON.exists() else ENTITIES_JSON
    if entities_path.exists():
        with entities_path.open("r", encoding="utf-8") as f:
            report["entities_count"] = len(json.load(f))
    if RELATIONS_JSON.exists():
        with RELATIONS_JSON.open("r", encoding="utf-8") as f:
            report["relations_count"] = len(json.load(f).get("relations", []))
    if TAXONOMY_JSON.exists():
        with TAXONOMY_JSON.open("r", encoding="utf-8") as f:
            report["clusters_count"] = len(json.load(f).get("clusters", {}))
    out_path = DATA / "coverage_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Relatório: {out_path}")


def main() -> None:
    full = "--full" in sys.argv
    update = "--update" in sys.argv
    if not full and not update:
        print("Uso: python scripts/discover_knowledge.py --full | --update")
        sys.exit(0)
    if full:
        print("Passo 1: Extração de entidades...")
        run_extract_entities()
        print("Passo 2: Inferência de propriedades...")
        run_infer_properties()
        print("Passo 3: Grafo de relações...")
        run_build_graph()
        print("Passo 4: Taxonomia (clusters)...")
        run_discover_taxonomy()
        write_coverage_report()
        print("Pipeline de descoberta concluído.")
    else:
        print("Modo --update: só extração de entidades.")
        run_extract_entities()
        run_infer_properties()
        run_build_graph()
        run_discover_taxonomy()
        write_coverage_report()


if __name__ == "__main__":
    main()
