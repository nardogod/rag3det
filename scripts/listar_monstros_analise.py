"""Lista monstros extraídos para análise."""
import json
from pathlib import Path

data = json.loads(Path("data/processed/monstros/monstros_extraidos.json").read_text(encoding="utf-8"))

# Por livro
livros = {}
for m in data:
    l = m.get("livro") or "sem livro"
    livros[l] = livros.get(l, 0) + 1

print("=== RESUMO POR LIVRO ===")
for l, q in sorted(livros.items(), key=lambda x: -x[1]):
    print(f"  {q:4} | {l[:70]}")

print()
print("=== TOTAL:", len(data), "monstros ===")
print()

# Monstros Arton (Daemon)
daemon = [m for m in data if "daemon" in (m.get("livro") or "").lower()]
print("=== MONSTROS DO LIVRO ARTON (Daemon) -", len(daemon), "===")
for m in daemon:
    c = m.get("caracteristicas") or {}
    extra = " [ENR]" if "comportamento" in m else ""
    f, h, r, a, pdf = c.get("F"), c.get("H"), c.get("R"), c.get("A"), c.get("PdF")
    print(f"  {m['nome']}{extra} | F{f} H{h} R{r} A{a} PdF{pdf}")

# Outros livros (amostra)
outros = [m for m in data if "daemon" not in (m.get("livro") or "").lower()]
print()
print("=== OUTROS LIVROS - amostra 50 ===")
for m in outros[:50]:
    c = m.get("caracteristicas") or {}
    livro = (m.get("livro") or "")[:40]
    print(f"  {m['nome']} | F{c.get('F')} H{c.get('H')} R{c.get('R')} A{c.get('A')} | {livro}")
