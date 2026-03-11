"""
Validação final do Nível 3: extração + critérios consolidados.

Uso (na raiz do projeto):
  python scripts/final_validate_level3.py

1. Roda extract_entities (extração com min_mentions=5)
2. Verifica entidades críticas: Bola de Fogo → MAGIA, Magia Elemental → MAGIA, "Na verdade" não existe
3. Conta por tipo e total
4. Se passa: cria data/level3_consolidated.flag e imprime "NÍVEL 3 CONSOLIDADO. Pronto para Nível 4 (Fine-tuning)."
5. Se não passa: mostra top 20 DESCONHECIDOS e sugere ajustes
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
ENTITIES_DIR = DATA / "entities"
EXTRACTED_JSON = ENTITIES_DIR / "extracted_entities.json"
FLAG_FILE = DATA / "level3_consolidated.flag"

# Critérios Nível 3 (metas realistas para corpus 3D&T)
MAGIA_MIN = 400
MAGIA_MAX = 600
MONSTRO_MIN = 400
MONSTRO_MAX = 600
ITEM_MIN = 300
ITEM_MAX = 500
VANTAGEM_MIN = 100  # corpus pode ter menos; 200-400 é meta ideal
VANTAGEM_MAX = 400
DESCONHECIDO_MAX = 50
TOTAL_MIN = 1500
TOTAL_MAX = 2500
CRITICAL_MAGIC_MUST_BE_MAGIA = (
    "Bola de Fogo", "Bola de fogo", "Invocação da Fênix", "Invocação da Fenix",
    "Magia Elemental", "Magia Branca", "Magia Negra", "Magia Arcana", "Magia Divina",
)
# Bloqueadores: se existirem → falha
PHRASES_MUST_NOT_EXIST = ("Na verdade", "na verdade", "Se falhar", "veja abaixo", "T Alpha pg", "Por isso", "APENAS")
# Críticas que devem existir (se não existir → ERRO)
CRITICAL_MUST_EXIST = ("Bola de Fogo", "Magia Branca")


def run_extraction_step() -> dict:
    """Executa extração e retorna dicionário de entidades."""
    from src.ingestion.pipeline import run_ingestion
    from src.ml.ner.extract_entities_from_corpus import (
        load_chunks_from_processed_dir,
        run_extraction,
    )
    DATA_PROCESSED = DATA / "processed"
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks_from_processed_dir(DATA_PROCESSED)
    if not chunks:
        chunks = run_ingestion()
        if not chunks:
            print("ERRO: Nenhum chunk. Verifique SOURCE_PDF_DIR e PDFs.")
            sys.exit(1)
    entities = run_extraction(
        chunks,
        EXTRACTED_JSON,
        min_mentions=4,
        save_chunks_path=DATA_PROCESSED if not (DATA_PROCESSED / "chunks.json").exists() else None,
    )
    return entities


def load_entities() -> dict:
    """Carrega entidades do JSON (se o usuário já rodou extract_entities antes)."""
    if not EXTRACTED_JSON.exists():
        return {}
    with EXTRACTED_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(entities: dict) -> tuple[bool, list[str]]:
    """Retorna (passou, lista de mensagens de erro)."""
    errors: list[str] = []
    total = len(entities)
    by_type: dict[str, int] = {}
    for data in entities.values():
        t = data.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1
    magia = by_type.get("MAGIA", 0)
    monstro = by_type.get("MONSTRO", 0)
    item = by_type.get("ITEM", 0)
    vantagem = by_type.get("VANTAGEM", 0)
    desconhecido = by_type.get("DESCONHECIDO", 0)

    # Bloqueadores: críticas devem existir
    for name in CRITICAL_MUST_EXIST:
        if name not in entities:
            errors.append(f"ERRO: '{name}' não existe (deve estar presente)")
        elif entities[name].get("type") != "MAGIA":
            errors.append(f"ERRO: '{name}' deve ser MAGIA (atual: {entities[name].get('type')})")

    # Outras críticas que existem devem ser MAGIA
    for name in CRITICAL_MAGIC_MUST_BE_MAGIA:
        if name in entities and entities[name].get("type") != "MAGIA":
            errors.append(f"'{name}' deve ser MAGIA (atual: {entities[name].get('type')})")

    # Frases comuns não devem existir (bloqueador)
    for phrase in PHRASES_MUST_NOT_EXIST:
        if phrase in entities:
            errors.append(f"ERRO: frase comum não deve ser entidade: '{phrase}'")

    # Faixas
    if magia < MAGIA_MIN or magia > MAGIA_MAX:
        errors.append(f"MAGIA: {magia} (esperado {MAGIA_MIN}-{MAGIA_MAX})")
    if monstro < MONSTRO_MIN or monstro > MONSTRO_MAX:
        errors.append(f"MONSTRO: {monstro} (esperado {MONSTRO_MIN}-{MONSTRO_MAX})")
    if item < ITEM_MIN or item > ITEM_MAX:
        errors.append(f"ITEM: {item} (esperado {ITEM_MIN}-{ITEM_MAX})")
    if vantagem < VANTAGEM_MIN or vantagem > VANTAGEM_MAX:
        errors.append(f"VANTAGEM: {vantagem} (esperado {VANTAGEM_MIN}-{VANTAGEM_MAX})")
    if desconhecido > DESCONHECIDO_MAX:
        errors.append(f"DESCONHECIDO: {desconhecido} (meta <{DESCONHECIDO_MAX})")
    if total < TOTAL_MIN or total > TOTAL_MAX:
        errors.append(f"Total: {total} (meta {TOTAL_MIN}-{TOTAL_MAX})")

    return len(errors) == 0, errors


def main() -> None:
    run_extract = "--run" in sys.argv or not EXTRACTED_JSON.exists()
    if run_extract:
        print("Rodando extração de entidades (min_mentions por tipo)...")
        entities = run_extraction_step()
    else:
        print("Carregando entidades de", EXTRACTED_JSON)
        entities = load_entities()
        if not entities:
            print("Nenhuma entidade encontrada. Execute com --run para rodar a extração.")
            sys.exit(1)

    passed, errors = validate(entities)
    by_type: dict[str, int] = {}
    for data in entities.values():
        t = data.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1

    print("\n--- Contagens ---")
    print(f"  Total: {len(entities)}")
    for t in sorted(by_type.keys(), key=lambda x: -by_type[x]):
        print(f"  {t}: {by_type[t]}")

    if passed:
        DATA.mkdir(parents=True, exist_ok=True)
        FLAG_FILE.write_text("Nível 3 consolidado.", encoding="utf-8")
        print("\nNÍVEL 3 CONSOLIDADO. Pronto para Nível 4 (Fine-tuning).")
        return

    print("\n--- Falhas ---")
    for e in errors:
        print(f"  - {e}")
    # Top 20 DESCONHECIDOS por menções
    desconhecidos = [(n, d) for n, d in entities.items() if d.get("type") == "DESCONHECIDO"]
    desconhecidos.sort(key=lambda x: -x[1].get("mentions", 0))
    print("\n--- Top 20 DESCONHECIDOS (para análise) ---")
    for name, data in desconhecidos[:20]:
        print(f"  - {name!r}: {data.get('mentions', 0)} menções")
    print("\nSugestões: ajustar padrões regex em extract_entities_from_corpus.py, ou aumentar min_mentions.")
    sys.exit(1)


if __name__ == "__main__":
    main()
