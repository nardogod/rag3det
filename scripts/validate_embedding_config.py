"""
TESTE 6: Validação final rápida (config + modelo efetivo + encode).

Uso (na raiz do projeto):
  python scripts/validate_embedding_config.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import embedding_config
from src.embedding.local_embeddings import get_embeddings_model, get_effective_embedding_model_id


def main() -> None:
    print("=== CONFIGURAÇÃO === ")
    print("  Modelo (path):", getattr(embedding_config, "embedding_model", "—"))
    print("  Fallback:", getattr(embedding_config, "embedding_fallback", "—"))

    print("\n=== MODELO EFETIVO === ")
    model = get_embeddings_model()
    model_id = get_effective_embedding_model_id()
    print("  Modelo carregado:", model_id)

    print("\n=== TESTE RÁPIDO === ")
    testes = ["Fênix", "Bola de Fogo", "Ghoul"]
    embeddings = [model.embed_query(t) for t in testes]
    shapes = [len(e) for e in embeddings]
    print("  Dimensões:", shapes)
    if all(s == shapes[0] and s > 0 for s in shapes):
        print("  [OK] Embedding funcionando!")
    else:
        print("  [ERRO] Dimensoes inconsistentes.")
    print("  Concluído.")


if __name__ == "__main__":
    main()
    sys.exit(0)
