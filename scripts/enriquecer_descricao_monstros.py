"""
Enriquecimento de descrição de monstros (piloto: 5 do Livro de Arton).
Adiciona: comportamento, altura_tamanho, peso, habitat, comportamento_dia_noite,
          comportamento_combate, habilidades_extra.

Executar: python scripts/enriquecer_descricao_monstros.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.enriquecer_descricao_monstro import main

if __name__ == "__main__":
    main()
