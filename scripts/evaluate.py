"""
Avaliação automática do retrieval: Recall@k e MRR.

Uso (na raiz do projeto):
  python scripts/evaluate.py
  python scripts/evaluate.py --k 5

- Executa apenas a etapa de retrieval (sem LLM).
- Cada pergunta tem "ground truth" como frases que devem aparecer em algum chunk relevante.
- Recall@k: fração de perguntas em que pelo menos um chunk no top-k contém alguma frase esperada.
- MRR (Mean Reciprocal Rank): média de 1/rank do primeiro chunk que contém uma frase esperada.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retrieval.pipeline import retrieve_relevant_chunks  # noqa: E402


# 10 perguntas de teste com frases que devem aparecer em chunks relevantes (ground truth).
EVAL_QUESTIONS = [
    {
        "question": "O que o Insano • Megalomaníaco acredita ser?",
        "expected_phrases": ["Megalomaníaco", "acredita ser", "insano"],
    },
    {
        "question": "Como funciona a magia elemental?",
        "expected_phrases": ["magia", "elemental", "elemento"],
    },
    {
        "question": "Quais são as vantagens para elfos?",
        "expected_phrases": ["elfo", "vantagem", "elfos"],
    },
    {
        "question": "O que é Invocação da Fênix?",
        "expected_phrases": ["Invocação", "Fênix", "Fenix"],
    },
    {
        "question": "Explique a regra de desvantagens.",
        "expected_phrases": ["desvantagem", "desvantagens"],
    },
    {
        "question": "Quais magias de ataque existem?",
        "expected_phrases": ["magia", "ataque", "Ataque Mágico"],
    },
    {
        "question": "O que é o monstro Marilith?",
        "expected_phrases": ["Marilith", "demônio", "guerreira"],
    },
    {
        "question": "Como funcionam as perícias em 3D&T?",
        "expected_phrases": ["perícia", "perícias"],
    },
    {
        "question": "O que é resistência a dano?",
        "expected_phrases": ["resistência", "dano"],
    },
    {
        "question": "Quais criaturas têm capacidade de teleportação?",
        "expected_phrases": ["teleportação", "Teleportação", "criatura", "magia"],
    },
]


def _first_rank_with_phrase(chunks: list, expected_phrases: list) -> int | None:
    """Retorna o rank (1-based) do primeiro chunk que contém alguma das frases, ou None."""
    for rank, chunk in enumerate(chunks, start=1):
        content = (chunk.content if hasattr(chunk, "content") else str(chunk)).lower()
        for phrase in expected_phrases:
            if phrase.lower() in content:
                return rank
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia retrieval: Recall@k e MRR.")
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Top-k chunks considerados para Recall e MRR (default: 10).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Imprime por pergunta se encontrou e em qual rank.",
    )
    args = parser.parse_args()
    k = args.k

    print(f"Avaliando retrieval com top_k={k} e {len(EVAL_QUESTIONS)} perguntas.\n")

    recall_hits = 0
    mrr_sum = 0.0

    for i, item in enumerate(EVAL_QUESTIONS, start=1):
        question = item["question"]
        expected = item["expected_phrases"]
        chunks = retrieve_relevant_chunks(question, k=k)
        rank = _first_rank_with_phrase(chunks, expected)
        if rank is not None:
            recall_hits += 1
            mrr_sum += 1.0 / rank
        if args.verbose:
            status = f"rank {rank}" if rank is not None else "não encontrado"
            print(f"  [{i}] {question[:50]}... -> {status}")

    recall_at_k = recall_hits / len(EVAL_QUESTIONS) if EVAL_QUESTIONS else 0.0
    mrr = mrr_sum / len(EVAL_QUESTIONS) if EVAL_QUESTIONS else 0.0

    print("\n" + "=" * 50)
    print(f"Recall@{k}: {recall_at_k:.2%}  ({recall_hits}/{len(EVAL_QUESTIONS)} perguntas)")
    print(f"MRR:       {mrr:.4f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
