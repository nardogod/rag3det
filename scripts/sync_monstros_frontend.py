"""
Sincroniza monstros_modelo_enriquecido.json com o frontend.
Copia o JSON processado para frontend/src/data/monstros.json.
Injeta "Dragão Bicéfalo" no Manual dos Monstros (alias de Dragões Bicéfalos).

Executar: python scripts/sync_monstros_frontend.py
"""

import json
from pathlib import Path

SRC = Path("data/processed/monstros/monstros_modelo_enriquecido.json")
DST = Path("frontend/src/data/monstros.json")
LIVRO_MANUAL_MONSTROS = "3dt alpha manual dos monstros"


def main() -> None:
    if not SRC.exists():
        print(f"Arquivo não encontrado: {SRC}")
        print("Execute primeiro: python scripts/enriquecer_todos_monstros.py")
        return
    monstros = json.loads(SRC.read_text(encoding="utf-8"))
    # Injeta "Dragão Bicéfalo" no Manual dos Monstros (mesma ficha que Dragões Bicéfalos)
    bicéfalos = next((m for m in monstros if m.get("nome") == "Dragões Bicéfalos"), None)
    if bicéfalos:
        dragao_bicefalo = dict(bicéfalos)
        dragao_bicefalo["nome"] = "Dragão Bicéfalo"
        dragao_bicefalo["livro"] = LIVRO_MANUAL_MONSTROS
        dragao_bicefalo["pagina"] = 101
        monstros.append(dragao_bicefalo)
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(monstros, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {SRC} -> {DST}")


if __name__ == "__main__":
    main()
