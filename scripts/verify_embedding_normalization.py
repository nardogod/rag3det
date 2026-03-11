"""
Verifica se o modelo de embeddings fine-tuned produz vetores L2-normalizados (norma ≈ 1).

Uso (na raiz do projeto):
  python scripts/verify_embedding_normalization.py
  python scripts/verify_embedding_normalization.py --model models/embeddings/3dt_finetuned
  python scripts/verify_embedding_normalization.py --text "Bola de Fogo"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_MODEL = ROOT / "models" / "embeddings" / "3dt_finetuned"
TEST_TEXT = "Fênix"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica normalização L2 do modelo de embeddings.")
    parser.add_argument(
        "--model",
        type=str,
        default=str(DEFAULT_MODEL),
        help="Caminho do modelo (pasta ou nome).",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=TEST_TEXT,
        help="Texto para encode (default: Fênix).",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.1,
        help="Tolerância para considerar normalizado (default: 0.1).",
    )
    args = parser.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        print("Instale: pip install sentence-transformers numpy")
        return 1

    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = ROOT / model_path
    if not model_path.exists():
        print(f"[ERRO] Modelo não encontrado: {model_path}")
        return 1

    model = SentenceTransformer(str(model_path))
    emb = model.encode(args.text)
    if hasattr(emb, "__array__"):
        emb = emb.__array__()
    norm = float(np.linalg.norm(emb))

    print(f"Texto: {args.text!r}")
    print(f"Norma L2: {norm:.4f} (deve ser próximo de 1.0 se normalizado)")

    if abs(norm - 1.0) > args.tolerance:
        print("[X] Nao normalizado! Garanta que o modelo tenha modulo Normalize (finetune com normalize).")
        return 1
    print("[OK] Normalizado corretamente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
