"""Gera amostra de 20 itens aleatórios com estrutura completa (livro, categoria, etc.)."""
import json
import random
from pathlib import Path

DATA = Path("data/processed/itens_magicos/itens_magicos_categorizados.json")
OUT = Path("data/processed/itens_magicos/amostra_20_itens.txt")

def _eh_item_valido(item: dict) -> bool:
    """Filtra fragmentos e itens mal extraídos."""
    nome = (item.get("nome") or "").strip()
    if len(nome) < 5 or nome.endswith("-"):
        return False
    if nome[0].islower() and len(nome) > 4:
        return False
    # Fragmentos comuns (começam com artigo/verbo)
    if nome.lower().startswith(("o ", "a ", "um ", "uma ", "este ", "esta ", "pergaminho contém", "anel oferece", "anel torna", "anel prateado", "anel com essa", "pergaminho consigo")):
        return False
    return True


def main():
    itens = json.loads(DATA.read_text(encoding="utf-8"))
    validos = [i for i in itens if _eh_item_valido(i)]
    random.seed(42)
    amostra = random.sample(validos, min(20, len(validos)))

    linhas = [
        "=" * 70,
        "AMOSTRA DE 20 ITENS MÁGICOS (aleatórios) - Estrutura completa",
        "Campos: Nome, Livro, Categoria, Tipo, Bônus, Preço, Efeito",
        "=" * 70,
    ]

    for i, item in enumerate(amostra, 1):
        efeito = (item.get("efeito") or "-").strip()
        if len(efeito) > 350:
            efeito = efeito[:350] + "..."
        linhas.extend([
            "",
            f"--- Item {i} ---",
            f"Nome: {item.get('nome', '')}",
            f"Livro: {item.get('livro', '')}",
            f"Categoria: {item.get('categoria_label', item.get('categoria', ''))}",
            f"Tipo: {item.get('tipo', '-')}",
            f"Bônus: {item.get('bonus', '-')}",
            f"Preço: {item.get('custo', '-')}",
            f"Efeito: {efeito}",
        ])

    texto = "\n".join(linhas)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(texto, encoding="utf-8")
    print(f"[OK] Amostra de {len(amostra)} itens salva em {OUT}")

if __name__ == "__main__":
    main()
