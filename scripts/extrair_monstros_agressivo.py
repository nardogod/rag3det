"""
Extrator de monstros/criaturas dos PDFs Manual dos Monstros e Bestiário.
Busca padrões F/H/R/A/PdF e extrai blocos de criaturas.
Executar: python scripts/extrair_monstros_agressivo.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import paths

# Padrão para stat block: Nome: F0-5, H0-5, R0-5, A0-5, PdF0-5 [, habilidades...]
STAT_PATTERN = re.compile(
    r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*:\s*"
    r"F\s*(\d+(?:\s*[-–]\s*\d+)?(?:\([^)]+\))?)\s*[,;]?\s*"
    r"H\s*(\d+(?:\s*[-–]\s*\d+)?)\s*[,;]?\s*"
    r"R\s*(\d+(?:\s*[-–]\s*\d+)?)\s*[,;]?\s*"
    r"A\s*(\d+(?:\s*[-–]\s*\d+)?)\s*[,;]?\s*"
    r"PdF\s*(\d+(?:\s*[-–]\s*\d+)?(?:\([^)]+\))?)"
    r"(?:[,;]\s*([^.\n]+))?",  # grupo 7: habilidades após PdF (ex: "Infravisão, Invulnerabilidade (Químico)")
    re.IGNORECASE,
)


def _encontrar_pdfs_monstros() -> list[Path]:
    """Localiza PDFs para extração de monstros. Processa todos os livros em source_pdf_dir."""
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        return []
    todos = sorted(pdf_dir.rglob("*.pdf"))
    return todos


def _limpar_descricao(txt: str, max_chars: int = 12000) -> str:
    """
    Normaliza o texto da descrição. Limite alto para preservar personalidade,
    habilidades, ataques e regras especiais que definem a dificuldade do combate.
    """
    if not txt or not txt.strip():
        return ""
    t = re.sub(r"\s+", " ", txt.strip())
    t = re.sub(r"\s*\.\s*", ". ", t)
    if len(t) > max_chars:
        t = t[: max_chars - 3].rsplit(". ", 1)[0] + "..."
    return t.strip()


# Frases típicas de intro genérica do bestiário (não são descrição do monstro)
_INTRO_MARKERS = (
    "magias: muitas criaturas",
    "morto-vivo: fantasmas",
    "vantagens únicas numerosas",
    "1d+6 e outros não",
    "como personagens jogadores",
)


def _parece_intro_generica(txt: str) -> bool:
    """Detecta se o texto parece ser intro do bestiário, não descrição do monstro."""
    if not txt or len(txt) < 100:
        return False
    inicio = txt[:500].lower()
    return any(m in inicio for m in _INTRO_MARKERS)


def _encontrar_inicio_descricao(texto: str, nome_monstro: str) -> str:
    """
    Localiza o início da entrada do monstro. Remove índice e intro genérica.
    Prioriza: "Monstros Nome" > título em linha > "Os X são" > nome no texto.
    """
    if not texto or not nome_monstro:
        return texto

    nome_limpo = nome_monstro.replace("-", " ").strip()
    partes = nome_limpo.split()
    texto_lower = texto.lower()

    # 1. "Monstros Nome" — cabeçalho em bestiários (remove índice)
    cabecalho = f"monstros {nome_limpo}"
    pos_cab = texto_lower.find(cabecalho)
    if pos_cab >= 0:
        return texto[pos_cab:]

    if not _parece_intro_generica(texto):
        return texto

    # 2. Título em linha própria (inclui citação após) — ex: "\nHomem Serpente\n\"Você acredita..."
    for v in [nome_monstro, nome_limpo, nome_limpo.replace(" ", "-"), nome_monstro.replace("-", " ")]:
        if len(v) < 5:
            continue
        # Nome no início de linha (após \n)
        pat = re.compile(r"\n\s*" + re.escape(v) + r"\s*[\n\"']", re.IGNORECASE)
        m = pat.search(texto)
        if m:
            return texto[m.start() + 1 :].lstrip()  # +1 para incluir o \n no corte

    # 3. "Os X são" — primeira frase da descrição (ex: "Os homens-serpente são uma raça antiga")
    variantes_corpo = []
    if len(partes) >= 2:
        plural = partes[0] + "s-" + partes[1]
        variantes_corpo.extend([f"os {plural} são", f"os {plural.replace('-', ' ')} são"])
    variantes_corpo.extend([f"os {nome_limpo} são", f"{nome_limpo} são"])

    for v in variantes_corpo:
        if len(v) < 8:
            continue
        pos = texto_lower.find(v)
        if pos >= 0:
            return texto[pos:]

    # 4. Nome no texto — evita ocorrências em listas (ex: "Brownie, Homem- Serpente e Manta")
    variantes = []
    if len(partes) >= 2:
        variantes.extend([partes[0] + "s-" + partes[1], partes[0] + "s " + partes[1]])
    variantes.extend([nome_monstro, nome_limpo, nome_limpo.replace(" ", "-"), nome_monstro.replace("-", "- ")])

    def _em_lista(t: str, pos: int, v: str) -> bool:
        """Detecta se o nome está em lista (ex: 'X, Y e Z')."""
        antes = t[max(0, pos - 80) : pos].lower()
        depois = t[pos + len(v) : pos + len(v) + 60].lower()
        return (
            ", " in antes[-40:] or " e " in depois[:30] or " e " in antes[-30:]
        )

    melhor_pos = -1
    for v in variantes:
        if len(v) < 5:
            continue
        start = 0
        while True:
            pos = texto_lower.find(v.lower(), start)
            if pos < 0:
                break
            if not _em_lista(texto_lower, pos, v) and pos > 50:
                if melhor_pos < 0 or pos < melhor_pos:
                    melhor_pos = pos
                break
            start = pos + 1
    if melhor_pos > 50:
        return texto[melhor_pos:]
    return texto


def _parsear_habilidades_da_linha(s: str) -> list[str]:
    """Extrai lista de habilidades de string como 'Infravisão, Invulnerabilidade (Químico)'."""
    if not s or not s.strip():
        return []
    partes = re.split(r"\s*,\s*", s.strip())
    return [p.strip() for p in partes if len(p.strip()) > 2]


def extrair_monstros_de_texto(texto: str, livro: str, pagina: int = 0) -> list[dict]:
    """Extrai monstros: stat block + descrição anterior + texto após (combate, habilidades)."""
    resultados = []
    matches = list(STAT_PATTERN.finditer(texto))
    for i, m in enumerate(matches):
        nome = m.group(1).strip()
        if len(nome) < 3 or len(nome) > 50:
            continue
        if re.match(r"^[\d\s\-]+$", nome):
            continue

        # Descrição: texto entre stat block anterior e o atual
        inicio = matches[i - 1].end() if i > 0 else 0
        fim = m.start()
        desc_antes = texto[inicio:fim]
        desc_antes = _encontrar_inicio_descricao(desc_antes, nome)

        # Texto APÓS o stat block até o próximo (combate, habilidades especiais)
        fim_match = m.end()
        fim_prox = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        desc_apos = texto[fim_match:fim_prox]
        desc_apos = _limpar_descricao(desc_apos, max_chars=6000)

        descricao = _limpar_descricao(desc_antes, max_chars=8000)
        if desc_apos:
            descricao = descricao + " " + desc_apos if descricao else desc_apos
            descricao = _limpar_descricao(descricao, max_chars=15000)

        # Habilidades na linha de stats (ex: "Chuul: F4, H2, R3, A3, PdF0, Infravisão, Invulnerabilidade (Químico)")
        hab_linha = m.group(7) if m.lastindex >= 7 else None
        habilidades = _parsear_habilidades_da_linha(hab_linha) if hab_linha else []

        mon = {
            "nome": nome,
            "tipo": "outro",
            "caracteristicas": {
                "F": m.group(2).strip(),
                "H": m.group(3).strip(),
                "R": m.group(4).strip(),
                "A": m.group(5).strip(),
                "PdF": m.group(6).strip(),
            },
            "pv": "variável",
            "pm": "0",
            "habilidades": habilidades,
            "tesouro": "",
            "vulnerabilidades": [],
            "fraqueza": "",
            "descricao": descricao,
            "livro": livro,
            "pagina": pagina,
        }
        _adicionar_habilidades_combate(mon)
        resultados.append(mon)
    return resultados


def _adicionar_habilidades_combate(mon: dict) -> None:
    """Extrai habilidades de combate da descrição e adiciona ao monstro."""
    try:
        from src.ingestion.extrair_habilidades_combate import extrair_habilidades_combate
        hab_combate = extrair_habilidades_combate(mon.get("descricao") or "")
        mon["habilidades_combate"] = hab_combate if hab_combate else []
    except Exception:
        mon["habilidades_combate"] = []


def main() -> None:
    print("Extraindo monstros dos PDFs...")
    pdfs = _encontrar_pdfs_monstros()
    if not pdfs:
        print("Nenhum PDF encontrado. Use monstros_canonico.json como fallback.")
        return

    todos_monstros: list[dict] = []
    seen = set()

    try:
        from src.ingestion.pdf_text_extractor import extrair_texto_dual
    except ImportError:
        try:
            import fitz
        except ImportError:
            print("Instale PyMuPDF: pip install pymupdf")
            return

    for pdf_path in pdfs:
        livro = pdf_path.stem.replace("_", " ").replace("-", " ")
        print(f"  Processando: {livro}")
        try:
            texto_por_pagina, _, texto_completo = extrair_texto_dual(pdf_path)
            for pg, texto in texto_por_pagina.items():
                monstros = extrair_monstros_de_texto(texto, livro, pg + 1)
                for mon in monstros:
                    key = (mon["nome"].lower(), livro)
                    if key not in seen:
                        seen.add(key)
                        todos_monstros.append(mon)
        except Exception as e:
            print(f"    Erro em {pdf_path.name}: {e}")

    out_dir = Path("data/processed/monstros")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "monstros_extraidos.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(todos_monstros, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(todos_monstros)} monstros extraídos em {out_path}")


if __name__ == "__main__":
    main()
