from __future__ import annotations

"""
Gera dados anotados automaticamente (weak supervision) para treinar NER.

Fluxo sugerido:
- Usa os chunks já produzidos por `run_ingestion()`.
- Aplica padrões em `patterns.py` para marcar atributos, raças, classes, magias.
- Exporta em formato JSONL compatível com spaCy v3:
  {"text": "...", "entities": [[start, end, "LABEL"], ...]}
"""

import json
from pathlib import Path
from typing import Iterable, List, Tuple

from langchain_core.documents import Document

from ml.ner.patterns import EntitySpan, weak_ner_patterns
from src.ingestion.pipeline import run_ingestion
from src.types import DocumentList


def annotate_documents(documents: Iterable[Document]) -> List[dict]:
    """
    Cria exemplos fracos de NER a partir de uma lista de Documents.

    Cada exemplo é um dicionário:
    {"text": doc.page_content, "entities": [[start, end, "LABEL"], ...]}
    """
    examples: List[dict] = []

    for doc in documents:
        text = doc.page_content
        spans: List[EntitySpan] = weak_ner_patterns(text)
        if not spans:
            continue

        entities: List[Tuple[int, int, str]] = [
            [start, end, label]  # type: ignore[list-item]
            for start, end, label in spans
        ]

        examples.append(
            {
                "text": text,
                "entities": entities,
            }
        )

    return examples


def export_to_jsonl(examples: List[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")


def main() -> None:
    """
    CLI simples:
    - Roda ingestão.
    - Gera anotações fracas.
    - Salva em `data/ner/weak_annotations.jsonl`.
    """
    print("Rodando ingestão para gerar dados de NER fraco...")
    chunks: DocumentList = run_ingestion()
    print(f"Chunks disponíveis: {len(chunks)}")

    print("Gerando anotações fracas (weak supervision)...")
    examples = annotate_documents(chunks)
    print(f"Exemplos anotados: {len(examples)}")

    out_path = Path("data") / "ner" / "weak_annotations.jsonl"
    export_to_jsonl(examples, out_path)
    print(f"Exportado para {out_path}")


if __name__ == "__main__":
    main()

