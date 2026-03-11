"""
Reindexa monstros/criaturas no Chroma para busca RAG.
Carrega monstros_extraidos.json ou monstros_canonico.json como fallback.
Executar: python scripts/reindexar_monstros.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.utils.formatar_monstro import formatar_ficha_monstro_tabela
from src.utils.livro_normalizado import normalizar_livro
from src.vectorstore.chroma_store import get_vectorstore

MONSTROS_DIR = Path("data/processed/monstros")
COMPLEMENTO_PATH = MONSTROS_DIR / "monstros_canonico_complemento.json"


def _carregar_complemento() -> dict[str, dict]:
    """Carrega complemento manual (sobrescreve monstros específicos)."""
    if not COMPLEMENTO_PATH.exists():
        return {}
    with COMPLEMENTO_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {m["nome"].strip().lower(): m for m in (data if isinstance(data, list) else [])}


def carregar_monstros() -> list[dict]:
    """Carrega monstros (extraídos ou canônico), enriquecidos quando disponível."""
    ext_path = MONSTROS_DIR / "monstros_extraidos.json"
    canon_path = MONSTROS_DIR / "monstros_canonico.json"
    enriquecido_path = MONSTROS_DIR / "monstros_modelo_enriquecido.json"
    path = ext_path if ext_path.exists() else canon_path
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    itens = data if isinstance(data, list) else []
    # Sobrescrever com dados enriquecidos (todos os monstros) quando existir
    CAMPOS_IDENTIDADE = {"nome", "livro", "pagina"}
    if enriquecido_path.exists():
        with enriquecido_path.open("r", encoding="utf-8") as f:
            enriquecidos = {m["nome"].strip().lower(): m for m in json.load(f) if m.get("nome")}
        for m in itens:
            key = m["nome"].strip().lower()
            if key in enriquecidos:
                for k, v in enriquecidos[key].items():
                    if k not in CAMPOS_IDENTIDADE:
                        m[k] = v
    complemento = _carregar_complemento()
    for m in itens:
        key = m["nome"].strip().lower()
        if key in complemento:
            m.update(complemento[key])
        m["livro"] = normalizar_livro(m.get("livro")) or m.get("livro", "")
        # Usa formato de ficha completo e tabelado (docs/FORMATO_FICHA_MONSTRO.md)
        m["texto_completo"] = expandir_siglas_3dt(formatar_ficha_monstro_tabela(m, incluir_descricao=True))
    return itens


def criar_documentos_monstro(item: dict) -> list[Document]:
    """Cria Document objects para indexação."""
    meta_base = {
        "tipo": "monstro",
        "nome": item["nome"],
        "tipo_criatura": item.get("tipo", ""),
        "livro": item.get("livro", ""),
    }
    return [
        Document(
            page_content=item["nome"],
            metadata={**meta_base, "tipo_chunk": "monstro_nome"},
        ),
        Document(
            page_content=item.get("texto_completo", item["nome"]),
            metadata={**meta_base, "tipo_chunk": "monstro_completo"},
        ),
    ]


def main() -> None:
    print("Carregando monstros...")
    itens = carregar_monstros()
    if not itens:
        print("Nenhum monstro encontrado. Execute: python scripts/extrair_monstros_agressivo.py")
        return
    print(f"  Monstros carregados: {len(itens)}")
    docs = []
    for item in itens:
        docs.extend(criar_documentos_monstro(item))
    print(f"  Documentos a adicionar: {len(docs)}")
    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos de monstros adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")


if __name__ == "__main__":
    main()
