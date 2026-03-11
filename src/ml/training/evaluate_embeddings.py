"""
Benchmark de Information Retrieval: embeddings fine-tuned vs baseline.

Métricas: MRR@10, Recall@5, NDCG@5, MAP.
Comparação: modelo genérico (baseline) vs modelo fine-tuned no domínio 3D&T.
Critério de aceitação: MRR melhorou >= 15% vs baseline.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.config import paths

DATA = paths.data_dir
PROJECT_ROOT = paths.project_root
TRAINING_DIR = DATA / "training"
BENCHMARK_QUERIES = TRAINING_DIR / "benchmark_queries.json"
CHUNKS_PATH = DATA / "processed" / "chunks.json"
BASELINE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FINETUNED_PATH = PROJECT_ROOT / "models" / "embeddings" / "3dt_finetuned"
REPORT_PATH = PROJECT_ROOT / "models" / "embeddings" / "evaluation_report.json"
MAX_CORPUS_SIZE = 12_000  # chunks para manter avaliação rápida
MRR_IMPROVEMENT_THRESHOLD = 0.15  # 15%


def load_chunks(max_chunks: int = MAX_CORPUS_SIZE) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Retorna (textos dos chunks, doc_ids, metadatas). doc_id = source:page."""
    if not CHUNKS_PATH.exists():
        return [], [], []
    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return [], [], []
    texts = []
    doc_ids = []
    metadatas = []
    for i, item in enumerate(raw):
        if i >= max_chunks:
            break
        if isinstance(item, dict):
            content = item.get("page_content") or ""
            meta = item.get("metadata") or {}
            src = meta.get("source") or meta.get("book_title") or ""
            page = meta.get("page", i)
            doc_id = f"{src}:{page}" if src else f"chunk_{i}"
            texts.append(content)
            doc_ids.append(doc_id)
            metadatas.append(meta)
    return texts, doc_ids, metadatas


def load_benchmark_queries() -> List[Dict[str, Any]]:
    """Carrega queries do benchmark."""
    if not BENCHMARK_QUERIES.exists():
        return []
    with BENCHMARK_QUERIES.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_ground_truth(
    queries: List[Dict[str, Any]],
    corpus_texts: List[str],
    doc_ids: List[str],
) -> List[Dict[str, Any]]:
    """Para cada query, define relevant_docs via heurística."""
    stats_re = re.compile(r"\b(F|H|R|A)\s*[:.]?\s*\d+|\b(PV|PM)\s*[:.]?\s*\d+", re.I)
    definition_re = re.compile(r"\b(é|são|funciona|permite|magia|escola)\b", re.I)
    out = []
    for q in queries:
        targets = q.get("targets") or []
        require_stats = q.get("require_stats", False)
        require_definition = q.get("require_definition", False)
        category = q.get("category", "")
        relevant = []
        for idx, (text, doc_id) in enumerate(zip(corpus_texts, doc_ids)):
            text_lower = text.lower()
            if not any(t.lower() in text_lower for t in targets):
                continue
            if require_stats and not stats_re.search(text):
                continue
            if require_definition and not definition_re.search(text):
                continue
            if category == "comparações" and len(targets) >= 2:
                if sum(1 for t in targets if t.lower() in text_lower) < 2:
                    continue
            relevant.append(doc_id)
        out.append({
            "query": q["query"],
            "category": q["category"],
            "relevant_docs": list(dict.fromkeys(relevant)),
        })
    return out


def _embed(model: Any, texts: List[str], batch_size: int = 32) -> Any:
    """Retorna array de embeddings (model pode ser SentenceTransformer ou HuggingFaceEmbeddings)."""
    if hasattr(model, "encode"):
        return model.encode(texts, batch_size=batch_size, show_progress_bar=len(texts) > 100)
    if hasattr(model, "embed_documents"):
        out = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            out.extend(model.embed_documents(batch))
        return out
    raise TypeError("Model must have encode or embed_documents")


