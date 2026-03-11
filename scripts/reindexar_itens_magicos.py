"""
Reindexa itens mágicos com metadados para busca no RAG.
Adiciona chunks item_nome e item_completo ao vectorstore.
Executar: python scripts/reindexar_itens_magicos.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.utils.livro_normalizado import normalizar_livro
from src.vectorstore.chroma_store import get_vectorstore


def carregar_itens_agressivo() -> list[dict] | None:
    """Carrega itens (categorizados se existir, senão extraídos, senão canônico como fallback)."""
    cat_path = Path("data/processed/itens_magicos/itens_magicos_categorizados.json")
    ext_path = Path("data/processed/itens_magicos/itens_magicos_extraidos_agressivo.json")
    canon_path = Path("data/processed/itens_magicos/itens_magicos_canonico.json")
    path = cat_path if cat_path.exists() else (ext_path if ext_path.exists() else canon_path)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return None
    itens = []
    for m in data:
        m["livro"] = normalizar_livro(m.get("livro")) or m.get("livro", "")
        partes = [
            m.get("nome", ""),
            f"Tipo: {m.get('tipo', '')}." if m.get("tipo") else "",
            f"Bônus: {m.get('bonus', '')}." if m.get("bonus") else "",
            f"Preço: {m.get('custo', '')}." if m.get("custo") else "",
            m.get("efeito", ""),
            f"Fonte: {m.get('livro', '')}." if m.get("livro") else "",
        ]
        texto = " ".join(p for p in partes if p)
        m["texto_completo"] = expandir_siglas_3dt(texto)
        itens.append(m)
    return itens


def criar_documentos_item(item: dict) -> list[Document]:
    """Cria Document objects para indexacao."""
    docs = []
    meta_base = {
        "tipo": "item_magico",
        "nome": item["nome"],
        "tipo_item": item.get("tipo", ""),
        "bonus": item.get("bonus", ""),
        "custo": item.get("custo", ""),
        "livro": item.get("livro", ""),
        "categoria": item.get("categoria", ""),
        "categoria_label": item.get("categoria_label", ""),
    }

    docs.append(
        Document(
            page_content=item["nome"],
            metadata={**meta_base, "tipo_chunk": "item_nome"},
        )
    )

    cabecalho = f"{item['nome']}. "
    if item.get("tipo"):
        cabecalho += f"Tipo: {item['tipo']}. "
    if item.get("custo"):
        cabecalho += f"Preço: {item['custo']}. "
    docs.append(
        Document(
            page_content=expandir_siglas_3dt(cabecalho.strip()),
            metadata={**meta_base, "tipo_chunk": "item_cabecalho"},
        )
    )

    docs.append(
        Document(
            page_content=item.get("texto_completo", expandir_siglas_3dt(item["nome"])),
            metadata={**meta_base, "tipo_chunk": "item_completo"},
        )
    )
    return docs


def main() -> None:
    print("Carregando itens magicos...")

    itens = carregar_itens_agressivo()
    if not itens:
        print("Nenhum item encontrado. Execute: python scripts/extrair_itens_magicos_agressivo.py")
        return

    print(f"  Itens carregados: {len(itens)}")

    docs = []
    for item in itens:
        docs.extend(criar_documentos_item(item))

    print(f"  Documentos a adicionar: {len(docs)}")

    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos de itens magicos adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")
        print("Dica: o Chroma deve existir. Rode a ingestao primeiro.")


if __name__ == "__main__":
    main()
