"""Analisa preços e qualidade dos itens mágicos extraídos."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "processed" / "itens_magicos"
with open(DATA / "itens_magicos_extraidos_agressivo.json", encoding="utf-8") as f:
    itens = json.load(f)

com_custo = sum(1 for i in itens if i.get("custo"))
sem_custo = sum(1 for i in itens if not i.get("custo"))
print("=== PREÇOS ===")
print(f"Com custo: {com_custo} ({100*com_custo/len(itens):.1f}%)")
print(f"Sem custo (null): {sem_custo} ({100*sem_custo/len(itens):.1f}%)")

formatos = {}
for i in itens:
    c = i.get("custo")
    if c:
        if "PE" in c.upper(): fmt = "PEs"
        elif "PM" in c.upper(): fmt = "PMs"
        elif " a " in c or "-" in c: fmt = "variável"
        else: fmt = "outro"
        formatos[fmt] = formatos.get(fmt, 0) + 1
print("Formatos de custo:", formatos)

# Fragmentos (nomes suspeitos: quebrados, começam com minúscula após espaço)
fragmentos = [
    i for i in itens
    if i.get("nome", "").endswith("-")
    or (len(i.get("nome", "")) > 3 and i.get("nome", "")[0].islower())
]
print(f"\nPossíveis fragmentos (nome suspeito): {len(fragmentos)}")
for x in fragmentos[:8]:
    print(f'  - "{x["nome"][:60]}"')

# Efeito truncado ou vazio
sem_efeito = sum(1 for i in itens if not i.get("efeito") or len(i.get("efeito", "")) < 30)
print(f"\nEfeito vazio ou muito curto (<30 chars): {sem_efeito}")

# Amostra de itens BOM
bons = [i for i in itens if i.get("custo") and len(i.get("nome", "")) > 15 and i.get("efeito") and len(i.get("efeito", "")) > 80]
print(f"\nItens com nome ok + custo + efeito razoável: {len(bons)}")
for x in bons[:3]:
    print(f"\n--- {x['nome']} ---")
    print(f"  Custo: {x['custo']}")
    print(f"  Efeito (início): {x['efeito'][:120]}...")
