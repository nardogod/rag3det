"""
Compara ranking ANTES (só vetor) vs DEPOIS (cross-encoder rerank).

Uso (na raiz do projeto):
  python scripts/compare_reranking.py

- Testa 5 queries fixas (Fênix, Insano Megalomaníaco, Mortos-vivos, etc.).
- Mostra top 5 antes e depois do reranking.
- Métrica: quantos docs relevantes estão no top 5 antes vs depois (relevante = contém a frase-chave da query).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.documents import Document

from src.retrieval.reranker import CrossEncoderReranker, _key_phrase_from_query
from src.vectorstore.chroma_store import get_vectorstore


VECTOR_K = 20
TOP_K = 5

QUERIES = [
    "Invocação da Fênix",
    "Insano Megalomaníaco",
    "Mortos-vivos",
    "Magia elemental de fogo",
    "Vantagem Ataque Extra",
]


def _distance_to_similarity(distance: float) -> float:
    return 1.0 / (1.0 + float(distance))


def _is_relevant(doc: Document, query: str) -> bool:
    """True se o conteúdo do doc contém a frase-chave da query (ex.: fênix, megalomaníaco)."""
    key = _key_phrase_from_query(query)
    if not key:
        return True
    content = (doc.page_content or "").lower()
    # Considera relevante se alguma palavra significativa da frase está no doc
    words = [w for w in key.split() if len(w) > 2]
    return any(w in content for w in words)


def _snippet(doc: Document, max_len: int = 80) -> str:
    text = (doc.page_content or "").replace("\n", " ")
    return (text[:max_len] + "...") if len(text) > max_len else text


def _safe(s: str) -> str:
    """Para exibição no console Windows (evita UnicodeEncodeError)."""
    return (s or "").encode("ascii", errors="replace").decode("ascii")


def main() -> None:
    vectorstore = get_vectorstore()
    reranker = CrossEncoderReranker()

    print("=" * 70)
    print("COMPARAÇÃO: Vector (top 5) vs Cross-Encoder Rerank (top 5)")
    print("=" * 70)

    total_relevant_before = 0
    total_relevant_after = 0
    total_subiram = 0

    for query in QUERIES:
        print(f"\n>>> Query: {query}")
        key = _key_phrase_from_query(query)
        print(f"    Frase-chave para relevância: {key!r}")

        # Vector: top 20, depois pegamos os 5 primeiros = "antes"
        try:
            raw = vectorstore.similarity_search_with_score(query, k=VECTOR_K)
        except Exception as e:
            print(f"    Erro na busca: {e}")
            continue

        docs_before = [doc for doc, _ in raw[:TOP_K]]
        scores_before = [_distance_to_similarity(d) for _, d in raw[:TOP_K]]

        # Rerank: top 5 = "depois"
        scored_after = reranker.rerank(query, [doc for doc, _ in raw], top_k=TOP_K)
        docs_after = [doc for doc, _ in scored_after]
        scores_after = [s for _, s in scored_after]

        # Contagem de relevantes
        rel_before = sum(1 for d in docs_before if _is_relevant(d, query))
        rel_after = sum(1 for d in docs_after if _is_relevant(d, query))
        total_relevant_before += rel_before
        total_relevant_after += rel_after
        subiram = max(0, rel_after - rel_before)
        total_subiram += subiram

        print("\n    ANTES (vector retrieval, top 5):")
        for i, (doc, sc) in enumerate(zip(docs_before, scores_before), 1):
            rel = " [RELEVANTE]" if _is_relevant(doc, query) else ""
            meta = doc.metadata or {}
            fonte = _safe(str(meta.get("book_title") or meta.get("source") or "?"))
            print(f"      {i}. [{sc:.4f}] {fonte} | {_safe(_snippet(doc))}{rel}")

        print("\n    DEPOIS (cross-encoder rerank, top 5):")
        for i, (doc, sc) in enumerate(zip(docs_after, scores_after), 1):
            rel = " [RELEVANTE]" if _is_relevant(doc, query) else ""
            meta = doc.metadata or {}
            fonte = _safe(str(meta.get("book_title") or meta.get("source") or "?"))
            print(f"      {i}. [{sc:.4f}] {fonte} | {_safe(_snippet(doc))}{rel}")

        print(f"\n    Métrica: relevantes no top 5 ANTES = {rel_before} | DEPOIS = {rel_after} | subiram = +{subiram}")

    print("\n" + "=" * 70)
    print("RESUMO GERAL")
    print("=" * 70)
    print(f"  Total de relevantes no top 5 (antes):  {total_relevant_before}")
    print(f"  Total de relevantes no top 5 (depois): {total_relevant_after}")
    print(f"  Quanto subiram (soma por query):        +{total_subiram}")
    print()


if __name__ == "__main__":
    main()
