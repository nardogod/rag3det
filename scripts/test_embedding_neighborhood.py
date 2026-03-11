"""
TESTE 3: Vizinhança no espaço vetorial (fine-tuned vs baseline).

Uso (na raiz do projeto):
  python scripts/test_embedding_neighborhood.py

Esperado: com fine-tuned, Fênix mais próximo de Bola de Fogo (razão dist(Fênix,Ghoul)/dist(Fênix,Bola) > 1.5).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from src.embedding.local_embeddings import get_embeddings_model, get_baseline_embeddings_model


def _embed(model, text: str) -> np.ndarray:
    """LangChain Embeddings usa embed_query; retorna vetor numpy."""
    vec = model.embed_query(text)
    return np.array(vec, dtype=np.float32)


def main() -> None:
    print("Carregando modelos...")
    fine = get_embeddings_model()
    base = get_baseline_embeddings_model()

    queries = ["Fênix", "Bola de Fogo", "Muralha de Fogo", "Ghoul", "Cemitério Vivo"]

    print("\n=== FINE-TUNED === ")
    for q in queries:
        emb = _embed(fine, q)
        print(f"  {q}: shape {emb.shape}")

    print("\n=== DISTÂNCIAS FINE-TUNED === ")
    f_fenix = _embed(fine, "Fênix")
    f_bola = _embed(fine, "Bola de Fogo")
    f_ghoul = _embed(fine, "Ghoul")

    dist_fogo = float(np.linalg.norm(f_fenix - f_bola))
    dist_ghoul = float(np.linalg.norm(f_fenix - f_ghoul))
    print(f"  Fenix vs Bola de Fogo: {dist_fogo:.3f} (menor = mais similar)")
    print(f"  Fenix vs Ghoul: {dist_ghoul:.3f}")
    ratio = dist_ghoul / dist_fogo if dist_fogo > 0 else 0
    print(f"  Razão (Ghoul/Fogo): {ratio:.2f}x (esperado > 1.5 para fine-tuned)")

    print("\n=== DISTÂNCIAS BASELINE === ")
    b_fenix = _embed(base, "Fênix")
    b_bola = _embed(base, "Bola de Fogo")
    b_ghoul = _embed(base, "Ghoul")

    dist_fogo_b = float(np.linalg.norm(b_fenix - b_bola))
    dist_ghoul_b = float(np.linalg.norm(b_fenix - b_ghoul))
    print(f"  Fenix vs Bola de Fogo: {dist_fogo_b:.3f}")
    print(f"  Fenix vs Ghoul: {dist_ghoul_b:.3f}")
    ratio_b = dist_ghoul_b / dist_fogo_b if dist_fogo_b > 0 else 0
    print(f"  Razão (Ghoul/Fogo): {ratio_b:.2f}x")

    print("\n=== RESUMO === ")
    if ratio > 1.5 and ratio > ratio_b:
        print("  [OK] Fine-tuned: Fenix mais proximo de Bola de Fogo (razao > 1.5)")
    else:
        print("  [AVISO] Fine-tuned: razao = {:.2f} (meta > 1.5)".format(ratio))
    print("  Concluído.")


if __name__ == "__main__":
    main()
    sys.exit(0)
