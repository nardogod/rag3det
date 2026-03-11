"""
Prepara dataset de treinamento NER a partir das entidades extraídas.

- Lê data/entities/extracted_entities.json
- Para cada entidade, encontra spans nos contexts e gera anotações no formato spaCy JSONL
- Saída: data/ner/training_data.jsonl (para uso com train_corpus_ner ou ml/ner)

Uso (na raiz do projeto):
  python scripts/prepare_ner_data.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths

ENTITIES_JSON = paths.data_dir / "entities" / "extracted_entities.json"
OUTPUT_JSONL = paths.data_dir / "ner" / "training_data.jsonl"


def main() -> None:
    if not ENTITIES_JSON.exists():
        print("Execute antes: python scripts/extract_entities.py")
        sys.exit(1)
    with ENTITIES_JSON.open("r", encoding="utf-8") as f:
        entities = json.load(f)
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with OUTPUT_JSONL.open("w", encoding="utf-8") as out:
        for name, data in entities.items():
            etype = data.get("type", "ENTIDADE")
            for ctx in data.get("contexts") or []:
                if name not in ctx:
                    continue
                start = ctx.find(name)
                if start == -1:
                    continue
                end = start + len(name)
                record = {
                    "text": ctx[:512],
                    "entities": [{"start": start, "end": end, "label": etype}],
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
                if count >= 500:
                    break
            if count >= 500:
                break
    print(f"Exemplos de treinamento: {count}. Salvos em {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()
