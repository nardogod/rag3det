"""
Gera dataset de pares (query, documento, label) para fine-tuning do reranker (cross-encoder).

Estratégia geral (weak supervision):
- Usa queries de benchmark (ou uma lista padrão) e chunks de `data/processed/chunks.json`.
- Para cada query, obtém os top-K chunks via busca vetorial.
- Aplica heurísticas simples para marcar pares relevantes/irrelevantes e um nível de
  dificuldade aproximado (easy / medium / hard).

Saída:
  data/training/rerank_pairs.jsonl
  Cada linha: {"query": str, "doc_text": str, "label": 0/1, "difficulty": "easy|medium|hard"}
"""
from __future__ import annotations

import json
import re
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_core.documents import Document

from src.config import paths
from src.retrieval.pipeline import retrieve_relevant_chunks

DATA = paths.data_dir
TRAINING_DIR = DATA / "training"
PROCESSED_DIR = DATA / "processed"

BENCHMARK_QUERIES = TRAINING_DIR / "benchmark_queries.json"
OUT_PATH = TRAINING_DIR / "rerank_pairs.jsonl"

MIN_PAIRS = 1000

# Alvos explícitos de balanceamento
TARGET_POSITIVES = 500
TARGET_NEGATIVES = 500

STATS_PATTERN = re.compile(r"\b[FHRA]\s*[:=]\s*\d", flags=re.IGNORECASE)
PM_PATTERN = re.compile(r"\b\d+\s*PM\b", flags=re.IGNORECASE)
PE_PATTERN = re.compile(r"\b\d+\s*PE\b", flags=re.IGNORECASE)


