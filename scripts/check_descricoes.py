"""Gera lista magia | fonte."""
import json
from pathlib import Path

path = Path("data/processed/magias/magias_extraidas_agressivo.json")
with path.open("r", encoding="utf-8") as f:
    magias = json.load(f)

out = Path("data/processed/magias/magias_com_fonte.txt")
with out.open("w", encoding="utf-8") as f:
    for m in magias:
        f.write(f"{m['nome']} | {m.get('livro', '?')}\n")

print(f"{len(magias)} magias salvas em {out}")
