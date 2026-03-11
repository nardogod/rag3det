"""Gera lista magia | fonte para magias não encontradas."""
from pathlib import Path

# Nome vem do índice do Manual da Magia; descrição não foi encontrada em nenhum PDF
FONTE = "índice - 3dt-alpha-manual-da-magia-biblioteca-elfica.pdf (não encontrada)"

path = Path("data/processed/magias/magias_nao_encontradas.txt")
if not path.exists():
    print("Execute primeiro: python scripts/extrair_magias_agressivo.py")
    exit(1)

linhas = path.read_text(encoding="utf-8").strip().splitlines()
out = Path("data/processed/magias/magias_nao_encontradas_com_fonte.txt")

with out.open("w", encoding="utf-8") as f:
    for line in linhas:
        if ". " in line:
            num, nome = line.strip().split(". ", 1)
            f.write(f"{nome} | {FONTE}\n")

print(f"{len(linhas)} magias não encontradas salvas em {out}")
