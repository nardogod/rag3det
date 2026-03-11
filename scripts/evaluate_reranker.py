"""
Avalia o reranker fine-tuned vs genérico.

Entrada: data/training/rerank_pairs.jsonl
Saída: imprime NDCG@5 e AUC-ROC para:
  - baseline (cross-encoder/ms-marco-MiniLM-L-6-v2)
  - fine-tuned (models/reranker/3dt_finetuned/)

Uso (na raiz do projeto):
  python scripts/evaluate_reranker.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from collections import defaultdict
from typing import Dict, List, Tuple

from sentence_transformers import CrossEncoder

from src.ml.training.finetune_reranker import RERANK_PAIRS, BASE_MODEL, OUTPUT_DIR, RerankPair, load_pairs


def _group_by_query(pairs: List[RerankPair], max_pairs_per_query: int = 50) -> Dict[str, List[RerankPair]]:
    by_q: Dict[str, List[RerankPair]] = defaultdict(list)
    for p in pairs:
        if len(by_q[p.query]) >= max_pairs_per_query:
            continue
        by_q[p.query].append(p)
    return by_q


def _ndcg_at_k(scores_labels: List[Tuple[float, float]], k: int = 5) -> float:
    if not scores_labels:
        return 0.0
    scores_labels = sorted(scores_labels, key=lambda x: x[0], reverse=True)[:k]
    dcg = 0.0
    for i, (_, label) in enumerate(scores_labels):
        rel = float(label)
        dcg += (2**rel - 1.0) / (log2(i + 2))
    # Ideal DCG
    ideal = sorted(scores_labels, key=lambda x: x[1], reverse=True)
    idcg = 0.0
    for i, (_, label) in enumerate(ideal):
        rel = float(label)
        idcg += (2**rel - 1.0) / (log2(i + 2))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def log2(x: float) -> float:
    import math
    return math.log(x, 2.0)


def _auc_roc(scores_labels: List[Tuple[float, float]]) -> float:
    """
    Implementação simples de ROC-AUC baseada em ranks (Mann-Whitney).
    """
    if not scores_labels:
        return 0.0
    # Ordena por score crescente
    sorted_pairs = sorted(scores_labels, key=lambda x: x[0])
    pos_scores = [s for s, l in sorted_pairs if l > 0.5]
    neg_scores = [s for s, l in sorted_pairs if l <= 0.5]
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return 0.0
    # AUC ~ P(score_pos > score_neg)
    favorable = 0.0
    total = n_pos * n_neg
    for sp in pos_scores:
        for sn in neg_scores:
            if sp > sn:
                favorable += 1.0
            elif sp == sn:
                favorable += 0.5
    return favorable / total


def evaluate_model(model: CrossEncoder, grouped: Dict[str, List[RerankPair]], k: int = 5) -> Tuple[float, float]:
    ndcgs: List[float] = []
    auc_scores: List[float] = []

    for q, pairs in grouped.items():
        if len(pairs) < 2:
            continue
        inputs = [[q, p.doc_text] for p in pairs]
        labels = [p.label for p in pairs]
        scores = model.predict(inputs)
        scores = [float(s) for s in scores]
        sl = list(zip(scores, labels))
        ndcgs.append(_ndcg_at_k(sl, k=k))
        auc_scores.append(_auc_roc(sl))

    if not ndcgs:
        return 0.0, 0.0
    avg_ndcg = sum(ndcgs) / len(ndcgs)
    avg_auc = sum(auc_scores) / len(auc_scores) if auc_scores else 0.0
    return avg_ndcg, avg_auc


def main() -> None:
    pairs = load_pairs(RERANK_PAIRS)
    if not pairs:
        print(f"[ERRO] Nenhum par em {RERANK_PAIRS}. Rode scripts/generate_rerank_dataset.py primeiro.")
        return

    grouped = _group_by_query(pairs, max_pairs_per_query=50)
    print(f"[INFO] Queries para avaliação: {len(grouped)}")

    # Baseline (genérico)
    print("[INFO] Avaliando baseline:", BASE_MODEL)
    baseline_model = CrossEncoder(BASE_MODEL, num_labels=1, max_length=512)
    ndcg_b, auc_b = evaluate_model(baseline_model, grouped, k=5)

    # Fine-tuned
    finetuned_path = OUTPUT_DIR
    if not finetuned_path.exists():
        print(f"[ERRO] Modelo fine-tuned não encontrado em {finetuned_path}")
        return
    print("[INFO] Avaliando fine-tuned:", finetuned_path)
    finetuned_model = CrossEncoder(str(finetuned_path), num_labels=1, max_length=512)
    ndcg_f, auc_f = evaluate_model(finetuned_model, grouped, k=5)

    print("\n--- Avaliação Reranker ---")
    print(f"NDCG@5 baseline:   {ndcg_b:.4f}")
    print(f"NDCG@5 fine-tuned: {ndcg_f:.4f}")
    print(f"AUC-ROC baseline:   {auc_b:.4f}")
    print(f"AUC-ROC fine-tuned: {auc_f:.4f}")

    if ndcg_b > 0:
        imp = (ndcg_f - ndcg_b) / ndcg_b * 100.0
        print(f"Melhoria relativa NDCG@5: {imp:+.1f}%")


if __name__ == "__main__":
    main()