def compute_metrics(
    ranked_doc_ids: List[List[str]],
    ground_truth: List[Dict[str, Any]],
    k_mrr: int = 10,
    k_recall: int = 5,
    k_ndcg: int = 5,
) -> Dict[str, float]:
    """Calcula MRR@k, Recall@k, NDCG@k e MAP."""
    import math
    mrr_sum = 0.0
    recall_sum = 0.0
    ndcg_sum = 0.0
    map_sum = 0.0
    n = len(ground_truth)
    if n == 0:
        return {"MRR@10": 0.0, "Recall@5": 0.0, "NDCG@5": 0.0, "MAP": 0.0}

    for i, gt in enumerate(ground_truth):
        rel_set = set(gt["relevant_docs"])
        if not rel_set:
            continue
        rank_list = ranked_doc_ids[i] if i < len(ranked_doc_ids) else []
        # MRR@10
        for r, doc_id in enumerate(rank_list[:k_mrr], 1):
            if doc_id in rel_set:
                mrr_sum += 1.0 / r
                break
        # Recall@5
        top5 = set(rank_list[:k_recall])
        recall_sum += len(rel_set & top5) / len(rel_set)
        # NDCG@5
        dcg = 0.0
        for r, doc_id in enumerate(rank_list[:k_ndcg], 1):
            if doc_id in rel_set:
                dcg += 1.0 / math.log2(r + 1)
        idcg = sum(1.0 / math.log2(ii + 2) for ii in range(min(len(rel_set), k_ndcg)))
        ndcg_sum += (dcg / idcg) if idcg > 0 else 0.0
        # MAP: cada documento relevante conta só na primeira aparição
        hits = 0
        prec_sum = 0.0
        seen = set()
        for r, doc_id in enumerate(rank_list, 1):
            if doc_id in rel_set and doc_id not in seen:
                seen.add(doc_id)
                hits += 1
                prec_sum += hits / r
        map_sum += prec_sum / len(rel_set) if rel_set else 0.0

    return {
        "MRR@10": mrr_sum / n,
        "Recall@5": recall_sum / n,
        "NDCG@5": ndcg_sum / n,
        "MAP": map_sum / n,
    }


def run_retrieval(
    model: Any,
    queries: List[str],
    corpus_texts: List[str],
    doc_ids: List[str],
    batch_size: int = 32,
) -> List[List[str]]:
    """Retorna ranked_doc_ids por query (top primeiro)."""
    import numpy as np
    q_emb = _embed(model, queries, batch_size=batch_size)
    d_emb = _embed(model, corpus_texts, batch_size=batch_size)
    if hasattr(q_emb, "numpy"):
        q_emb = q_emb.numpy()
    if hasattr(d_emb, "numpy"):
        d_emb = d_emb.numpy()
    q_emb = np.asarray(q_emb, dtype=np.float32)
    d_emb = np.asarray(d_emb, dtype=np.float32)
    # normalizar para cosine = dot
    qn = np.linalg.norm(q_emb, axis=1, keepdims=True)
    qn[qn == 0] = 1
    q_emb = q_emb / qn
    dn = np.linalg.norm(d_emb, axis=1, keepdims=True)
    dn[dn == 0] = 1
    d_emb = d_emb / dn
    scores = q_emb @ d_emb.T
    ranked = []
    for i in range(len(queries)):
        order = np.argsort(-scores[i])
        ranked.append([doc_ids[j] for j in order])
    return ranked


