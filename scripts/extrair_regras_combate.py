"""
Extrai e consolida Regras de Combate 3D&T.
Carrega regras_combate_canonico.json e gera regras_combate_consolidado.json.
Executar: python scripts/extrair_regras_combate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt


def carregar_canonico() -> list[dict]:
    """Carrega regras canônicas."""
    path = Path("data/processed/regras_combate/regras_combate_canonico.json")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def consolidar_regra(regra: dict) -> dict:
    """Monta texto_completo para busca RAG e expande siglas."""
    partes = [
        regra.get("titulo", ""),
        regra.get("descricao", ""),
        f"Fórmula: {regra['formula']}." if regra.get("formula") else "",
        ", ".join(regra["modificadores"]) if regra.get("modificadores") else "",
    ]
    texto = " ".join(p for p in partes if p)
    regra["texto_completo"] = expandir_siglas_3dt(texto)
    return regra


def main() -> None:
    print("Carregando regras canônicas...")
    regras = carregar_canonico()
    if not regras:
        print("Nenhuma regra encontrada em regras_combate_canonico.json")
        return

    print(f"  Regras carregadas: {len(regras)}")

    consolidado = [consolidar_regra(r.copy()) for r in regras]

    out_path = Path("data/processed/regras_combate/regras_combate_consolidado.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(consolidado, f, ensure_ascii=False, indent=2)

    print(f"[OK] Consolidado em {out_path}")


if __name__ == "__main__":
    main()
