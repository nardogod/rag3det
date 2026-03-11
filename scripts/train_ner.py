"""
Script para treinar (ou retreinar) o modelo de NER em cima dos dados fracos.

Fluxo sugerido:
- Gerar dados fracos: `python -m ml.ner.weak_annotate` (gera `data/ner/weak_annotations.jsonl`).
- Ajustar/validar o arquivo de config em `ml/ner/config.cfg`.
- Rodar este script:
    python scripts/train_ner.py

O spaCy vai treinar um modelo e salvar em `models/ner_3det` (por padrão),
com métricas de precision/recall/F1 por entidade no log.
"""
from __future__ import annotations

import sys
from pathlib import Path

import spacy
from spacy.cli.train import train


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "ml" / "ner" / "config.cfg"
OUTPUT_PATH = ROOT / "models" / "ner_3det"


def main() -> None:
    if not CONFIG_PATH.exists():
        print(f"Config de treino não encontrada: {CONFIG_PATH}")
        sys.exit(1)

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    print(f"Treinando NER com config: {CONFIG_PATH}")
    # `overrides` precisa ser um dict (spaCy >=3.7), não `None`
    train(
        config_path=str(CONFIG_PATH),
        output_path=str(OUTPUT_PATH),
        overrides={},
    )
    print(f"Treino concluído. Modelo salvo em: {OUTPUT_PATH}")
    print("Para usar no RAG, defina NER_MODEL_PATH no .env, por exemplo:")
    print(f'  NER_MODEL_PATH="{OUTPUT_PATH.as_posix()}"')


if __name__ == "__main__":
    main()

