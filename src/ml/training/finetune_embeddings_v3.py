"""
Fine-tuning v3 de embeddings para domínio 3D&T com dataset v2 (hard negatives) opcional.

- Dataset v1: train_triples.jsonl / val_triples.jsonl (gerador original).
- Dataset v2: train_triples_v2.jsonl / val_triples_v2.jsonl (hard negatives).
- Opcionalmente adiciona triplas de falhas do A/B test (ab_failures_triples.jsonl).
- Treino com MultipleNegativesRankingLoss (pares anchor/positive, in-batch negatives),
  avaliação com TripletEvaluator e early stopping.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.config import paths
from src.ml.training.finetune_embeddings import load_triples

DATA = paths.data_dir
PROJECT_ROOT = paths.project_root
TRAINING_DIR = DATA / "training"

TRAIN_V1 = TRAINING_DIR / "train_triples.jsonl"
VAL_V1 = TRAINING_DIR / "val_triples.jsonl"
TRAIN_V2 = TRAINING_DIR / "train_triples_v2.jsonl"
VAL_V2 = TRAINING_DIR / "val_triples_v2.jsonl"
AB_FAILURES = TRAINING_DIR / "ab_failures_triples.jsonl"

OUTPUT_V2 = PROJECT_ROOT / "models" / "embeddings" / "3dt_finetuned_v2"
OUTPUT_V3 = PROJECT_ROOT / "models" / "embeddings" / "3dt_finetuned_v3"

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FALLBACK_MODEL = "sentence-transformers/distiluse-base-multilingual-cased-v1"

BATCH_SIZE = 8
EPOCHS = 5
WARMUP_STEPS = 300
LEARNING_RATE = 3e-5
EARLY_STOPPING_PATIENCE = 2
MNLOSS_SCALE = 20.0  # temperatura / escala da MultipleNegativesRankingLoss


def _extract_score(eval_result: Any) -> float:
    if isinstance(eval_result, (int, float)):
        return float(eval_result)
    if isinstance(eval_result, dict):
        for k in ("val_triplet_TripletEvaluator_acc_cos_sim", "val_triplet_acc_cos_sim", "val_triplet_acc"):
            if k in eval_result:
                return float(eval_result[k])
        if eval_result:
            return float(next(iter(eval_result.values())))
    return 0.0


def _select_paths(dataset: str) -> Tuple[Path, Path, Path]:
    if dataset == "v2":
        return TRAIN_V2, VAL_V2, OUTPUT_V3
    # default: v1
    return TRAIN_V1, VAL_V1, OUTPUT_V2


def run_finetune_v3(
    dataset: str = "v2",
    epochs: int = EPOCHS,
    lr: float = LEARNING_RATE,
    batch_size: int = BATCH_SIZE,
    warmup_steps: int = WARMUP_STEPS,
    use_ab_failures: bool = True,
    model_name: str | None = None,
) -> Dict[str, Any]:
    """
    Treina modelo de embeddings (v3) com MultipleNegativesRankingLoss e early stopping.
    """
    try:
        from sentence_transformers import SentenceTransformer, losses, InputExample
        from sentence_transformers.evaluation import TripletEvaluator
        from sentence_transformers.models import Normalize
        from torch.utils.data import DataLoader
    except ImportError as e:
        raise ImportError(
            "Fine-tuning requer: pip install sentence-transformers datasets torch"
        ) from e

    train_path, val_path, output_path = _select_paths(dataset)

    train_triples = load_triples(train_path)
    val_triples = load_triples(val_path)
    if not train_triples:
        return {"error": f"Nenhuma tripla em {train_path}. Rode generate_embedding_dataset_v2.py primeiro."}

    if use_ab_failures and AB_FAILURES.exists():
        ab_triples = load_triples(AB_FAILURES)
        train_triples.extend(ab_triples)

    # Pares (anchor, positive) para MultipleNegativesRankingLoss
    pair_examples = [
        InputExample(texts=[t["anchor"], t["positive"]])
        for t in train_triples
    ]
    train_dataloader = DataLoader(pair_examples, shuffle=True, batch_size=batch_size)

    # Triplas para avaliação
    val_anchors = [t["anchor"] for t in val_triples]
    val_positives = [t["positive"] for t in val_triples]
    val_negatives = [t["negative"] for t in val_triples]
    evaluator = TripletEvaluator(
        anchors=val_anchors,
        positives=val_positives,
        negatives=val_negatives,
        name="val_triplet",
        batch_size=batch_size,
    )

    # Carregar modelo base
    base_name = model_name or DEFAULT_MODEL
    model = None
    for attempt, name in enumerate([base_name, FALLBACK_MODEL]):
        try:
            model = SentenceTransformer(name)
            break
        except Exception as e:
            if attempt == 0:
                print(f"[WARN] Falha ao carregar {name}: {e}. Tentando fallback {FALLBACK_MODEL}.")
                continue
            raise

    # Garantir módulo Normalize no final
    if not (len(model) > 0 and isinstance(model[-1], Normalize)):
        model.append(Normalize())
        print("[INFO] Módulo Normalize adicionado ao modelo (embeddings com norma 1).")

    train_loss = losses.MultipleNegativesRankingLoss(model=model, scale=MNLOSS_SCALE)

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    log_entries: List[Dict[str, Any]] = []
    best_score: float = -1.0
    no_improve_count = 0

    steps_per_epoch = max(1, len(pair_examples) // batch_size)
    total_steps = 0

    for epoch_idx in range(epochs):
        current_warmup = warmup_steps if epoch_idx == 0 else 0
        print(f"[INFO] Epoch {epoch_idx + 1}/{epochs} (warmup_steps={current_warmup})")
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=1,
            warmup_steps=current_warmup,
            optimizer_params={"lr": lr},
            evaluator=None,
            evaluation_steps=0,
            output_path=None,
            save_best_model=False,
            show_progress_bar=True,
        )
        total_steps += steps_per_epoch

        eval_result = evaluator(model)
        score = _extract_score(eval_result)
        log_entries.append({"epoch": epoch_idx + 1, "step": total_steps, "score": score})
        print(f"[INFO] Val score (epoch {epoch_idx + 1}): {score:.4f}")

        if score > best_score:
            best_score = score
            no_improve_count = 0
            model.save(str(output_path))
            print(f"[INFO] Novo melhor score {best_score:.4f}, modelo salvo em {output_path}")
        else:
            no_improve_count += 1
            print(f"[INFO] Sem melhora ({no_improve_count}/{EARLY_STOPPING_PATIENCE}).")
            if no_improve_count >= EARLY_STOPPING_PATIENCE:
                print(f"[INFO] Early stopping: sem melhora em {EARLY_STOPPING_PATIENCE} avaliações consecutivas.")
                break

    # Avaliação final com o melhor modelo salvo
    from sentence_transformers import SentenceTransformer as _ST

    best_model = _ST(str(output_path))
    final_eval = evaluator(best_model)
    final_score = _extract_score(final_eval)

    training_log = {
        "dataset_version": dataset,
        "model_name": base_name,
        "train_samples": len(train_triples),
        "val_samples": len(val_triples),
        "batch_size": batch_size,
        "epochs_requested": epochs,
        "epochs_run": len(log_entries),
        "learning_rate": lr,
        "warmup_steps": warmup_steps,
        "use_ab_failures": use_ab_failures,
        "best_score": final_score,
        "history": log_entries,
    }
    with (output_path / "training_config_v3.json").open("w", encoding="utf-8") as f:
        json.dump(training_log, f, ensure_ascii=False, indent=2)

    return {
        "output_path": str(output_path),
        "best_score": final_score,
        "history": log_entries,
        "training_log_path": str(output_path / "training_config_v3.json"),
    }

