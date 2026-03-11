"""
Reindexa regras do Mestre e Ficha de Personagem no Chroma para busca RAG.
Adiciona chunks mestre_titulo, mestre_cabecalho e mestre_completo.
Executar: python scripts/reindexar_mestre.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.vectorstore.chroma_store import get_vectorstore


def carregar_mestre() -> list[dict] | None:
    """Carrega regras consolidadas (ou canônico se consolidado não existir)."""
    path = Path("data/processed/mestre/mestre_consolidado.json")
    if not path.exists():
        path = Path("data/processed/mestre/mestre_canonico.json")
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return None
    itens = []
    for r in data:
        if "texto_completo" not in r:
            partes = [
                r.get("titulo", ""),
                r.get("descricao", ""),
                f"Fórmula: {r['formula']}." if r.get("formula") else "",
            ]
            r["texto_completo"] = expandir_siglas_3dt(" ".join(p for p in partes if p))
        itens.append(r)
    return itens


def criar_documentos_mestre(item: dict) -> list[Document]:
    """Cria Document objects para indexação."""
    docs = []
    meta_base = {
        "tipo": "mestre",
        "id": item.get("id", ""),
        "titulo": item.get("titulo", ""),
        "categoria": item.get("categoria", ""),
        "livro": item.get("livro", ""),
        "pagina": str(item.get("pagina", "")),
    }

    docs.append(
        Document(
            page_content=item.get("titulo", ""),
            metadata={**meta_base, "tipo_chunk": "mestre_titulo"},
        )
    )

    cabecalho = f"{item.get('titulo', '')}. "
    if item.get("formula"):
        cabecalho += f"Fórmula: {expandir_siglas_3dt(item['formula'])}. "
    cabecalho += f"Categoria: {item.get('categoria', '')}."
    docs.append(
        Document(
            page_content=cabecalho.strip(),
            metadata={**meta_base, "tipo_chunk": "mestre_cabecalho"},
        )
    )

    docs.append(
        Document(
            page_content=item.get("texto_completo", item.get("titulo", "")),
            metadata={**meta_base, "tipo_chunk": "mestre_completo"},
        )
    )
    return docs


def main() -> None:
    print("Carregando regras do Mestre...")

    itens = carregar_mestre()
    if not itens:
        print("Nenhum item encontrado. Execute: python scripts/extrair_mestre.py")
        return

    print(f"  Itens carregados: {len(itens)}")

    docs = []
    for item in itens:
        docs.extend(criar_documentos_mestre(item))

    print(f"  Documentos a adicionar: {len(docs)}")

    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos do Mestre adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")
        print("Dica: o Chroma deve existir. Rode a ingestão primeiro.")


if __name__ == "__main__":
    main()
