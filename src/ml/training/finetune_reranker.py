"""
Fine-tuning do reranker (CrossEncoder) para 3D&T.

Entrada: data/training/rerank_pairs.jsonl
  {"query": str, "doc_text": str, "label": 0/1, "difficulty": "..."}

Saída:
  models/reranker/3dt_finetuned/
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from sentence_transformers import CrossEncoder, InputExample
from torch.utils.data import DataLoader

from src.config import paths

DATA = paths.data_dir
TRAINING_DIR = DATA / "training"
RERANK_PAIRS = TRAINING_DIR / "rerank_pairs.jsonl"

OUTPUT_DIR = paths.project_root / "models" / "reranker" / "3dt_finetuned"

BASE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

EPOCHS = 3
BATCH_SIZE = 8
LEARNING_RATE = 1e-5
MAX_LENGTH = 512
VAL_RATIO = 0.1


@dataclass
class RerankPair:
    query: str
    doc_text: str
    label: float


def load_pairs(path: Path) -> List[RerankPair]:
    if not path.exists():
        return []
    pairs: List[RerankPair] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            try:
                q = str(row["query"])
                d = str(row["doc_text"])
                lbl = float(row["label"])
            except KeyError:
                continue
            pairs.append(RerankPair(query=q, doc_text=d, label=lbl))
    return pairs


def split_train_val(pairs: List[RerankPair], val_ratio: float = VAL_RATIO) -> Tuple[List[RerankPair], List[RerankPair]]:
    if not pairs:
        return [], []
    n = len(pairs)
    cut = max(1, int(n * (1.0 - val_ratio)))
    return pairs[:cut], pairs[cut:]


def run_finetune_reranker(
    base_model: str = BASE_MODEL,
    output_dir: Path | None = None,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
    learning_rate: float = LEARNING_RATE,
    max_length: int = MAX_LENGTH,
) -> Dict[str, object]:
    pairs = load_pairs(RERANK_PAIRS)
    if not pairs:
        return {"error": f"Nenhum par em {RERANK_PAIRS}. Rode scripts/generate_rerank_dataset.py primeiro."}

    train_pairs, val_pairs = split_train_val(pairs, val_ratio=VAL_RATIO)
    if not train_pairs or not val_pairs:
        return {"error": "Falha ao dividir train/val para reranker.", "total_pairs": len(pairs)}

    # CrossEncoder espera lista de InputExample(texts=[query, doc], label=...).
    train_samples = [
        InputExample(texts=[p.query, p.doc_text], label=float(p.label))
        for p in train_pairs
    ]
    # val_pairs são usados apenas para avaliação posterior (scripts/evaluate_reranker.py).

    train_dataloader = DataLoader(train_samples, shuffle=True, batch_size=batch_size)

    output_dir = output_dir or OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = CrossEncoder(
        base_model,
        num_labels=1,
        max_length=max_length,
    )

    print("[INFO] Fine-tuning reranker")
    print(f"  Base model: {base_model}")
    print(f"  Pairs: {len(pairs)} (train={len(train_pairs)}, val={len(val_pairs)})")
    print(f"  Epochs: {epochs}, LR: {learning_rate}, Batch: {batch_size}")

    model.fit(
        train_dataloader=train_dataloader,
        epochs=epochs,
        optimizer_params={"lr": learning_rate},
        output_path=str(output_dir),
        show_progress_bar=True,
        evaluation_steps=0,
        warmup_steps=0,
        use_amp=False,
    )

    # Garantir que o modelo fine-tuned é salvo de forma carregável pelo CrossEncoder
    try:
        model.save(str(output_dir))
    except Exception as e:
        print(f"[WARN] Falha ao salvar modelo fine-tuned em formato completo: {e}")

    # Salvar um pequeno resumo de treino
    summary = {
        "base_model": base_model,
        "total_pairs": len(pairs),
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "max_length": max_length,
    }
    with (output_dir / "training_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return {
        "output_dir": str(output_dir),
        "summary_path": str(output_dir / "training_summary.json"),
    }


if __name__ == "__main__":
    result = run_finetune_reranker()
    if result.get("error"):
        print(f"[ERRO] {result['error']}")
    else:
        print("[OK] Fine-tuning reranker concluído.")
        print(f"  Modelo salvo em: {result['output_dir']}")
        print(f"  Summary: {result['summary_path']}")

