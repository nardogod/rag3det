"""
Fine-tuning de embeddings para domínio 3D&T.

Modelo base: paraphrase-multilingual-MiniLM-L12-v2 (ou distiluse-base-multilingual-cased-v1 se OOM).
- Triplas (anchor, positive, negative) para avaliação; treino com MultipleNegativesRankingLoss em pares (anchor, positive).
- Módulo Normalize para embeddings L2 (norma 1).
- Treino: até 5 epochs com early stopping; saída em models/embeddings/3dt_finetuned_v2/.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.config import paths

DATA = paths.data_dir
PROJECT_ROOT = paths.project_root
TRAINING_DIR = DATA / "training"
TRAIN_TRIPLES = TRAINING_DIR / "train_triples.jsonl"
VAL_TRIPLES = TRAINING_DIR / "val_triples.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "models" / "embeddings" / "3dt_finetuned"
OUTPUT_DIR_V2 = PROJECT_ROOT / "models" / "embeddings" / "3dt_finetuned_v2"
TRAINING_LOG = OUTPUT_DIR / "training_log.json"

# Modelo base (trocar para distiluse-base-multilingual-cased-v1 se OOM)
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
FALLBACK_MODEL = "sentence-transformers/distiluse-base-multilingual-cased-v1"

# Hiperparâmetros (treino completo com normalização L2)
BATCH_SIZE = 8  # menor batch => mais updates / menos memória
EPOCHS = 5
WARMUP_STEPS = 200
LEARNING_RATE = 3e-5
EVALUATION_STEPS = 0  # usamos avaliação explícita ao final de cada epoch
EARLY_STOPPING_PATIENCE = 2  # parar se 2 avaliações consecutivas sem melhora

# Temperatura (escala) da MultipleNegativesRankingLoss (equivalente a "temperature")
MNLOSS_SCALE = 20.0


def load_triples(path: Path) -> List[Dict[str, Any]]:
    """Carrega triplas de um JSONL (anchor, positive, negative, weight)."""
    if not path.exists():
        return []
    triples = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            triples.append(json.loads(line))
    return triples


def run_finetune(
    model_name: str | None = None,
    train_path: Path | None = None,
    val_path: Path | None = None,
    output_path: Path | None = None,
    batch_size: int = BATCH_SIZE,
    epochs: int = EPOCHS,
    warmup_steps: int = WARMUP_STEPS,
    learning_rate: float = LEARNING_RATE,
    evaluation_steps: int = EVALUATION_STEPS,
    early_stopping_patience: int = EARLY_STOPPING_PATIENCE,
    use_fallback_model_on_oom: bool = True,
) -> Dict[str, Any]:
    """
    Carrega triplas, treina com MultipleNegativesRankingLoss (pares anchor/positive, 5 epochs, early stopping),
    avalia com TripletEvaluator e salva o melhor modelo em models/embeddings/3dt_finetuned_v2/.
    Retorna dicionário com best_score, history e caminhos.
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

    train_path = train_path or TRAIN_TRIPLES
    val_path = val_path or VAL_TRIPLES
    output_path = output_path or OUTPUT_DIR_V2
    model_name = model_name or DEFAULT_MODEL

    train_triples = load_triples(train_path)
    val_triples = load_triples(val_path)
    if not train_triples:
        return {"error": f"Nenhuma tripla em {train_path}. Rode scripts/generate_embedding_dataset.py primeiro."}
    # Para treino com MultipleNegativesRankingLoss usamos apenas pares (anchor, positive);
    # negatives vêm in-batch.
    pair_examples = [
        InputExample(texts=[t["anchor"], t["positive"]])
        for t in train_triples
    ]
    train_dataloader = DataLoader(pair_examples, shuffle=True, batch_size=batch_size)

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

    model = None
    for attempt, name in enumerate([model_name, FALLBACK_MODEL] if use_fallback_model_on_oom else [model_name]):
        try:
            model = SentenceTransformer(name)
            break
        except Exception as e:
            if use_fallback_model_on_oom and attempt == 0:
                print(f"[WARN] Falha ao carregar {name}: {e}. Tentando {FALLBACK_MODEL}.")
                continue
            raise

    # Garantir embeddings L2-normalizados (norma ≈ 1) para distâncias consistentes
    if not (len(model) > 0 and isinstance(model[-1], Normalize)):
        model.append(Normalize())
        print("[INFO] Módulo Normalize adicionado ao modelo (embeddings com norma 1).")

    # Loss principal: MultipleNegativesRankingLoss com escala (temperatura) ajustável.
    train_loss = losses.MultipleNegativesRankingLoss(model=model, scale=MNLOSS_SCALE)

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    log_entries: List[Dict[str, Any]] = []
    best_score: float = -1.0
    no_improve_count = 0

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

    # Loop manual por epoch para permitir early stopping com TripletEvaluator.
    steps_per_epoch = max(1, len(pair_examples) // batch_size)
    total_steps = 0

    for epoch_idx in range(epochs):
        current_warmup = warmup_steps if epoch_idx == 0 else 0
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=1,
            warmup_steps=current_warmup,
            optimizer_params={"lr": learning_rate},
            evaluator=None,
            evaluation_steps=0,
            output_path=None,
            save_best_model=False,
            show_progress_bar=True,
        )
        total_steps += steps_per_epoch

        # Avaliação ao final de cada epoch
        eval_result = evaluator(model)
        score = _extract_score(eval_result)
        log_entries.append({"epoch": epoch_idx + 1, "step": total_steps, "score": score})

        if score > best_score:
            best_score = score
            no_improve_count = 0
            model.save(str(output_path))
        else:
            no_improve_count += 1
            if no_improve_count >= early_stopping_patience:
                print(f"[INFO] Early stopping: sem melhora em {early_stopping_patience} avaliações consecutivas.")
                break

    # Carregar o melhor modelo salvo para avaliação final
    from sentence_transformers import SentenceTransformer as _ST

    best_model = _ST(str(output_path))
    final_eval = evaluator(best_model)
    final_score = _extract_score(final_eval)

    training_log = {
        "model_name": model_name,
        "train_samples": len(train_triples),
        "val_samples": len(val_triples),
        "batch_size": batch_size,
        "epochs_requested": epochs,
        "epochs_run": len(log_entries),
        "best_score": final_score,
        "history": log_entries,
    }
    with (output_path / "training_log.json").open("w", encoding="utf-8") as f:
        json.dump(training_log, f, ensure_ascii=False, indent=2)

    return {
        "output_path": str(output_path),
        "best_score": final_score,
        "history": log_entries,
        "training_log_path": str(output_path / "training_log.json"),
    }
