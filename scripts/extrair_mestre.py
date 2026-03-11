"""
Extrai e consolida regras do Mestre e Ficha de Personagem 3D&T.
Carrega mestre_canonico.json e gera mestre_consolidado.json.
Executar: python scripts/extrair_mestre.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt


def carregar_canonico() -> list[dict]:
    """Carrega regras canônicas do Mestre."""
    path = Path("data/processed/mestre/mestre_canonico.json")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def consolidar_item(item: dict) -> dict:
    """Monta texto_completo para busca RAG e expande siglas."""
    partes = [
        item.get("titulo", ""),
        item.get("descricao", ""),
        f"Fórmula: {item['formula']}." if item.get("formula") else "",
        ", ".join(item["modificadores"]) if item.get("modificadores") else "",
    ]
    if item.get("schema"):
        s = item["schema"]
        campos = []
        if "caracteristicas" in s:
            campos.append("Características: " + ", ".join(s["caracteristicas"]))
        if "caminhos_magia" in s:
            campos.append("Caminhos da Magia: " + ", ".join(s["caminhos_magia"]))
        if campos:
            partes.append(" Campos: " + "; ".join(campos))
    texto = " ".join(p for p in partes if p)
    item["texto_completo"] = expandir_siglas_3dt(texto)
    return item


def main() -> None:
    print("Carregando regras do Mestre...")
    itens = carregar_canonico()
    if not itens:
        print("Nenhum item encontrado em mestre_canonico.json")
        return

    print(f"  Itens carregados: {len(itens)}")

    consolidado = [consolidar_item(i.copy()) for i in itens]

    out_path = Path("data/processed/mestre/mestre_consolidado.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(consolidado, f, ensure_ascii=False, indent=2)

    print(f"[OK] Consolidado em {out_path}")


if __name__ == "__main__":
    main()
