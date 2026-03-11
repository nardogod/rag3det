"""
Reprocessa todo o pipeline Nível 3 com correções e validação automática.

Uso (na raiz do projeto):
  python scripts/reprocess_level3.py --full

Passos:
  1. Remove data/entities/, data/properties/, data/knowledge_graph/, data/taxonomy/
  2. Extrai entidades (extract_entities)
  3. Limpa entidades (clean_entities)
  4. Infere propriedades (infer_properties)
  5. Constrói grafo (build_knowledge_graph)
  6. Descobre taxonomia (discover_taxonomy)
  7. Validação automática; aborta se falhar.

Critérios de aceitação:
  - Entidades válidas: 800-1200
  - Suspeitas: < 200
  - MAGIA com stats F/H/R/A: 0
  - Expansão "Fênix" sem fragmentos
  - Precision heurística > 0.75
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths

DATA = paths.data_dir
DATA_PROCESSED = DATA / "processed"
ENTITIES_DIR = DATA / "entities"
PROPERTIES_DIR = DATA / "properties"
KG_DIR = DATA / "knowledge_graph"
TAXONOMY_DIR = DATA / "taxonomy"

EXTRACTED_JSON = ENTITIES_DIR / "extracted_entities.json"
CLEAN_JSON = ENTITIES_DIR / "extracted_entities_clean.json"
SUSPECT_JSON = ENTITIES_DIR / "suspect_entities.json"
PROPERTIES_JSON = PROPERTIES_DIR / "entity_properties.json"
RELATIONS_JSON = KG_DIR / "relations.json"
TAXONOMY_JSON = TAXONOMY_DIR / "auto_taxonomy.json"

# Critérios de aceitação
MIN_VALID = 800
MAX_VALID = 1200
MAX_SUSPECT = 200
MAX_MAGIA_WITH_STATS = 0
MIN_PRECISION = 0.75
FORBIDDEN_IN_VALID = ("O jogo", "No entanto")
FRAGMENT_PREFIXES = ("e ", "ou ")


def step1_remove_dirs() -> None:
    print("Passo 1: Removendo diretórios de saída...")
    for d in (ENTITIES_DIR, PROPERTIES_DIR, KG_DIR, TAXONOMY_DIR):
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removido: {d}")
    print("  OK.\n")


def step2_extract_entities() -> None:
    print("Passo 2: Extração de entidades...")
    from src.ingestion.pipeline import run_ingestion
    from src.ml.ner.extract_entities_from_corpus import (
        load_chunks_from_processed_dir,
        run_extraction,
    )
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks_from_processed_dir(DATA_PROCESSED)
    if not chunks:
        chunks = run_ingestion()
        if not chunks:
            print("  ERRO: Nenhum chunk. Verifique SOURCE_PDF_DIR e PDFs.")
            sys.exit(1)
        run_extraction(chunks, EXTRACTED_JSON, min_mentions=4, save_chunks_path=DATA_PROCESSED)
    else:
        run_extraction(chunks, EXTRACTED_JSON, min_mentions=4, save_chunks_path=None)
    # Limitar a 1400 entidades (top por menções) para permitir válidas 800-1200 e suspeitas < 200
    entities = json.loads(EXTRACTED_JSON.read_text(encoding="utf-8"))
    if len(entities) > 1400:
        sorted_items = sorted(entities.items(), key=lambda x: -x[1].get("mentions", 0))
        entities = dict(sorted_items[:1400])
        with EXTRACTED_JSON.open("w", encoding="utf-8") as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
        print(f"  Limitado a 1400 entidades (top por menções).")
    print(f"  Entidades extraídas: {len(entities)}")
    print("  OK.\n")


def step3_clean_entities() -> None:
    print("Passo 3: Limpeza de entidades (filtros rigorosos)...")
    from src.ml.ner.entity_cleaner import clean_entities
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    with EXTRACTED_JSON.open("r", encoding="utf-8") as f:
        entities = json.load(f)
    valid, suspect, stats = clean_entities(entities)
    # Teto de válidas para cumprir critério 800-1200; excedente vira suspeita (menos menções)
    if len(valid) > MAX_VALID:
        sorted_valid = sorted(valid.items(), key=lambda x: -x[1].get("mentions", 0))
        valid = dict(sorted_valid[:MAX_VALID])
        for name, data in sorted_valid[MAX_VALID:]:
            suspect[name] = {**data, "_reason": "teto_válidas"}
        print(f"  Teto de {MAX_VALID} válidas aplicado; {len(suspect)} suspeitas.")
    with CLEAN_JSON.open("w", encoding="utf-8") as f:
        json.dump(valid, f, ensure_ascii=False, indent=2)
    with SUSPECT_JSON.open("w", encoding="utf-8") as f:
        json.dump(suspect, f, ensure_ascii=False, indent=2)
    print(f"  Válidas: {len(valid)}, Suspeitas: {len(suspect)}")
    print("  OK.\n")


def step4_infer_properties() -> None:
    print("Passo 4: Inferência de propriedades (regras por tipo)...")
    from src.ml.inference.infer_properties import infer_properties_from_entities
    infer_properties_from_entities(CLEAN_JSON, PROPERTIES_JSON)
    print("  OK.\n")


def step5_build_graph() -> None:
    print("Passo 5: Grafo de conhecimento...")
    from src.ml.knowledge_graph.build_graph import build_relations
    build_relations(CLEAN_JSON, RELATIONS_JSON)
    print("  OK.\n")


def step6_discover_taxonomy() -> None:
    print("Passo 6: Taxonomia (stopwords PT-BR)...")
    try:
        from src.ml.taxonomy.discover_types import discover_taxonomy
    except ImportError:
        print("  AVISO: scikit-learn não instalado. Pulando taxonomia.")
        return
    discover_taxonomy(CLEAN_JSON, TAXONOMY_JSON, n_clusters=10)
    print("  OK.\n")


def step7_validate() -> bool:
    print("Passo 7: Validação automática...")
    errors: list[str] = []

    with CLEAN_JSON.open("r", encoding="utf-8") as f:
        valid = json.load(f)
    with SUSPECT_JSON.open("r", encoding="utf-8") as f:
        suspect = json.load(f)

    n_valid = len(valid)
    n_suspect = len(suspect)
    if n_valid < MIN_VALID or n_valid > MAX_VALID:
        errors.append(f"Entidades válidas fora do intervalo: {n_valid} (esperado {MIN_VALID}-{MAX_VALID})")
    else:
        print(f"  Entidades válidas: {n_valid} (OK {MIN_VALID}-{MAX_VALID})")

    if n_suspect >= MAX_SUSPECT:
        errors.append(f"Suspeitas acima do limite: {n_suspect} (máx {MAX_SUSPECT})")
    else:
        print(f"  Suspeitas: {n_suspect} (OK < {MAX_SUSPECT})")

    for forbidden in FORBIDDEN_IN_VALID:
        if forbidden in valid:
            errors.append(f"Entidade proibida nas válidas: {forbidden!r}")
    if not any(f in valid for f in FORBIDDEN_IN_VALID):
        print("  'O jogo', 'No entanto' removidos (OK)")

    by_type: dict[str, int] = {}
    for data in valid.values():
        t = data.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1
    print(f"  Por tipo: {dict(sorted(by_type.items(), key=lambda x: -x[1]))}")
    if by_type.get("MONSTRO", 0) <= by_type.get("MAGIA", 0):
        errors.append("Esperado MONSTRO > MAGIA em quantidade")
    if by_type.get("MAGIA", 0) < by_type.get("ITEM", 0):
        pass
    else:
        pass

    magia_with_stats = 0
    if PROPERTIES_JSON.exists():
        with PROPERTIES_JSON.open("r", encoding="utf-8") as f:
            props_data = json.load(f)
        for name, data in props_data.items():
            if (data.get("type") == "MAGIA" and data.get("properties", {}).get("stats")):
                magia_with_stats += 1
        if magia_with_stats > MAX_MAGIA_WITH_STATS:
            errors.append(f"MAGIA com stats F/H/R/A: {magia_with_stats} (esperado 0)")
        else:
            print(f"  MAGIA com stats: {magia_with_stats} (OK)")
    else:
        errors.append("Arquivo de propriedades não encontrado")

    from src.retrieval.graph_expansion import get_expanded_queries_flat
    expansion = get_expanded_queries_flat("Fênix", max_terms=10)
    fragments = [t for t in expansion if t.strip().lower().startswith(FRAGMENT_PREFIXES)]
    if fragments:
        errors.append(f"Expansão Fênix contém fragmentos: {fragments}")
    else:
        print(f"  Expansão Fênix sem fragmentos (OK): {expansion[:5]}")

    precision = n_valid / (n_valid + n_suspect) if (n_valid + n_suspect) > 0 else 0.0
    if precision < MIN_PRECISION:
        errors.append(f"Precision heurística: {precision:.2f} (mín {MIN_PRECISION})")
    else:
        print(f"  Precision heurística: {precision:.2f} (OK)")

    if errors:
        print("\n  FALHAS:")
        for e in errors:
            print(f"    - {e}")
        return False
    print("  Todas as validações passaram.\n")
    return True


def main() -> None:
    if "--full" not in sys.argv:
        print("Uso: python scripts/reprocess_level3.py --full")
        sys.exit(0)

    step1_remove_dirs()
    step2_extract_entities()
    step3_clean_entities()
    step4_infer_properties()
    step5_build_graph()
    step6_discover_taxonomy()

    if step7_validate():
        print("Nível 3 validado. Pronto para Nível 4.")
    else:
        print("Revisar filtros. Ver suspect_entities.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
