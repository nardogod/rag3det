"""
Inventário completo do livro de magias 3D&T Alpha.
Extrai: lista das 300 magias do índice, magias com descrição, cobertura, fontes.
Saída: data/processed/inventario_magias.json e docs/INVENTARIO_MAGIAS.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.entity_extractor import extrair_magias_de_texto


def carregar_chunks() -> list[dict]:
    """Carrega todos os chunks de chunks.json."""
    path = Path("data/processed/chunks.json")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("chunks", data.get("documents", [data]))
    return [i for i in items if isinstance(i, dict)]


def extrair_lista_300_magias(chunks: list[dict]) -> list[dict]:
    """
    Extrai os nomes das 300 magias do índice "Lista Completa das 300 Magias Alpha".
    Formato: "Nome (MM, pg. 07). Nome2 ( M3D&T, pg. 84)." - split por "). " e parse.
    Retorna lista de {nome, fonte, pagina}.
    """
    # Concatena todos os chunks do índice para ter a lista completa
    textos_indice = []
    for chunk in chunks:
        content = chunk.get("content") or chunk.get("page_content") or ""
        if "Lista Completa das 300 Magias Alpha" not in content:
            continue
        textos_indice.append(content)
    texto_indice = "\n".join(textos_indice)

    magias_indice = []
    seen = set()

    # Também tenta regex para capturar "Nome (ref)" mesmo com variações
    for match in re.finditer(
        r"([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\-'\"\.\,\!\?]+?)\s*\(([^)]*?pg\.?\s*\d+[^)]*)\)",
        texto_indice,
        re.IGNORECASE,
    ):
        nome = match.group(1).strip()
        ref = match.group(2).strip().replace("\n", " ")
        if "\n" in nome:
            nome = nome.split("\n")[-1].strip()
        if not nome or len(nome) < 2:
            continue
        if "lista completa" in nome.lower() or "300 magias" in nome.lower():
            continue
        if nome.lower() in ("lista", "completa", "alpha", "magias"):
            continue

        fonte = "?"
        pagina = "?"
        if "pg." in ref or "pg " in ref:
            pg_match = re.search(r"pg\.?\s*(\d+)", ref, re.IGNORECASE)
            if pg_match:
                pagina = pg_match.group(1)
        if "MM" in ref:
            fonte = "MM"
        elif "M3D&T" in ref or "3D&T" in ref:
            fonte = "M3D&T"
        elif "MD" in ref:
            fonte = "MD"

        if nome not in seen:
            seen.add(nome)
            magias_indice.append({"nome": nome, "fonte": fonte, "pagina": pagina})
        continue

    # Fallback: split por "). "
    if len(magias_indice) < 100:
        magias_indice = []
        seen = set()
        parts = re.split(r"\)\.\s*", texto_indice)
        for part in parts:
            if "(" not in part or "pg" not in part.lower():
                continue
            try:
                nome, ref = part.rsplit("(", 1)
                nome = nome.strip()
                # Se o nome veio com cabeçalho (ex: "Lista Completa...\nAbençoar Água"), pega a última linha
                if "\n" in nome:
                    nome = nome.split("\n")[-1].strip()
                ref = ref.strip().replace("\n", " ")
                if not nome or len(nome) < 2:
                    continue
                # Ignora cabeçalhos
                if "lista completa" in nome.lower() or "300 magias" in nome.lower():
                    continue
                if nome.lower() in ("lista", "completa", "alpha", "magias"):
                    continue

                fonte = "?"
                pagina = "?"
                if "pg." in ref or "pg " in ref:
                    pg_match = re.search(r"pg\.?\s*(\d+)", ref, re.IGNORECASE)
                    if pg_match:
                        pagina = pg_match.group(1)
                if "MM" in ref:
                    fonte = "MM"
                elif "M3D&T" in ref or "3D&T" in ref:
                    fonte = "M3D&T"
                elif "MD" in ref:
                    fonte = "MD"

                if nome not in seen:
                    seen.add(nome)
                    magias_indice.append({"nome": nome, "fonte": fonte, "pagina": pagina})
            except ValueError:
                continue

    return magias_indice


def chunks_por_fonte(chunks: list[dict]) -> dict[str, list[dict]]:
    """Agrupa chunks por source (PDF)."""
    por_fonte = defaultdict(list)
    for c in chunks:
        src = (c.get("metadata") or {}).get("source", "desconhecido")
        por_fonte[src].append(c)
    return dict(por_fonte)


def reconstruir_texto_por_pagina(chunks: list[dict], source: str) -> str:
    """
    Concatena chunks de um mesmo source ordenados por página.
    Isso evita que magias cortadas no meio do chunk sejam perdidas.
    """
    chunks_filtrados = [
        c for c in chunks
        if (c.get("metadata") or {}).get("source") == source
    ]
    # Ordena por página
    def page_key(c):
        m = c.get("metadata", c) or {}
        p = m.get("page", m.get("page_label", 0))
        return (int(p) if str(p).isdigit() else 0, id(c))

    chunks_filtrados.sort(key=page_key)

    textos = []
    for c in chunks_filtrados:
        content = c.get("content") or c.get("page_content") or ""
        if content.strip():
            textos.append(content)
    return "\n\n".join(textos)


def extrair_magias_completas(texto: str) -> list[dict]:
    """Extrai magias com descrição completa do texto concatenado."""
    return extrair_magias_de_texto(texto)


def main() -> None:
    print("=== Inventário do Livro de Magias 3D&T Alpha ===\n")

    chunks = carregar_chunks()
    print(f"Chunks totais: {len(chunks)}")

    # 1. Lista das 300 magias do índice
    magias_indice = extrair_lista_300_magias(chunks)
    print(f"Magias no índice (Lista Completa): {len(magias_indice)}")

    # 2. Fontes
    por_fonte = chunks_por_fonte(chunks)
    print(f"\nFontes (PDFs): {list(por_fonte.keys())}")

    # 3. Manual da Magia - texto completo para extração
    manual_magia = "3dt-alpha-manual-da-magia-biblioteca-elfica.pdf"
    texto_manual = reconstruir_texto_por_pagina(chunks, manual_magia)
    print(f"\nTexto Manual da Magia: {len(texto_manual)} caracteres")

    # 4. Extrair magias com descrição
    magias_completas = extrair_magias_completas(texto_manual)
    print(f"Magias extraídas (com Escola/Custo/Alcance/Descrição): {len(magias_completas)}")

    # 5. Bestiário também tem magias?
    bestiario = "3dt-alpha-bestiario-alpha-biblioteca-elfica.pdf"
    if bestiario in por_fonte:
        chunks_magias = [
            c for c in por_fonte[bestiario]
            if "Escola:" in (c.get("content") or c.get("page_content") or "")
            and "Custo:" in (c.get("content") or c.get("page_content") or "")
        ]
        print(f"Chunks com magias no Bestiário: {len(chunks_magias)}")

    # 6. Cobertura: quantas do índice têm descrição extraída?
    nomes_extraidos = {m["nome"].strip() for m in magias_completas}
    nomes_indice = {m["nome"].strip() for m in magias_indice}
    cobertos = nomes_indice & nomes_extraidos
    faltando = nomes_indice - nomes_extraidos
    extras = nomes_extraidos - nomes_indice  # magias extraídas que não estão no índice

    print(f"\n--- Cobertura ---")
    print(f"Magias no índice: {len(nomes_indice)}")
    print(f"Magias com descrição extraída: {len(nomes_extraidos)}")
    print(f"Cobertas (no índice e extraídas): {len(cobertos)}")
    print(f"No índice mas sem descrição: {len(faltando)}")
    print(f"Extraídas mas não no índice: {len(extras)}")

    # 7. Montar inventário
    inventario = {
        "resumo": {
            "total_indice": len(magias_indice),
            "total_com_descricao": len(magias_completas),
            "cobertos": len(cobertos),
            "faltando_descricao": len(faltando),
            "extras": len(extras),
        },
        "lista_indice": magias_indice,
        "magias_completas": magias_completas,
        "nomes_faltando": sorted(faltando),
        "nomes_extras": sorted(extras),
    }

    # Salvar JSON
    out_json = Path("data/processed/inventario_magias.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(inventario, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Inventário salvo em {out_json}")

    # 8. Gerar docs/INVENTARIO_MAGIAS.md
    md_path = Path("docs/INVENTARIO_MAGIAS.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    linhas = [
        "# Inventário do Livro de Magias 3D&T Alpha",
        "",
        "## Resumo",
        "",
        f"- **Magias no índice (Lista Completa)**: {len(magias_indice)}",
        f"- **Magias com descrição extraída**: {len(magias_completas)}",
        f"- **Cobertura**: {len(cobertos)} magias do índice têm descrição",
        f"- **Faltando descrição**: {len(faltando)}",
        "",
        "## Fontes",
        "",
    ]
    for src, items in por_fonte.items():
        linhas.append(f"- `{src}`: {len(items)} chunks")
    linhas.extend(["", "## Lista das 300 Magias (índice)", ""])

    for m in sorted(magias_indice, key=lambda x: x["nome"].lower()):
        status = "✓" if m["nome"].strip() in nomes_extraidos else "○"
        linhas.append(f"- {status} **{m['nome']}** ({m['fonte']}, pg. {m['pagina']})")

    linhas.extend(["", "## Magias sem descrição extraída", ""])
    for n in sorted(faltando):
        linhas.append(f"- {n}")

    linhas.extend(["", "## Magias extraídas (sem correspondência no índice)", ""])
    for n in sorted(extras)[:50]:  # limitar
        linhas.append(f"- {n}")
    if len(extras) > 50:
        linhas.append(f"- ... e mais {len(extras) - 50}")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print(f"[OK] Documentação em {md_path}")


if __name__ == "__main__":
    main()
