"""
Aplica filtro de combate em todas as descrições de monstros.
Mantém apenas conteúdo relevante para combate (fórmulas, ataques, sopro, magias, etc.).
Executar: python scripts/filtrar_descricoes_combate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.filtrar_descricao_combate import filtrar_descricao_combate

MONSTROS_PATH = Path("data/processed/monstros/monstros_extraidos.json")


def main() -> None:
    if not MONSTROS_PATH.exists():
        print(f"Arquivo não encontrado: {MONSTROS_PATH}")
        return

    with MONSTROS_PATH.open("r", encoding="utf-8") as f:
        monstros = json.load(f)

    alterados = 0
    for m in monstros:
        desc = m.get("descricao", "").strip()
        if not desc:
            continue
        nova = filtrar_descricao_combate(desc)
        if nova != desc:
            m["descricao"] = nova
            alterados += 1

    with MONSTROS_PATH.open("w", encoding="utf-8") as f:
        json.dump(monstros, f, ensure_ascii=False, indent=2)

    print(f"[OK] {alterados} descrições filtradas de {len(monstros)} monstros.")
    print(f"     Salvo em {MONSTROS_PATH}")


if __name__ == "__main__":
    main()
