"""
Diagnóstico do índice extraído - verifica sequência, formato e problemas.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def analisar_indice(caminho_indice: str | Path = "data/processed/indice_magias_3dt.txt") -> None:
    path = Path(caminho_indice)
    if not path.exists():
        print(f"Arquivo nao encontrado: {path}")
        return

    with path.open("r", encoding="utf-8") as f:
        linhas = [l.rstrip() for l in f.readlines() if l.strip()]

    print(f"Total de entradas: {len(linhas)}")
    print("\n--- Primeiras 20 ---")
    for i, linha in enumerate(linhas[:20], 1):
        print(f"  {i:2d}. {linha}")

    print("\n--- Ultimas 20 ---")
    for i, linha in enumerate(linhas[-20:], len(linhas) - 19):
        print(f"  {len(linhas)-20+i:3d}. {linha}")

    # Detectar problemas
    problemas = []
    numeros = []
    for i, linha in enumerate(linhas):
        stripped = linha.strip()
        # Formato esperado: "001. Nome da Magia" ou "1. Nome"
        match = re.match(r"^(\d{1,3})\.\s*(.+)$", stripped)
        if match:
            num = int(match.group(1))
            nome = match.group(2).strip()
            numeros.append((i + 1, num, nome))
            if not nome:
                problemas.append(f"Linha {i+1}: numero sem nome - '{linha[:50]}'")
        else:
            problemas.append(f"Linha {i+1}: formato invalido - '{stripped[:60]}'")

    # Verificar sequencia
    nums_ordem = [n for _, n, _ in numeros]
    saltos = []
    for j in range(1, len(nums_ordem)):
        if nums_ordem[j] != nums_ordem[j - 1] + 1:
            saltos.append((j + 1, nums_ordem[j - 1], nums_ordem[j]))

    print(f"\n--- Sequencia ---")
    print(f"  Numeros: {nums_ordem[0]} a {nums_ordem[-1]}")
    print(f"  Sequenciais: {'Sim' if not saltos else 'Nao'}")
    if saltos:
        print(f"  Saltos detectados: {len(saltos)}")
        for idx, (ant, prox) in [(s[0], (s[1], s[2])) for s in saltos[:15]]:
            print(f"    Linha ~{idx}: {ant} -> {prox}")

    print(f"\n--- Problemas ---")
    print(f"  Total: {len(problemas)}")
    for p in problemas[:15]:
        print(f"  {p}")


if __name__ == "__main__":
    analisar_indice()
