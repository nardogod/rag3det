"""
Descoberta automática de taxonomia por co-ocorrência: TF-IDF + K-Means nos contexts.

- Stopwords PT-BR removidas; min_df=2, max_df=0.8; n-grams opcionais.
- Pós-processamento: remove clusters só com stopwords, mescla similares, nome por 3 termos.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

from src.ml.taxonomy.portuguese_stopwords import STOPWORDS_PT_BR, filter_stopwords_from_terms

try:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def _cluster_name(common_terms: List[str], max_words: int = 3) -> str:
    """Nomeia cluster pelos termos mais representativos (não genéricos), snake_case."""
    filtered = filter_stopwords_from_terms(common_terms, min_len=2)[:max_words]
    if not filtered:
        return ""
    return "_".join(w.lower().replace(" ", "_") for w in filtered)


def _is_stopword_only_cluster(terms: List[str]) -> bool:
    """True se todos os termos são stopwords."""
    return all((t or "").lower() in STOPWORDS_PT_BR for t in terms)


def _cluster_overlap(a: List[str], b: List[str], threshold: float = 0.7) -> float:
    """Jaccard-like: |intersection| / min(|a|,|b|)."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def discover_taxonomy(
    entities_path: Path,
    output_path: Path,
    n_clusters: int = 10,
    max_df: float = 0.8,
    min_df: int = 2,
    use_ngrams: bool = True,
) -> Dict[str, Any]:
    """
    Lê entidades, vetoriza com TF-IDF (stopwords PT-BR), K-Means.
    Pós-processa: remove clusters stopword-only, mescla overlap > 70%, nome por 3 termos.
    Saída: terms (não common_terms) e description melhorada.
    """
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn é necessário: pip install scikit-learn")

    if not entities_path.exists():
        return {"clusters": {}}

    with entities_path.open("r", encoding="utf-8") as f:
        entities = json.load(f)

    names = []
    texts = []
    for name, data in entities.items():
        names.append(name)
        contexts = data.get("contexts") or []
        texts.append(" ".join(contexts)[:2000])

    if len(texts) < n_clusters:
        n_clusters = max(1, len(texts) // 2)

    vectorizer = TfidfVectorizer(
        max_df=max_df,
        min_df=min_df,
        max_features=500,
        strip_accents="unicode",
        stop_words=list(STOPWORDS_PT_BR),
        ngram_range=(1, 2) if use_ngrams else (1, 1),
    )
    X = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out().tolist()
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_

    clusters: Dict[str, Dict[str, Any]] = {}
    for i in range(n_clusters):
        indices = [j for j, l in enumerate(labels) if l == i]
        if not indices:
            continue
        top = centers[i].argsort()[-10:][::-1]
        common_terms = [feature_names[k] for k in top if k < len(feature_names)]
        if _is_stopword_only_cluster(common_terms):
            continue
        terms = filter_stopwords_from_terms(common_terms)
        cluster_id = _cluster_name(terms, max_words=3) or f"cluster_{i}"
        entity_list = [names[j] for j in indices]
        clusters[cluster_id] = {
            "entities": entity_list,
            "terms": terms[:8],
            "description": " ".join(terms[:5]) if terms else "",
        }

    # Mesclar clusters com overlap > 70%
    merged: Dict[str, Dict[str, Any]] = {}
    used: Set[str] = set()
    for cid, c in clusters.items():
        if cid in used:
            continue
        merged[cid] = dict(c)
        for cid2, c2 in clusters.items():
            if cid2 == cid or cid2 in used:
                continue
            if _cluster_overlap(c["entities"], c2["entities"]) >= 0.7:
                merged[cid]["entities"] = list(set(merged[cid]["entities"]) | set(c2["entities"]))
                merged[cid]["terms"] = list(dict.fromkeys((merged[cid]["terms"] + c2["terms"])[:8]))
                merged[cid]["description"] = " ".join(merged[cid]["terms"][:5])
                used.add(cid2)
        used.add(cid)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out = {"clusters": merged}
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out
