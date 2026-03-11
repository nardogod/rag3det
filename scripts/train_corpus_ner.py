"""
Prepara dados e treina modelo NER com corpus 3D&T (entidades extraídas).

Requer: python scripts/prepare_ner_data.py antes.
        pt_core_news_lg (python -m spacy download pt_core_news_lg)

Uso (na raiz do projeto):
  python scripts/train_corpus_ner.py

O script gera dados no formato esperado por ml/ner e indica como usar
o treino via spacy train (config.cfg) ou treino em processo com poucas épocas.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths

TRAINING_JSONL = paths.data_dir / "ner" / "training_data.jsonl"
MODEL_OUT_DIR = paths.project_root / "models" / "ner_3det_corpus"


def main() -> None:
    if not TRAINING_JSONL.exists():
        print("Execute antes: python scripts/prepare_ner_data.py")
        sys.exit(1)
    try:
        import spacy
        from spacy.training import Example
    except ImportError:
        print("spaCy não instalado. pip install spacy")
        sys.exit(1)
    try:
        nlp = spacy.load("pt_core_news_lg")
    except OSError:
        print("Baixe o modelo: python -m spacy download pt_core_news_lg")
        sys.exit(1)
    if "ner" not in nlp.pipe_names:
        nlp.add_pipe("ner", last=True)
    ner = nlp.get_pipe("ner")
    labels = set()
    examples = []
    with TRAINING_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            text = rec.get("text", "")
            entities = [(e["start"], e["end"], e["label"]) for e in rec.get("entities", [])]
            for _, _, label in entities:
                labels.add(label)
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, {"entities": entities})
            examples.append(example)
    for label in labels:
        ner.add_label(label)
    if not examples:
        print("Nenhum exemplo válido em training_data.jsonl.")
        sys.exit(1)
    MODEL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(15):
        losses = {}
        for ex in examples:
            nlp.update([ex], losses=losses)
        if i % 3 == 0:
            print(f"Época {i}, losses: {losses}")
    nlp.to_disk(MODEL_OUT_DIR)
    print(f"Modelo salvo em {MODEL_OUT_DIR}")
    print("Para usar no RAG: NER_MODEL_PATH=models/ner_3det_corpus no .env")


if __name__ == "__main__":
    main()