def load_baseline_model():
    """Carrega modelo baseline (SentenceTransformer)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(BASELINE_MODEL)


def load_finetuned_model():
    """Carrega modelo fine-tuned se existir."""
    from sentence_transformers import SentenceTransformer
    path = FINETUNED_PATH / "config_sentence_transformers.json"
    if not path.exists():
        return None
    return SentenceTransformer(str(FINETUNED_PATH))


def run_benchmark(
    baseline_model: Any,
    finetuned_model: Any | None,
    ground_truth: List[Dict[str, Any]],
    corpus_texts: List[str],
    doc_ids: List[str],
) -> Dict[str, Any]:
    """Executa retrieval com baseline e (opcional) fine-tuned; retorna métricas e report."""
    queries = [g["query"] for g in ground_truth]

    report = {"queries_count": len(queries), "corpus_size": len(corpus_texts)}

    # Baseline
    ranked_baseline = run_retrieval(baseline_model, queries, corpus_texts, doc_ids)
    metrics_baseline = compute_metrics(ranked_baseline, ground_truth)
    report["baseline"] = {"model": BASELINE_MODEL, "metrics": metrics_baseline}

    if finetuned_model is not None:
        ranked_ft = run_retrieval(finetuned_model, queries, corpus_texts, doc_ids)
        metrics_ft = compute_metrics(ranked_ft, ground_truth)
        report["finetuned"] = {"model_path": str(FINETUNED_PATH), "metrics": metrics_ft}
        # Deltas percentuais
        deltas = {}
        for k in metrics_baseline:
            b = metrics_baseline[k]
            f = metrics_ft[k]
            if b != 0:
                deltas[k] = (f - b) / b
            else:
                deltas[k] = (f - b) * 100.0 if f != b else 0.0
        report["deltas_pct"] = deltas
        report["mrr_improvement_pct"] = deltas.get("MRR@10", 0.0)
        report["acceptance"] = report["mrr_improvement_pct"] >= MRR_IMPROVEMENT_THRESHOLD
    else:
        report["finetuned"] = None
        report["deltas_pct"] = None
        report["mrr_improvement_pct"] = None
        report["acceptance"] = False

    return report


def run_visualization(
    baseline_model: Any,
    finetuned_model: Any | None,
    corpus_texts: List[str],
    doc_ids: List[str],
    labels: List[str] | None,
    output_dir: Path,
    max_points: int = 800,
) -> None:
    """Gera t-SNE/UMAP de embeddings antes/depois (opcional)."""
    try:
        import numpy as np
        from sklearn.manifold import TSNE
    except ImportError:
        return
    n = min(max_points, len(corpus_texts))
    indices = np.linspace(0, len(corpus_texts) - 1, n, dtype=int)
    texts = [corpus_texts[i] for i in indices]
    lbl = [labels[i] for i in indices] if labels and len(labels) == len(corpus_texts) else None
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def _tsne_plot(emb, title: str, path: Path) -> None:
        emb = np.asarray(emb, dtype=np.float32)
        if emb.shape[0] != n:
            emb = np.asarray(emb)[indices]
        X = TSNE(n_components=2, random_state=42, perplexity=min(30, n - 1)).fit_transform(emb)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8, 6))
            if lbl:
                for u in set(lbl):
                    mask = [i for i in range(n) if lbl[i] == u]
                    plt.scatter(X[mask, 0], X[mask, 1], label=u, alpha=0.6, s=20)
                plt.legend(loc="best", fontsize=8)
            else:
                plt.scatter(X[:, 0], X[:, 1], alpha=0.6, s=20)
            plt.title(title)
            plt.tight_layout()
            plt.savefig(path, dpi=120)
            plt.close()
        except Exception:
            pass

    emb_b = _embed(baseline_model, texts)
    _tsne_plot(emb_b, "Embeddings (baseline)", output_dir / "tsne_baseline.png")
    if finetuned_model is not None:
        emb_f = _embed(finetuned_model, texts)
        _tsne_plot(emb_f, "Embeddings (fine-tuned)", output_dir / "tsne_finetuned.png")


def infer_section_labels(corpus_texts: List[str], metadata_list: List[Dict] | None) -> List[str]:
    """Infer labels para visualização (magia, monstro, item, outro) a partir de section/metadata ou texto."""
    if metadata_list and len(metadata_list) == len(corpus_texts):
        out = []
        for m in metadata_list:
            sec = (m.get("section") or m.get("section_title") or "").lower()
            if "magia" in sec or "magic" in sec:
                out.append("magia")
            elif "monstro" in sec or "bestiário" in sec or "criatura" in sec:
                out.append("monstro")
            elif "item" in sec or "equipamento" in sec:
                out.append("item")
            else:
                out.append("outro")
        return out
    out = []
    for text in corpus_texts:
        t = text.lower()
        if "magia" in t and ("custa" in t or "PM" in t or "escola" in t):
            out.append("magia")
        elif any(x in t for x in ("F0", "F1", "H0", "R0", "A0", "PV ", "PM ")) and ("monstro" in t or "criatura" in t):
            out.append("monstro")
        elif "PE" in t and ("preço" in t or "custa" in t):
            out.append("item")
        else:
            out.append("outro")
    return out


def run_evaluation(
    max_corpus: int = MAX_CORPUS_SIZE,
    run_viz: bool = True,
    output_report_path: Path | None = None,
) -> Dict[str, Any]:
    """
    Pipeline completo: carrega chunks, benchmark, modelos, executa IR e gera report.
    Retorna o report e salva em models/embeddings/evaluation_report.json.
    """
    output_report_path = output_report_path or REPORT_PATH
    corpus_texts, doc_ids, metadata_list = load_chunks(max_chunks=max_corpus)
    if not corpus_texts:
        return {"error": f"Nenhum chunk em {CHUNKS_PATH}. Rode o pipeline de ingestão."}

    raw_queries = load_benchmark_queries()
    if not raw_queries:
        return {"error": f"Nenhuma query em {BENCHMARK_QUERIES}."}

    ground_truth = build_ground_truth(raw_queries, corpus_texts, doc_ids)
    # remover queries sem relevantes (opcional: manter e deixar recall 0)
    ground_truth = [g for g in ground_truth if g["relevant_docs"]]
    if not ground_truth:
        return {"error": "Nenhuma query com documentos relevantes (heurística)."}

    baseline_model = load_baseline_model()
    finetuned_model = load_finetuned_model()

    report = run_benchmark(baseline_model, finetuned_model, ground_truth, corpus_texts, doc_ids)

    if run_viz and len(corpus_texts) >= 100:
        try:
            labels = infer_section_labels(corpus_texts, metadata_list if metadata_list else None)
            run_visualization(
                baseline_model,
                finetuned_model,
                corpus_texts,
                doc_ids,
                labels,
                output_dir=REPORT_PATH.parent,
                max_points=800,
            )
            report["visualization"] = {
                "tsne_baseline": str(REPORT_PATH.parent / "tsne_baseline.png"),
                "tsne_finetuned": str(REPORT_PATH.parent / "tsne_finetuned.png") if finetuned_model else None,
            }
        except Exception as e:
            report["visualization"] = {"error": str(e)}

    report["recommendations"] = []
    if report.get("acceptance") is False and finetuned_model is not None:
        report["recommendations"] = [
            "Aumentar dataset de treino (mais triplas).",
            "Aumentar epochs (com cuidado para overfit).",
            "Tentar modelo base diferente (ex.: distiluse-base-multilingual-cased-v1).",
        ]

    output_report_path = Path(output_report_path)
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report
