"""
Reindexa Regras de Combate no Chroma para busca RAG.
Adiciona chunks regra_titulo, regra_cabecalho e regra_completo.
Executar: python scripts/reindexar_regras_combate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.vectorstore.chroma_store import get_vectorstore


def carregar_regras() -> list[dict] | None:
    """Carrega regras consolidadas (ou canônico se consolidado não existir)."""
    path = Path("data/processed/regras_combate/regras_combate_consolidado.json")
    if not path.exists():
        path = Path("data/processed/regras_combate/regras_combate_canonico.json")
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return None
    regras = []
    for r in data:
        if "texto_completo" not in r:
            partes = [
                r.get("titulo", ""),
                r.get("descricao", ""),
                f"Fórmula: {r['formula']}." if r.get("formula") else "",
            ]
            r["texto_completo"] = expandir_siglas_3dt(" ".join(p for p in partes if p))
        regras.append(r)
    return regras


def criar_documentos_regra(regra: dict) -> list[Document]:
    """Cria Document objects para indexação."""
    docs = []
    meta_base = {
        "tipo": "regra_combate",
        "id": regra.get("id", ""),
        "titulo": regra.get("titulo", ""),
        "categoria": regra.get("categoria", ""),
        "livro": regra.get("livro", ""),
        "pagina": str(regra.get("pagina", "")),
    }

    docs.append(
        Document(
            page_content=regra.get("titulo", ""),
            metadata={**meta_base, "tipo_chunk": "regra_titulo"},
        )
    )

    cabecalho = f"{regra.get('titulo', '')}. "
    if regra.get("formula"):
        cabecalho += f"Fórmula: {expandir_siglas_3dt(regra['formula'])}. "
    cabecalho += f"Categoria: {regra.get('categoria', '')}."
    docs.append(
        Document(
            page_content=cabecalho.strip(),
            metadata={**meta_base, "tipo_chunk": "regra_cabecalho"},
        )
    )

    docs.append(
        Document(
            page_content=regra.get("texto_completo", regra.get("titulo", "")),
            metadata={**meta_base, "tipo_chunk": "regra_completo"},
        )
    )
    return docs


def main() -> None:
    print("Carregando regras de combate...")

    regras = carregar_regras()
    if not regras:
        print("Nenhuma regra encontrada. Execute: python scripts/extrair_regras_combate.py")
        return

    print(f"  Regras carregadas: {len(regras)}")

    docs = []
    for regra in regras:
        docs.extend(criar_documentos_regra(regra))

    print(f"  Documentos a adicionar: {len(docs)}")

    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos de regras de combate adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")
        print("Dica: o Chroma deve existir. Rode a ingestão primeiro.")


if __name__ == "__main__":
    main()
