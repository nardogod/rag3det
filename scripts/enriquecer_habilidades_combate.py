"""
Enriquece todos os monstros em monstros_extraidos.json com habilidades_combate
extraídas da descrição. Executar: python scripts/enriquecer_habilidades_combate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.extrair_habilidades_combate import extrair_habilidades_combate


def main() -> None:
    out_dir = Path("data/processed/monstros")
    path = out_dir / "monstros_extraidos.json"
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    total_com_hab = 0

    for mon in data:
        desc = mon.get("descricao") or ""
        hab_combate = extrair_habilidades_combate(desc)
        mon["habilidades_combate"] = hab_combate
        if hab_combate:
            total_com_hab += 1

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(data)} monstros processados. {total_com_hab} com habilidades de combate extraídas.")


if __name__ == "__main__":
    main()
