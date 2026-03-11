"""
Testa extração NER em uma frase (modelo treinado no corpus 3D&T).

Uso (na raiz do projeto):
  python scripts/test_ner.py "Invocação da Fênix"
  python scripts/test_ner.py "O Insano Megalomaníaco é um devorador de mentes"
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import paths

MODEL_DIR = paths.project_root / "models" / "ner_3det_corpus"


def main() -> None:
    text = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "Invocação da Fênix custa 10 PM"
    if not MODEL_DIR.exists():
        print(f"Modelo não encontrado em {MODEL_DIR}. Execute: python scripts/train_corpus_ner.py")
        sys.exit(1)
    try:
        import spacy
        nlp = spacy.load(MODEL_DIR)
    except Exception as e:
        print("Erro ao carregar modelo:", e)
        sys.exit(1)
    doc = nlp(text)
    print(f"Texto: {text}")
    print("Entidades:")
    for ent in doc.ents:
        print(f"  {ent.text!r} -> {ent.label_}")


if __name__ == "__main__":
    main()