def _load_benchmark_queries(max_n: int = 100) -> List[str]:
    if BENCHMARK_QUERIES.exists():
        with BENCHMARK_QUERIES.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        queries = [q.get("query") or "" for q in raw if q.get("query")]
        if queries:
            return queries[:max_n]
    # Fallback padrão
    default = [
        "Fênix",
        "Bola de Fogo",
        "stats do Ghoul",
        "custo de Cura Total",
        "Mãos de Fogo",
        "Magia Elemental de fogo",
        "Resistência à Magia",
        "Vulnerabilidade",
        "Invocação da Fênix",
        "Muralha de Fogo",
        "diferença entre Magia Branca e Magia Negra",
        "Corpo Elemental",
    ]
    return default * max(1, max_n // len(default))


def _detectar_tipo_query(q: str) -> str | None:
    """Heurística simples para tipo de entidade na query."""
    if any(k in q for k in ("magia", "feiti", "escola", "pm", "custa")):
        return "MAGIA"
    if any(k in q for k in ("monstro", "criatura", "ghoul", "dragão", "dragao", "vampiro", "zumbi")):
        return "MONSTRO"
    if any(k in q for k in ("item", "equipamento", "espada", "armadura", "anel")):
        return "ITEM"
    return None


def _detectar_tipo_doc(text: str, metadata: Dict[str, Any] | None) -> str | None:
    """Heurística simples para tipo de entidade no documento."""
    meta = metadata or {}
    t = text.lower()
    doc_type = (meta.get("entity_type") or meta.get("type") or "").upper()
    if doc_type in ("MAGIA", "MONSTRO", "ITEM"):
        return doc_type
    if STATS_PATTERN.search(text):
        return "MONSTRO"
    if PE_PATTERN.search(text) or "preço" in t or "preco" in t:
        return "ITEM"
    if "magia" in t or "escola" in t:
        return "MAGIA"
    return None


def _heuristic_relevance(
    query: str,
    doc_text: str,
    metadata: Dict[str, Any] | None = None,
    rank: int | None = None,
) -> Tuple[int, str]:
    """
    Heurísticas simples para rotular relevância e dificuldade.
    Retorna (label, difficulty).
    """
    q = query.lower()
    t = doc_text.lower()

    # Easy positives
    if "stats" in q or "atributos" in q:
        if STATS_PATTERN.search(doc_text):
            return 1, "easy"
        if "f:" in t or "h:" in t or "r:" in t or "a:" in t:
            return 1, "easy"
    if "custo" in q or "pm" in q:
        if PM_PATTERN.search(doc_text):
            return 1, "easy"
    # Query menciona nome; doc menciona também
    tokens = [tok for tok in re.split(r"\W+", q) if len(tok) > 3]
    if tokens and any(tok in t for tok in tokens):
        # Se também tiver padrão de stats ou custo, considere easy; senão medium
        if STATS_PATTERN.search(doc_text) or PM_PATTERN.search(doc_text):
            return 1, "easy"
        return 1, "medium"

    # Negatives (easy): tipo claramente errado (MAGIA vs MONSTRO/ITEM), usando tipo inferido
    q_tipo = _detectar_tipo_query(q)
    d_tipo = _detectar_tipo_doc(doc_text, metadata)
    if q_tipo and d_tipo:
        if q_tipo == "MAGIA" and d_tipo == "MONSTRO":
            return 0, "easy"
        if q_tipo == "MONSTRO" and d_tipo == "MAGIA":
            return 0, "easy"
        if q_tipo != "ITEM" and d_tipo == "ITEM":
            return 0, "easy"

    # Heurística legada baseada em palavras-chave
    magia_like_q = any(k in q for k in ("magia", "custa", "pm"))
    monstro_stats_doc = STATS_PATTERN.search(doc_text) is not None
    if magia_like_q and monstro_stats_doc:
        return 0, "easy"

    if "magia" in q and "monstro" in t:
        return 0, "easy"

    monstro_like_q = "monstro" in q or "criatura" in q
    if monstro_like_q and PE_PATTERN.search(doc_text):
        # Doc parece item com preço em PE
        return 0, "easy"
    if "monstro" in q and "magia" in t:
        return 0, "easy"

    # Negatives (medium): elemento / função oposta
    if "fogo" in q and any(k in t for k in ("gelo", "frio", "neve", "água", "agua")):
        return 0, "medium"
    if "gelo" in q and "fogo" in t:
        return 0, "medium"
    if "cura" in q and any(k in t for k in ("dano", "ataque", "explos", "golpe", "rajada")):
        return 0, "medium"
    if any(k in q for k in ("dano", "ataque", "explos", "golpe", "rajada")) and "cura" in t:
        return 0, "medium"

    # Negatives (hard): função oposta no mesmo tipo/elemento
    if "bola de fogo" in q and "muralha de fogo" in t:
        return 0, "hard"
    if "muralha de fogo" in q and "bola de fogo" in t:
        return 0, "hard"
    if "fogo" in q and "fogo" in t:
        attack_q = any(k in q for k in ("bola de fogo", "explos", "ataque", "rajada"))
        defence_t = any(k in t for k in ("muralha", "barreira", "proteção", "protecao", "escudo"))
        if attack_q and defence_t:
            return 0, "hard"

    # Hard cases: mesmo nome / elemento mas contexto possivelmente diferente
    if "fênix" in q and "fênix" in t:
        # Se não houver stats nem custo, tratamos como potencial hard negative
        if not STATS_PATTERN.search(doc_text) and not PM_PATTERN.search(doc_text):
            return 0, "hard"
        return 1, "hard"
    if "bola de fogo" in q and "fogo" in t:
        # Pode ser magia ou outro contexto de fogo
        if "magia" in t or "escola" in t:
            return 1, "hard"
        return 0, "hard"

    # Dragão em contexto não RPG (ex.: constelação)
    if ("dragão" in q or "dragao" in q) and ("dragão" in t or "dragao" in t):
        if "constelação" in t or "constelacao" in t or "zodíaco" in t or "zodiaco" in t:
            return 0, "hard"

    # Ranking baixo (top 15-20): negativos fáceis se nada bateu
    if rank is not None and rank >= 15:
        return 0, "easy"

    # Fallback: desconhecido (label -1)
    return -1, "unknown"


def _vector_candidates_for_query(query: str, k: int = 20) -> List[Tuple[Document, float]]:
    """
    Usa apenas a etapa vetorial (via retrieve_relevant_chunks com baseline) como fonte de candidatos.
    """
    # retrieve_relevant_chunks já aplica híbrido+rerank; aqui preferimos só vetorial,
    # mas para simplificar reusamos a saída final como candidatos.
    chunks = retrieve_relevant_chunks(query, k=k, use_baseline=True)
    docs_with_score: List[Tuple[Document, float]] = []
    for ch in chunks:
        # Reconstituir Document-like com page_content a partir do RetrievedChunk.
        meta = ch.metadata or {}
        docs_with_score.append(
            (
                Document(page_content=ch.content, metadata=meta),
                float(ch.score or 0.0),
            )
        )
    return docs_with_score


def generate_pairs(seed: int = 42, min_pairs: int = MIN_PAIRS) -> Dict[str, Any]:
    rng = random.Random(seed)
    queries = _load_benchmark_queries(max_n=100)
    if not queries:
        return {"error": "Nenhuma query disponível para gerar pares de reranking.", "pairs": 0}

    positives: List[Dict[str, Any]] = []
    negatives: List[Dict[str, Any]] = []
    all_candidates: List[Tuple[str, str, Dict[str, Any]]] = []

    for q in queries:
        candidates = _vector_candidates_for_query(q, k=20)
        if not candidates:
            continue
        for idx, (doc, _score) in enumerate(candidates):
            text = doc.page_content or ""
            meta = doc.metadata or {}
            all_candidates.append((q, text, meta))
            label, difficulty = _heuristic_relevance(q, text, metadata=meta, rank=idx)
            if label not in (0, 1):
                continue
            row = {
                "query": q,
                "doc_text": text.strip(),
                "label": int(label),
                "difficulty": difficulty,
            }
            if label == 1:
                positives.append(row)
            else:
                negatives.append(row)

    total = len(positives) + len(negatives)
    if total < min_pairs:
        print(f"[WARN] Apenas {total} pares gerados (mínimo desejado: {min_pairs}).")

    # Garantia adicional: se houver poucos negativos, tentar gerar mais a partir de candidatos arbitrários
    if negatives and positives and len(negatives) < len(positives) * 0.5 and all_candidates:
        rng.shuffle(all_candidates)
        attempts = 0
        max_attempts = 5000
        while len(negatives) < len(positives) and attempts < max_attempts:
            attempts += 1
            q_rand, text_rand, meta_rand = rng.choice(all_candidates)
            lbl, diff = _heuristic_relevance(q_rand, text_rand, metadata=meta_rand, rank=None)
            if lbl == 1:
                continue
            row = {
                "query": q_rand,
                "doc_text": text_rand.strip(),
                "label": 0,
                "difficulty": diff if diff != "unknown" else "easy",
            }
            negatives.append(row)

    rng.shuffle(positives)
    rng.shuffle(negatives)

    # Seleção balanceada por label
    pos_target = min(TARGET_POSITIVES, len(positives))
    neg_target = min(TARGET_NEGATIVES, len(negatives))

    selected_pos = positives[:pos_target]
    selected_neg = negatives[:neg_target]

    selected: List[Dict[str, Any]] = []
    selected.extend(selected_pos)
    selected.extend(selected_neg)

    # Se ainda faltar até min_pairs, completa com o que sobrar (aceitando desbalanceamento leve)
    remaining = max(0, min_pairs - len(selected))
    if remaining > 0:
        pool = positives[pos_target:] + negatives[neg_target:]
        rng.shuffle(pool)
        selected.extend(pool[:remaining])

    rng.shuffle(selected)

    # Salvar jsonl
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for row in selected:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_label = defaultdict(int)
    by_difficulty = defaultdict(int)
    for r in selected:
        by_label[int(r["label"])] += 1
        by_difficulty[r["difficulty"]] += 1

    pos_count = by_label.get(1, 0)
    neg_count = by_label.get(0, 0)
    ratio = float(pos_count) / float(neg_count) if pos_count and neg_count else 0.0
    print(f"Total de pares: {len(selected)} (positivos={pos_count}, negativos={neg_count}, razão={ratio:.2f})")
    if neg_count == 0 or ratio < 0.3 or ratio > 3.0:
        print("[WARN] Dataset desbalanceado (razão positivos/negativos fora do intervalo [0.3, 3.0]).")

    stats = {
        "total_pairs": len(selected),
        "by_label": dict(by_label),
        "by_difficulty": dict(by_difficulty),
        "pos_neg_ratio": ratio,
        "paths": {"rerank_pairs": str(OUT_PATH)},
    }
    return stats


if __name__ == "__main__":
    info = generate_pairs()
    print(json.dumps(info, ensure_ascii=False, indent=2))

