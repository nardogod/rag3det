"""
Categoriza itens mágicos extraídos conforme taxonomia do Manual da Magia.
Baseado na estrutura a partir da pg. 72: Arma Especial, Habilidades, Armas, Armaduras, etc.

Uso: python scripts/categorizar_itens_magicos.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA = Path("data/processed/itens_magicos")
TAXONOMIA = DATA / "taxonomia_manual_magia.json"
ITENS_JSON = DATA / "itens_magicos_extraidos_agressivo.json"
OUTPUT_JSON = DATA / "itens_magicos_categorizados.json"
OUTPUT_TXT = DATA / "itens_por_categoria.txt"


def _normalizar(nome: str) -> str:
    """Remove acentos para comparação flexível."""
    import unicodedata
    n = unicodedata.normalize("NFD", nome.lower())
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


def carregar_taxonomia() -> dict:
    with TAXONOMIA.open("r", encoding="utf-8") as f:
        return json.load(f)


def categorizar_item(nome: str, tax: dict) -> str:
    """Retorna o id da categoria para o item."""
    nome_limpo = nome.strip()
    if not nome_limpo or len(nome_limpo) < 3:
        return "desconhecido"
    nome_norm = _normalizar(nome_limpo)

    cats = tax["categorias"]
    ordem = tax.get("ordem_categorias", [])

    # 1. Bônus genérico (Força +1, Armadura +2, etc.)
    for cat_id in ordem:
        c = cats.get(cat_id, {})
        for padrao in c.get("padroes", []):
            if re.search(padrao, nome_limpo, re.IGNORECASE):
                return cat_id

    # 2. Prefixos primeiro (Anel X, Poção Y) - evita "Anel de Armazenar" → habilidade
    for cat_id in ordem:
        c = cats.get(cat_id, {})
        for prefixo in c.get("prefixos", []):
            if nome_limpo.startswith(prefixo) or nome_norm.startswith(_normalizar(prefixo)):
                return cat_id

    # 3. Lista explícita - match exato ou nome começa com item
    for cat_id in ordem:
        c = cats.get(cat_id, {})
        for item in c.get("itens", []):
            item_norm = _normalizar(item)
            if nome_norm == item_norm or nome_norm.startswith(item_norm + " "):
                return cat_id

    return "diverso"


def main() -> None:
    if not TAXONOMIA.exists():
        print(f"Taxonomia não encontrada: {TAXONOMIA}")
        return
    if not ITENS_JSON.exists():
        print(f"Itens não encontrados: {ITENS_JSON}")
        print("Execute: python scripts/extrair_itens_magicos_agressivo.py")
        return

    tax = carregar_taxonomia()
    with ITENS_JSON.open("r", encoding="utf-8") as f:
        itens = json.load(f)

    # Filtrar fragmentos (nomes quebrados)
    def eh_fragmento(n: str) -> bool:
        return n.endswith("-") or (len(n) > 3 and n[0].islower())

    categorias: dict[str, list[dict]] = {}
    for item in itens:
        nome = item.get("nome", "")
        if eh_fragmento(nome):
            continue
        cat_id = categorizar_item(nome, tax)
        item["categoria"] = cat_id
        item["categoria_label"] = tax["categorias"].get(cat_id, {}).get("label", cat_id)
        categorias.setdefault(cat_id, []).append(item)

    # Salvar JSON com categorias
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False, indent=2)
    print(f"[OK] Salvos {len(itens)} itens em {OUTPUT_JSON}")

    # Gerar relatório por categoria
    linhas = [
        "=" * 70,
        "ITENS MÁGICOS POR CATEGORIA (3dt-manual-da-magia-biblioteca-elfica.pdf)",
        "=" * 70,
        "",
    ]
    for cat_id in tax.get("ordem_categorias", []) + ["diverso", "desconhecido"]:
        lista = categorias.get(cat_id, [])
        if not lista:
            continue
        label = tax["categorias"].get(cat_id, {}).get("label", cat_id)
        linhas.append(f"\n--- {label} ({len(lista)} itens) ---")
        # Filtrar só do manual da magia
        manual = [i for i in lista if "manual-da-magia" in (i.get("livro") or "").lower() and "alpha" not in (i.get("livro") or "").lower()]
        for i in (manual if manual else lista)[:20]:
            custo = i.get("custo") or "-"
            linhas.append(f"  • {i['nome']} | Preço: {custo}")
        if len(manual if manual else lista) > 20:
            linhas.append(f"  ... e mais {len(manual if manual else lista) - 20}")

    with OUTPUT_TXT.open("w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"[OK] Relatório em {OUTPUT_TXT}")

    # Resumo
    print("\nResumo por categoria:")
    for cat_id, lista in sorted(categorias.items(), key=lambda x: -len(x[1])):
        label = tax["categorias"].get(cat_id, {}).get("label", cat_id)
        print(f"  {label}: {len(lista)}")


if __name__ == "__main__":
    main()
