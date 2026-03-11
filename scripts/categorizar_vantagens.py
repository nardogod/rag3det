"""
Categoriza Vantagens e Desvantagens conforme taxonomia do Manual da Magia.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA = Path("data/processed/vantagens_desvantagens")
TAXONOMIA = DATA / "taxonomia_manual_magia.json"
ITENS_JSON = DATA / "vantagens_magia_extraidas.json"
OUTPUT_JSON = DATA / "vantagens_magia_categorizadas.json"
OUTPUT_TXT = DATA / "vantagens_por_categoria.txt"


def _normalizar(nome: str) -> str:
    import unicodedata
    n = unicodedata.normalize("NFD", nome.lower())
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


def categorizar_item(nome: str, tipo: str, tax: dict) -> str:
    """Retorna o id da categoria."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        return "desconhecido"
    nome_norm = _normalizar(nome_limpo)

    cats = tax["categorias"]
    ordem = tax.get("ordem_categorias", [])

    # Kits: padrões específicos
    for padrao in cats.get("kit_personagem", {}).get("padroes", []):
        p_norm = _normalizar(padrao)
        if p_norm in nome_norm or nome_norm.startswith(p_norm):
            return "kit_personagem"

    # Vantagem mágica: padrões
    for padrao in cats.get("vantagem_magia", {}).get("padroes", []):
        p_norm = _normalizar(padrao)
        if p_norm in nome_norm or nome_norm.startswith(p_norm):
            return "vantagem_magia"

    # Vantagem raça: prefixos
    for prefixo in cats.get("vantagem_raca", {}).get("prefixos", []):
        if nome_norm.startswith(_normalizar(prefixo)):
            return "vantagem_raca"

    # Desvantagem mágica
    for padrao in cats.get("desvantagem_magia", {}).get("padroes", []):
        if _normalizar(padrao) in nome_norm:
            return "desvantagem_magia"

    # Por tipo
    if tipo == "desvantagem":
        return "desvantagem_geral"
    return "vantagem_magia"  # fallback para vantagens não mapeadas


def main() -> None:
    if not TAXONOMIA.exists():
        print(f"Taxonomia não encontrada: {TAXONOMIA}")
        return
    if not ITENS_JSON.exists():
        print(f"Itens não encontrados: {ITENS_JSON}")
        print("Execute: python scripts/extrair_vantagens_magia_agressivo.py")
        return

    tax = json.loads(TAXONOMIA.read_text(encoding="utf-8"))
    itens = json.loads(ITENS_JSON.read_text(encoding="utf-8"))

    categorias: dict[str, list] = {}
    for item in itens:
        cat_id = categorizar_item(
            item.get("nome", ""),
            item.get("tipo", ""),
            tax,
        )
        item["categoria"] = cat_id
        item["categoria_label"] = tax["categorias"].get(cat_id, {}).get("label", cat_id)
        categorias.setdefault(cat_id, []).append(item)

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False, indent=2)
    print(f"[OK] Salvos {len(itens)} itens em {OUTPUT_JSON}")

    linhas = [
        "=" * 70,
        "VANTAGENS E DESVANTAGENS POR CATEGORIA (Manual da Magia)",
        "=" * 70,
        "",
    ]
    for cat_id in tax.get("ordem_categorias", []) + ["desconhecido"]:
        lista = categorias.get(cat_id, [])
        if not lista:
            continue
        label = tax["categorias"].get(cat_id, {}).get("label", cat_id)
        linhas.append(f"\n--- {label} ({len(lista)} itens) ---")
        for i in lista[:15]:
            linhas.append(f"  • {i['nome']} | {i.get('custo', '-')} | {i['tipo']}")
        if len(lista) > 15:
            linhas.append(f"  ... e mais {len(lista) - 15}")

    OUTPUT_TXT.write_text("\n".join(linhas), encoding="utf-8")
    print(f"[OK] Relatório em {OUTPUT_TXT}")

    print("\nResumo por categoria:")
    for cat_id, lista in sorted(categorias.items(), key=lambda x: -len(x[1])):
        label = tax["categorias"].get(cat_id, {}).get("label", cat_id)
        print(f"  {label}: {len(lista)}")


if __name__ == "__main__":
    main()
