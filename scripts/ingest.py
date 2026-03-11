"""
Script para (re)processar PDFs e gerar chunks, sem reconstruir o índice vetorial.

Uso (a partir da raiz do projeto):
  python scripts/ingest.py --path data/raw/

- `--path` (opcional) permite apontar para outro diretório de PDFs.
- Apenas roda a pipeline de ingestão e mostra quantos chunks foram gerados.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.pipeline import run_ingestion  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reprocessa PDFs em um diretório e gera chunks prontos para indexação."
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default=None,
        help="Diretório com os PDFs de origem (ex.: data/raw/). "
        "Se omitido, usa o diretório padrão configurado em SOURCE_PDF_DIR ou data/raw/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    source_dir = Path(args.path).resolve() if args.path is not None else None
    if source_dir is not None and not source_dir.exists():
        print(f"Diretório informado não existe: {source_dir}")
        sys.exit(1)

    print("Iniciando ingestão de PDFs...")
    if source_dir is not None:
        print(f"- Diretório de origem: {source_dir}")

    chunks = run_ingestion(source_dir=source_dir)
    if not chunks:
        print("Nenhum chunk foi gerado. Verifique se há PDFs legíveis no diretório informado.")
        sys.exit(1)

    print(f"Ingestão concluída. Total de chunks gerados: {len(chunks)}")


if __name__ == "__main__":
    main()

