"""
Verifica se os índices Chroma (fine-tuned e baseline) existem.

Uso (na raiz do projeto):
  python scripts/check_indices.py

Se faltar algum, rodar: python scripts/reindex_with_finetuned.py --both
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from src.config import paths
    from langchain_chroma import Chroma

    persist_dir = str(paths.chroma_dir)
    coll_fine = "3det_rag"
    coll_base = "3det_rag_baseline"

    def has_collection(name: str) -> bool:
        try:
            vs = Chroma(persist_directory=persist_dir, collection_name=name)
            n = vs._collection.count()
            return n > 0
        except Exception:
            return False

    ok_fine = has_collection(coll_fine)
    ok_base = has_collection(coll_base)

    if ok_fine:
        print("[OK] Indice fine-tuned existe (3det_rag)")
    else:
        print("[X] Indice fine-tuned NAO existe ou esta vazio")

    if ok_base:
        print("[OK] Indice baseline existe (3det_rag_baseline)")
    else:
        print("[X] Indice baseline NAO existe ou esta vazio")

    if not ok_fine or not ok_base:
        print("\nRecriar ambos: python scripts/reindex_with_finetuned.py --both")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
