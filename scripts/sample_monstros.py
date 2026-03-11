"""
Mostra 6 monstros aleatórios no formato de ficha completo e tabelado.
Padrão: docs/FORMATO_FICHA_MONSTRO.md
"""
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.formatar_monstro import formatar_ficha_monstro_tabela

path = Path("data/processed/monstros/monstros_modelo_enriquecido.json")
data = json.loads(path.read_text(encoding="utf-8"))

# Filtrar monstros válidos (excluir fragmentos/artefatos de extração)
def _eh_monstro_valido(m: dict) -> bool:
    nome = (m.get("nome") or "").strip()
    if not nome or len(nome) < 4 or len(nome) > 50:
        return False
    if any(c in nome for c in "0123456789"):
        return False
    # Fragmentos comuns
    if re.search(
        r"^\s*-\s*$|^por sua|^guerreiro anão únic|^por arma|^capitão james|^\s*[a-z]\s*$",
        nome,
        re.I,
    ):
        return False
    if " - " in nome and len(nome) < 15:
        return False
    # Excluir nomes que parecem índice ou instrução
    if re.search(r"\b(ritual|único|única)\b", nome, re.I) and len(nome) < 25:
        return False
    # Nome deve parecer criatura (letras, espaços, hífens)
    if not re.match(r"^[A-ZÀ-ÿ][A-Za-zÀ-ÿ\s\-']+$", nome):
        return False
    return True

monstros = [
    m for m in data
    if isinstance(m, dict) and m.get("caracteristicas") and _eh_monstro_valido(m)
]
sample = random.sample(monstros, min(6, len(monstros)))

for m in sample:
    print(formatar_ficha_monstro_tabela(m, incluir_descricao=True))
    print("\n" + "=" * 60 + "\n")
