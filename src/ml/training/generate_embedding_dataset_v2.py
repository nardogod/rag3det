"""
Gera dataset de triplas (anchor, positive, negative) focado em hard negatives para 3D&T.

Novas estratégias (v2):
  a) Ambiguidade de Nome (30%): mesma raiz de nome, tipos diferentes (MAGIA, MONSTRO, ITEM).
  b) Mesmo Elemento, Tipo Diferente (25%): mesmo elemento (fogo, gelo...) mas tipos diferentes.
  c) Mesmo Tipo, Função Diferente (20%): todas MAGIA, mas cura vs dano (funções opostas).
  d) Nível de Poder (15%): mesmo elemento, mas "baixo nível" vs "alto nível".
  e) Sinônimos e Variações (10%): nomes muito parecidos vs elemento oposto.

Formato saída: {"anchor": "...", "positive": "...", "negative": "...", "weight": float, "strategy": str}
Mínimo 3000 triplas; divisão 85% train, 15% val.

As heurísticas usam:
  - extracted_entities.json (type, contexts, stats)
  - entity_properties.json (opcional) para hints adicionais
"""
from __future__ import annotations

import json
import random
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from src.config import paths
from src.ml.training.generate_embedding_dataset import (  # reaproveita utilitários v1
    _entities_by_type,
    _load_entities,
    _load_properties,
    _make_description,
    OUT_DIR,
    TRAIN_RATIO,
    save_jsonl,
    split_train_val,
)

DATA = paths.data_dir
ENTITIES_PATH = DATA / "entities" / "extracted_entities.json"
PROPERTIES_PATH = DATA / "properties" / "entity_properties.json"

MIN_TRIPLES_V2 = 3000

# Proporções desejadas para v2
RATIO_AMBIG_NAME = 0.30
RATIO_SAME_ELEMENT_DIFF_TYPE = 0.25
RATIO_SAME_TYPE_DIFF_FUNC = 0.20
RATIO_POWER_LEVEL = 0.15
RATIO_SYNONYM = 0.10

WEIGHT_AMBIG_NAME = 1.0
WEIGHT_SAME_ELEMENT_DIFF_TYPE = 0.9
WEIGHT_SAME_TYPE_DIFF_FUNC = 0.9
WEIGHT_POWER_LEVEL = 0.8
WEIGHT_SYNONYM = 0.8


def _normalize_text(s: str) -> str:
    """Normaliza para comparações frouxas (lower + remover acentos)."""
    s = s.lower()
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _iter_entities(entities: Dict[str, Dict]) -> Iterable[Tuple[str, Dict]]:
    for name, data in entities.items():
        if isinstance(data, dict) and data.get("type"):
            yield name, data


def _infer_element(name: str, data: Dict, properties: Dict[str, Dict]) -> str | None:
    """Inferir elemento (fogo, gelo, etc.) a partir do nome + contextos."""
    text_parts: List[str] = [name]
    ctx = data.get("contexts") or []
    if isinstance(ctx, list):
        text_parts.extend(str(c) for c in ctx)
    prop = properties.get(name)
    if isinstance(prop, dict):
        ev = prop.get("evidence") or {}
        if isinstance(ev, dict):
            text_parts.extend(str(v) for v in ev.values())
    txt = _normalize_text(" ".join(text_parts))

    if any(k in txt for k in ("fogo", "chama", "flamej", "incendi", "magia de fogo")):
        return "FOGO"
    if any(k in txt for k in ("gelo", "frio", "neve", "geada")):
        return "GELO"
    if any(k in txt for k in ("luz", "radiante", "sagrado")):
        return "LUZ"
    if any(k in txt for k in ("trevas", "sombria", "sombrio", "necr", "morto-vivo")):
        return "TREVAS"
    return None


def _infer_function(name: str, data: Dict) -> str | None:
    """Inferir função da magia (CURAR, DANO) por palavras-chave."""
    if data.get("type") != "MAGIA":
        return None
    text_parts: List[str] = [name]
    ctx = data.get("contexts") or []
    if isinstance(ctx, list):
        text_parts.extend(str(c) for c in ctx)
    txt = _normalize_text(" ".join(text_parts))
    if any(k in txt for k in ("cura", "curar", "curativo", "healing", "restaur", "reviver", "ressuscitar")):
        return "CURAR"
    if any(k in txt for k in ("dano", "explos", "ataque", "misse", "projeteis", "golpe", "rajada", "bola de fogo")):
        return "DANO"
    return None


