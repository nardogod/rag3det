"""
Validação manual opcional das entidades extraídas.

Uso (na raiz do projeto):
  python scripts/validate_entities.py
  python scripts/validate_entities.py --limit 30
  python scripts/validate_entities.py --review-suspects

- Mostra entidades para conferência; permite correção de tipo (MAGIA→MONSTRO).
- --review-suspects: mostra suspect_entities.json para marcar keep/remove.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths

ENTITIES_JSON = paths.data_dir / "entities" / "extracted_entities.json"
ENTITIES_CLEAN_JSON = paths.data_dir / "entities" / "extracted_entities_clean.json"
SUSPECT_JSON = paths.data_dir / "entities" / "suspect_entities.json"
VALID_TYPES = ("MAGIA", "MONSTRO", "ITEM", "VANTAGEM", "DESVANTAGEM", "PERÍCIA", "ATRIBUTO", "ENTIDADE", "CAPÍTULO", "DESCONHECIDO")


def review_suspects() -> None:
    if not SUSPECT_JSON.exists():
        print(f"Nenhum arquivo {SUSPECT_JSON}. Execute: python scripts/clean_entities.py")
        return
    with SUSPECT_JSON.open("r", encoding="utf-8") as f:
        suspect = json.load(f)
    clean = {}
    if ENTITIES_CLEAN_JSON.exists():
        with ENTITIES_CLEAN_JSON.open("r", encoding="utf-8") as f:
            clean = json.load(f)
    items = sorted(suspect.items(), key=lambda x: -x[1].get("mentions", 0))[:50]
    print(f"Suspeitas ({len(items)} de {len(suspect)}). Comandos: N keep | N remove | s salvar | q sair\n")
    for i, (name, data) in enumerate(items, 1):
        ctx = (data.get("contexts") or [""])[0][:60].replace("\n", " ")
        print(f"  {i}. {name} ({data.get('mentions', 0)} menções) | {ctx}...")
    kept = set()
    removed = set()
    while True:
        try:
            line = input("Ação: ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line.lower() == "q":
            break
        if line.lower() == "s":
            for name in kept:
                if name in suspect:
                    clean[name] = {k: v for k, v in suspect[name].items() if k != "_reason"}
                    del suspect[name]
            with ENTITIES_CLEAN_JSON.open("w", encoding="utf-8") as f:
                json.dump(clean, f, ensure_ascii=False, indent=2)
            with SUSPECT_JSON.open("w", encoding="utf-8") as f:
                json.dump(suspect, f, ensure_ascii=False, indent=2)
            print(f"Salvo. {len(kept)} movidas para clean.")
            kept.clear()
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                idx = int(parts[0])
                cmd = parts[1].lower()
                name = items[idx - 1][0]
                if cmd == "keep":
                    kept.add(name)
                    print(f"  -> {name} marcada para keep")
                elif cmd == "remove":
                    removed.add(name)
                    print(f"  -> {name} marcada para remove")
            except (ValueError, IndexError):
                print("Use: N keep ou N remove")
    print("Até mais.")


def main() -> None:
    if "--review-suspects" in sys.argv:
        review_suspects()
        return
    limit = 30
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    entities_path = ENTITIES_CLEAN_JSON if ENTITIES_CLEAN_JSON.exists() else ENTITIES_JSON
    if not entities_path.exists():
        print(f"Arquivo não encontrado: {entities_path}")
        print("Execute: python scripts/extract_entities.py ou python scripts/clean_entities.py")
        sys.exit(1)
    with entities_path.open("r", encoding="utf-8") as f:
        entities = json.load(f)
    ENTITIES_JSON.parent.mkdir(parents=True, exist_ok=True)
    save_path = entities_path

    items = sorted(entities.items(), key=lambda x: -x[1]["mentions"])[:limit]
    print(f"Mostrando até {limit} entidades (ordenadas por menções).")
    print("Comandos: número + novo_tipo para corrigir (ex: 5 MONSTRO), s para salvar, q para sair.\n")

    modified = False
    for i, (name, data) in enumerate(items, 1):
        etype = data.get("type", "?")
        mentions = data.get("mentions", 0)
        ctx = (data.get("contexts") or [""])[0][:80].replace("\n", " ")
        print(f"  {i}. [{etype}] {name} ({mentions} menções)")
        print(f"      {ctx}...")
        print()

    while True:
        try:
            line = input("Ação (número tipo | s | q): ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line.lower() == "q":
            break
        if line.lower() == "s":
            if modified:
                with save_path.open("w", encoding="utf-8") as f:
                    json.dump(entities, f, ensure_ascii=False, indent=2)
                print("Salvo.")
            else:
                print("Nada a salvar.")
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                idx = int(parts[0])
                new_type = parts[1].upper()
                if new_type not in VALID_TYPES:
                    new_type = "ENTIDADE"
                name = items[idx - 1][0]
                if name in entities:
                    entities[name]["type"] = new_type
                    modified = True
                    print(f"  -> {name} alterado para {new_type}")
            except (ValueError, IndexError):
                print("Use: número espaço tipo (ex: 5 MONSTRO)")
    print("Até mais.")


if __name__ == "__main__":
    main()
