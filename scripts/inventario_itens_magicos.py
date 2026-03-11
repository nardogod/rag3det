"""
Inventário de itens mágicos 3D&T.
Gera resumo, lista e documentação a partir dos dados extraídos.
Saída: data/processed/inventario_itens_magicos.json e docs/INVENTARIO_ITENS_MAGICOS.md
"""

from __future__ import annotations

import json
from pathlib import Path

# Adiciona raiz ao path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def carregar_itens_extraidos() -> list[dict]:
    """Carrega itens do extrator agressivo."""
    path = Path("data/processed/itens_magicos/itens_magicos_extraidos_agressivo.json")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def carregar_indice() -> list[tuple[int, str]]:
    """Carrega índice de itens (se existir)."""
    path = Path("data/processed/indice_itens_magicos_3dt.txt")
    if not path.exists():
        return []
    indice = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if ". " in line:
                num, nome = line.strip().split(". ", 1)
                indice.append((int(num), nome))
    return indice


def main() -> None:
    print("=== Inventário de Itens Mágicos 3D&T ===\n")

    itens = carregar_itens_extraidos()
    indice = carregar_indice()

    print(f"Itens extraídos: {len(itens)}")
    print(f"Itens no índice: {len(indice)}")

    nomes_extraidos = {i["nome"].strip() for i in itens}
    nomes_indice = {n for _, n in indice}
    cobertos = nomes_indice & nomes_extraidos if indice else set()
    faltando = nomes_indice - nomes_extraidos if indice else set()
    extras = nomes_extraidos - nomes_indice if indice else nomes_extraidos

    # Por livro
    por_livro: dict[str, int] = {}
    for i in itens:
        livro = i.get("livro", "?")
        por_livro[livro] = por_livro.get(livro, 0) + 1

    inventario = {
        "resumo": {
            "total_indice": len(indice),
            "total_com_descricao": len(itens),
            "cobertos": len(cobertos),
            "faltando_descricao": len(faltando),
            "extras": len(extras),
        },
        "por_livro": por_livro,
        "itens": itens,
        "nomes_faltando": sorted(faltando),
        "nomes_extras": sorted(extras),
    }

    out_json = Path("data/processed/inventario_itens_magicos.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(inventario, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Inventário salvo em {out_json}")

    # Gerar docs/INVENTARIO_ITENS_MAGICOS.md
    md_path = Path("docs/INVENTARIO_ITENS_MAGICOS.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "# Inventário de Itens Mágicos 3D&T",
        "",
        "## Resumo",
        "",
        f"- **Itens com descrição extraída**: {len(itens)}",
        f"- **Cobertura do índice**: {len(cobertos)}" + (f" de {len(indice)}" if indice else ""),
        "",
        "## Fontes por livro",
        "",
    ]
    for livro, qtd in sorted(por_livro.items(), key=lambda x: -x[1]):
        linhas.append(f"- `{livro}`: {qtd} itens")
    linhas.extend(["", "## Lista de itens", ""])

    for i in sorted(itens, key=lambda x: x["nome"].lower()):
        custo = i.get("custo", "")
        bonus = i.get("bonus", "")
        tipo = i.get("tipo", "")
        extras_str = []
        if tipo:
            extras_str.append(f"Tipo: {tipo}")
        if bonus:
            extras_str.append(f"Bônus: {bonus}")
        if custo:
            extras_str.append(f"Custo: {custo}")
        suf = f" ({', '.join(extras_str)})" if extras_str else ""
        linhas.append(f"- **{i['nome']}**{suf}")

    if faltando:
        linhas.extend(["", "## Itens do índice sem descrição", ""])
        for n in sorted(faltando):
            linhas.append(f"- {n}")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"[OK] Documentação em {md_path}")


if __name__ == "__main__":
    main()
