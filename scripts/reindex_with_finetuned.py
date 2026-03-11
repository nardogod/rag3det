"""
Reindexação completa do vectorstore com embeddings fine-tuned.

Uso (na raiz do projeto):
  python scripts/reindex_with_finetuned.py

- Carrega chunks de data/processed/chunks.json (ou roda ingestão se não existir).
- Recria o índice Chroma com o modelo de embeddings configurado (fine-tuned se existir).
- Mostra 5 exemplos de como "Fênix" se moveu no espaço vetorial:
  esperado: mais próximo de "Bola de Fogo", "Muralha de Fogo"; mais distante de "Ghoul".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.documents import Document

from src.config import paths
from src.embedding.pipeline import get_embedding_function
from src.embedding.local_embeddings import get_effective_embedding_model_id
from src.vectorstore.chroma_store import build_or_update_vectorstore, _get_persist_directory
from src.vectorstore.chroma_store import _COLLECTION_NAME
from langchain_chroma import Chroma


def load_chunks_from_processed() -> list[Document]:
    """Carrega chunks de data/processed/chunks.json."""
    chunks_path = paths.data_dir / "processed" / "chunks.json"
    if not chunks_path.exists():
        return []
    with chunks_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return []
    out = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        content = item.get("page_content") or ""
        meta = item.get("metadata") or {}
        out.append(Document(page_content=content, metadata=meta))
    return out


def run_ingestion_if_needed():
    """Se não houver chunks.json, roda ingestão."""
    chunks_path = paths.data_dir / "processed" / "chunks.json"
    if chunks_path.exists():
        return None
    from src.ingestion.pipeline import run_ingestion
    return run_ingestion()


def compare_examples(vectorstore: Chroma) -> None:
    """Mostra 5 exemplos: vizinhança de 'Fênix' (deve incluir Bola de Fogo, Muralha de Fogo; distante de Ghoul)."""
    print("\n--- Exemplos de vizinhança no espaço vetorial (embedding fine-tuned) ---\n")
    queries = [
        "Fênix",
        "Invocação da Fênix",
        "Bola de Fogo",
        "Muralha de Fogo",
        "Ghoul",
    ]
    for q in queries:
        try:
            results = vectorstore.similarity_search_with_score(q, k=5)
            print(f"Query: {q!r}")
            for doc, score in results:
                snippet = (doc.page_content or "")[:120].replace("\n", " ")
                print(f"  dist={score:.4f}  {snippet}...")
            print()
        except Exception as e:
            print(f"Query {q!r}: erro {e}\n")

    # Comparação explícita: para query "Fênix", distância a trechos típicos
    print("--- Distância da query 'Fênix' a trechos relacionados vs não relacionados ---")
    try:
        fenix_results = vectorstore.similarity_search_with_score("Fênix", k=20)
        for doc, dist in fenix_results[:10]:
            content = (doc.page_content or "").lower()
            label = "fogo/magia" if ("bola de fogo" in content or "muralha" in content or "fênix" in content or "invocação" in content) else ("ghoul/monstro" if "ghoul" in content else "outro")
            print(f"  {dist:.4f}  [{label}]  {(doc.page_content or '')[:80]}...")
    except Exception as e:
        print(f"  Erro: {e}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Reindexa vectorstore com embeddings fine-tuned.")
    parser.add_argument("--both", action="store_true", help="Construir também índice baseline (para A/B test)")
    args = parser.parse_args()

    print("Reindexando vectorstore com embeddings fine-tuned...")
    chunks = load_chunks_from_processed()
    if not chunks:
        print("Chunks não encontrados em data/processed/chunks.json. Rodando ingestão...")
        chunks = run_ingestion_if_needed()
        if not chunks:
            print("ERRO: Rode antes a ingestão (scripts/build_index.py) ou gere data/processed/chunks.json.")
            sys.exit(1)
    print(f"Chunks carregados: {len(chunks)}")
    model_id = get_effective_embedding_model_id()
    print(f"Modelo de embedding: {model_id}")

    build_or_update_vectorstore(chunks)
    print("Índice fine-tuned recriado com sucesso.")
    if args.both:
        print("Construindo índice baseline (genérico)...")
        build_or_update_vectorstore(chunks, use_baseline=True)
        print("Índice baseline recriado com sucesso.")

    persist_dir = _get_persist_directory()
    embeddings = get_embedding_function()
    vs = Chroma(
        persist_directory=persist_dir,
        collection_name=_COLLECTION_NAME,
        embedding_function=embeddings,
    )
    compare_examples(vs)
    print("Concluído.")


if __name__ == "__main__":
    main()
