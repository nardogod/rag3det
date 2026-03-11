"""
Reindexa Perícias no Chroma para busca RAG.
Executar: python scripts/reindexar_pericias.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.vectorstore.chroma_store import get_vectorstore


def carregar_pericias() -> list[dict] | None:
    """Carrega Perícias extraídas."""
    path = Path("data/processed/pericias/pericias_extraidas.json")
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return None
    for m in data:
        partes = [
            m.get("nome", ""),
            f"Custo: {m.get('custo', '')}.",
            m.get("descricao", ""),
            f"Especializações: {', '.join(m.get('especializacoes', []))}." if m.get("especializacoes") else "",
            f"Fonte: {m.get('livro', '')}." if m.get("livro") else "",
        ]
        texto = " ".join(p for p in partes if p)
        m["texto_completo"] = expandir_siglas_3dt(texto)
    return data


def criar_documentos_pericia(item: dict) -> list[Document]:
    """Cria Document objects para indexação."""
    docs = []
    meta_base = {
        "tipo": "pericia",
        "nome": item["nome"],
        "custo": item.get("custo", ""),
        "livro": item.get("livro", ""),
    }

    docs.append(
        Document(
            page_content=item["nome"],
            metadata={**meta_base, "tipo_chunk": "pericia_nome"},
        )
    )

    cabecalho = f"{item['nome']}. Custo: {item.get('custo', '')}."
    if item.get("especializacoes"):
        cabecalho += f" Especializações: {', '.join(item['especializacoes'])}."
    docs.append(
        Document(
            page_content=expandir_siglas_3dt(cabecalho),
            metadata={**meta_base, "tipo_chunk": "pericia_cabecalho"},
        )
    )

    docs.append(
        Document(
            page_content=item.get("texto_completo", expandir_siglas_3dt(item["nome"])),
            metadata={**meta_base, "tipo_chunk": "pericia_completo"},
        )
    )
    return docs


def main() -> None:
    print("Carregando perícias...")

    itens = carregar_pericias()
    if not itens:
        print("Nenhuma perícia encontrada. Execute: python scripts/extrair_pericias_agressivo.py")
        return

    print(f"  Itens carregados: {len(itens)}")

    docs = []
    for item in itens:
        docs.extend(criar_documentos_pericia(item))

    print(f"  Documentos a adicionar: {len(docs)}")

    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos de perícias adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")


if __name__ == "__main__":
    main()
