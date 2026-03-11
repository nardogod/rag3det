"""Extrai índice de Vantagens/Desvantagens do Manual da Magia."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.extrair_indice_vantagens_magia import (
    extrair_indice_vantagens_magia,
    salvar_indice,
)

if __name__ == "__main__":
    try:
        itens = extrair_indice_vantagens_magia()
        if itens:
            salvar_indice(itens)
        else:
            print("Nenhuma vantagem/desvantagem encontrada.")
    except (ImportError, FileNotFoundError) as e:
        print(f"Erro: {e}")
