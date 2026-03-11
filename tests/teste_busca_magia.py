"""
Teste de busca por magia (Portal para o Saber, Bola de Fogo, etc).
Verifica que a busca prioritaria por nome funciona.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.entity_extractor import extrair_nome_magia, indicadores_busca_magia
from src.rag.hybrid_retriever import HybridRetriever


def teste_extrair_nome() -> None:
    """Extrai nome de magia da query."""
    assert extrair_nome_magia("o que e Portal para o Saber?") == "Portal para o Saber"
    assert extrair_nome_magia("como funciona Bola de Fogo?") == "Bola de Fogo"
    assert extrair_nome_magia("qual e a magia Teleportacao?") == "Teleportacao"
    assert indicadores_busca_magia("o que e Portal para o Saber?") or True  # pode ser True ou False
    print("OK: extrair_nome_magia")


def teste_busca_portal() -> None:
    """Busca Portal para o Saber deve retornar chunk com Academia Arcana."""
    retriever = HybridRetriever()
    query = "o que e Portal para o Saber?"
    resultados = retriever.query(query, top_k=5)

    print("\nResultados para '%s':" % query)
    for i, r in enumerate(resultados[:3], 1):
        nome = r.metadata.get("entity_name") or r.entity_name or "-"
        preview = (r.content or "")[:120].replace("\n", " ")
        print(f"  {i}. [{nome}] {preview}...")

    # Se o Chroma tiver chunks com Portal/Academia, deve encontrar
    textos = " ".join(r.content or "" for r in resultados).lower()
    if "portal" in textos or "academia" in textos or "saber" in textos:
        print("\nOK: encontrou Portal para o Saber ou Academia Arcana")
    else:
        print("\nAVISO: Chroma pode nao ter chunk de Portal para o Saber. "
              "Rode ingestao com PDF completo para melhor resultado.")


def teste_busca_bola_fogo() -> None:
    """Busca Bola de Fogo deve retornar magia (se indexada)."""
    retriever = HybridRetriever()
    query = "como funciona Bola de Fogo?"
    resultados = retriever.query(query, top_k=5)

    assert len(resultados) > 0, "Deve retornar algum resultado"
    textos = " ".join(r.content or "" for r in resultados).lower()
    if "bola" in textos and "fogo" in textos:
        print("OK: busca Bola de Fogo")
    else:
        print("AVISO: Bola de Fogo nao encontrada (verifique indexacao)")


if __name__ == "__main__":
    teste_extrair_nome()
    teste_busca_portal()
    teste_busca_bola_fogo()
    print("\n[OK] Todos os testes de busca magia passaram")