def _infer_power_level(name: str, data: Dict) -> str | None:
    """Classifica em BAIXO/NORMAL/ALTO de forma heurística."""
    text_parts: List[str] = [name]
    ctx = data.get("contexts") or []
    if isinstance(ctx, list):
        text_parts.extend(str(c) for c in ctx)
    txt = _normalize_text(" ".join(text_parts))
    # Alto nível: palavras fortes
    if any(k in txt for k in ("inferno de fogo", "apocalipse", "suprema", "supremo", "tempestade", "meteoro", "destruicao total")):
        return "ALTO"
    # Baixo nível: nomes de truques simples
    if any(k in txt for k in ("tranca", "toque", "truque", "basica", "simples")):
        return "BAIXO"
    return "NORMAL"


def _tokenize_name(name: str) -> List[str]:
    txt = _normalize_text(name)
    for ch in ",.;:!?()/\\":
        txt = txt.replace(ch, " ")
    tokens = [t for t in txt.split() if len(t) > 2]
    return tokens


def _build_name_buckets(entities: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Cria buckets por "raiz" de nome: token principal em comum.
    Ex.: tudo que contém 'fenix', 'fogo', etc.
    """
    buckets: Dict[str, List[str]] = defaultdict(list)
    for name, data in _iter_entities(entities):
        tokens = _tokenize_name(name)
        if not tokens:
            continue
        # Escolhe o token mais "distintivo": o mais longo
        key = max(tokens, key=len)
        buckets[key].append(name)
    return buckets


def _pick_many(seq: Sequence[str], k: int, rng: random.Random) -> List[str]:
    if not seq or k <= 0:
        return []
    if len(seq) <= k:
        return list(seq)
    return rng.sample(list(seq), k=k)


def generate_ambiguity_name_pairs(
    entities: Dict[str, Dict],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Ambiguidade de nome: mesma raiz em nomes diferentes, tipos diferentes.
    Ex.: Fênix magia vs Fênix criatura, etc.
    """
    out: List[Dict[str, Any]] = []
    buckets = _build_name_buckets(entities)
    # Seleciona apenas buckets com pelo menos 2 entidades de tipos diferentes
    candidate_buckets: List[List[str]] = []
    for _, names in buckets.items():
        types = {entities[n].get("type") for n in names if isinstance(entities.get(n), dict)}
        if len(types - {None}) >= 2 and len(names) >= 2:
            candidate_buckets.append(names)

    if not candidate_buckets:
        return out

    while len(out) < n_target:
        names = rng.choice(candidate_buckets)
        a, b = rng.sample(names, 2)
        da, db = entities.get(a, {}), entities.get(b, {})
        ta, tb = da.get("type"), db.get("type")
        if not ta or not tb or ta == tb:
            continue
        # Anchor: a (prioriza magias quando possível)
        if ta != "MAGIA" and tb == "MAGIA":
            anchor_name, other_name = b, a
            da, db = db, da
        else:
            anchor_name, other_name = a, b
        anchor_desc = _make_description(anchor_name, entities, _load_properties())
        other_desc = _make_description(other_name, entities, _load_properties())
        out.append(
            {
                "anchor": anchor_name,
                "positive": anchor_desc,
                "negative": other_desc,
                "weight": WEIGHT_AMBIG_NAME,
                "strategy": "v2_ambiguity_name",
            }
        )
        if len(out) >= n_target:
            break
    return out


def generate_same_element_diff_type_pairs(
    entities: Dict[str, Dict],
    properties: Dict[str, Dict],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Mesmo elemento (ex. fogo), tipos diferentes.
    Anchor: MAGIA de elemento X.
    Positive: outra MAGIA de elemento X.
    Negative: ITEM/MONSTRO/OUTRO tipo com mesmo elemento.
    """
    out: List[Dict[str, Any]] = []
    by_element_type: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for name, data in _iter_entities(entities):
        el = _infer_element(name, data, properties)
        if not el:
            continue
        t = data.get("type")
        by_element_type[(el, t)].append(name)

    magias_by_element: Dict[str, List[str]] = defaultdict(list)
    others_by_element: Dict[str, List[str]] = defaultdict(list)
    for (el, t), names in by_element_type.items():
        if t == "MAGIA":
            magias_by_element[el].extend(names)
        else:
            others_by_element[el].extend(names)

    elements = [el for el in magias_by_element.keys() if others_by_element.get(el)]
    if not elements:
        return out

    while len(out) < n_target:
        el = rng.choice(elements)
        magias = magias_by_element[el]
        others = [n for n in others_by_element[el] if n not in magias]
        if len(magias) < 2 or not others:
            continue
        anchor = rng.choice(magias)
        positive = rng.choice([m for m in magias if m != anchor])
        negative = rng.choice(others)
        out.append(
            {
                "anchor": anchor,
                "positive": _make_description(positive, entities, properties),
                "negative": _make_description(negative, entities, properties),
                "weight": WEIGHT_SAME_ELEMENT_DIFF_TYPE,
                "strategy": "v2_same_element_diff_type",
            }
        )
    return out


def generate_same_type_diff_function_pairs(
    entities: Dict[str, Dict],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Mesmo tipo (MAGIA), funções diferentes (cura vs dano).
    Anchor: magia de cura; positives: outras magias de cura; negatives: magias de dano.
    """
    out: List[Dict[str, Any]] = []
    by_func: Dict[str, List[str]] = defaultdict(list)
    for name, data in _iter_entities(entities):
        func = _infer_function(name, data)
        if not func:
            continue
        by_func[func].append(name)

    curas = by_func.get("CURAR") or []
    danos = by_func.get("DANO") or []
    if not curas or not danos:
        return out

    while len(out) < n_target:
        anchor = rng.choice(curas)
        positive_candidates = [c for c in curas if c != anchor]
        if not positive_candidates:
            break
        positive = rng.choice(positive_candidates)
        negative = rng.choice(danos)
        out.append(
            {
                "anchor": anchor,
                "positive": positive,
                "negative": negative,
                "weight": WEIGHT_SAME_TYPE_DIFF_FUNC,
                "strategy": "v2_same_type_diff_function",
            }
        )
    return out


def generate_power_level_pairs(
    entities: Dict[str, Dict],
    properties: Dict[str, Dict],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Mesmo elemento, níveis de poder diferentes.
    Anchor: BAIXO; Positive: outra BAIXO/NORMAL; Negative: ALTO.
    """
    out: List[Dict[str, Any]] = []
    by_level: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for name, data in _iter_entities(entities):
        if data.get("type") != "MAGIA":
            continue
        el = _infer_element(name, data, properties)
        if not el:
            continue
        lvl = _infer_power_level(name, data)
        by_level[(el, lvl)].append(name)

    elements = set(el for el, _ in by_level.keys())
    for el in elements:
        lows = by_level.get((el, "BAIXO"), []) + by_level.get((el, "NORMAL"), [])
        highs = by_level.get((el, "ALTO"), [])
        if len(lows) < 2 or not highs:
            continue
        while len(out) < n_target:
            anchor = rng.choice(lows)
            positive = rng.choice([m for m in lows if m != anchor])
            negative = rng.choice(highs)
            out.append(
                {
                    "anchor": anchor,
                    "positive": _make_description(positive, entities, properties),
                    "negative": _make_description(negative, entities, properties),
                    "weight": WEIGHT_POWER_LEVEL,
                    "strategy": "v2_power_level",
                }
            )
            if len(out) >= n_target:
                break
    return out


def generate_synonym_pairs(
    entities: Dict[str, Dict],
    n_target: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Sinônimos/variações: nomes muito parecidos vs elemento oposto.

    Heurística: nomes com alta sobreposição de tokens são "sinônimos".
    Negative: entidade com token compartilhado mas infer_element oposto (fogo vs gelo).
    """
    out: List[Dict[str, Any]] = []
    names = [name for name, _ in _iter_entities(entities)]
    if len(names) < 3:
        return out

    # Pré-cálculo simples de tokens por nome
    tokens_by_name: Dict[str, Set[str]] = {n: set(_tokenize_name(n)) for n in names}

    def _similar(a: str, b: str) -> bool:
        ta = tokens_by_name.get(a) or set()
        tb = tokens_by_name.get(b) or set()
        inter = ta & tb
        return bool(inter) and len(inter) >= 1 and (len(inter) / max(1, min(len(ta), len(tb)))) >= 0.5

    tries = 0
    max_tries = n_target * 20
    while len(out) < n_target and tries < max_tries:
        tries += 1
        a, b = rng.sample(names, 2)
        if not _similar(a, b):
            continue
        da, db = entities.get(a, {}), entities.get(b, {})
        if da.get("type") != "MAGIA" or db.get("type") != "MAGIA":
            continue
        fa = _infer_element(a, da, {})
        fb = _infer_element(b, db, {})
        if not fa or not fb or fa == fb:
            continue
        # Escolhe um como anchor, outro como positive; negative será algo do elemento oposto
        anchor, positive = a, b
        out.append(
            {
                "anchor": anchor,
                "positive": positive,
                "negative": b,  # será substituído depois ou usado como contraste leve
                "weight": WEIGHT_SYNONYM,
                "strategy": "v2_synonym",
            }
        )
    return out


def generate_all_triples_v2(seed: int = 42, min_triples: int = MIN_TRIPLES_V2) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    entities, valid_names = _load_entities()
    if not valid_names:
        return []
    properties = _load_properties()

    target = max(min_triples, MIN_TRIPLES_V2)
    n_ambig = int(target * RATIO_AMBIG_NAME)
    n_same_el = int(target * RATIO_SAME_ELEMENT_DIFF_TYPE)
    n_same_type = int(target * RATIO_SAME_TYPE_DIFF_FUNC)
    n_power = int(target * RATIO_POWER_LEVEL)
    n_syn = max(1, target - (n_ambig + n_same_el + n_same_type + n_power))

    triples: List[Dict[str, Any]] = []
    triples.extend(generate_ambiguity_name_pairs(entities, n_ambig, rng))
    triples.extend(generate_same_element_diff_type_pairs(entities, properties, n_same_el, rng))
    triples.extend(generate_same_type_diff_function_pairs(entities, n_same_type, rng))
    triples.extend(generate_power_level_pairs(entities, properties, n_power, rng))
    triples.extend(generate_synonym_pairs(entities, n_syn, rng))

    # Se por qualquer motivo gerar menos que o mínimo, faz backfill com v1.
    if len(triples) < target:
        from src.ml.training.generate_embedding_dataset import generate_all_triples as legacy_generate

        needed = target - len(triples)
        legacy = legacy_generate(seed=seed, min_triples=needed)
        for t in legacy:
            t.setdefault("strategy", "v1_backfill")
        triples.extend(legacy)

    return triples


def run_v2(
    seed: int = 42,
    out_dir: Path | None = None,
    min_triples: int = MIN_TRIPLES_V2,
) -> Dict[str, Any]:
    """
    Gera triplas v2, divide em train/val e salva arquivos *_v2.jsonl.
    Retorna estatísticas.
    """
    out_dir = out_dir or OUT_DIR
    entities, valid_names = _load_entities()
    if not valid_names:
        return {"error": "Nenhuma entidade em extracted_entities.json", "triples": 0}

    triples = generate_all_triples_v2(seed=seed, min_triples=min_triples)

    if len(triples) < min_triples:
        print(f"[WARN] Triplas v2 geradas ({len(triples)}) abaixo do mínimo ({min_triples}).")

    train, val = split_train_val(triples, train_ratio=TRAIN_RATIO, seed=seed)
    all_path = out_dir / "embedding_triples_v2.jsonl"
    train_path = out_dir / "train_triples_v2.jsonl"
    val_path = out_dir / "val_triples_v2.jsonl"
    save_jsonl(triples, all_path)
    save_jsonl(train, train_path)
    save_jsonl(val, val_path)

    by_strategy = defaultdict(int)
    for t in triples:
        by_strategy[t.get("strategy", "?")] += 1
    stats = {
        "total_triples": len(triples),
        "train": len(train),
        "val": len(val),
        "by_strategy": dict(by_strategy),
        "paths": {
            "embedding_triples_v2": str(all_path),
            "train_triples_v2": str(train_path),
            "val_triples_v2": str(val_path),
        },
    }
    return stats


if __name__ == "__main__":
    # Uso direto para debug: python -m src.ml.training.generate_embedding_dataset_v2
    info = run_v2(seed=42)
    print(json.dumps(info, ensure_ascii=False, indent=2))

