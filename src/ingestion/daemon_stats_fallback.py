"""
Lógica de fallback para extrair F/H/R/A/PdF de monstros do Guia Daemon quando:
1. O bloco de stats está com OCR garbled
2. Usar a descrição para extrair características de batalha
3. Cross-reference com bestiário atual para preencher stats faltantes
"""

from __future__ import annotations

import re
from pathlib import Path


def _normalizar_stat(val: str) -> str:
    """Converte OCR artifacts para dígitos válidos. Normaliza / para - em ranges."""
    if not val or not val.strip():
        return "0"
    v = val.strip()
    v = re.sub(r"\bO\b", "0", v)
    v = re.sub(r"\bl\b", "1", v)
    v = re.sub(r"\bI\b", "1", v)
    v = re.sub(r"\bS\b", "5", v)
    v = v.replace("/", "-")  # 1/4 → 1-4
    return v


def extrair_stats_da_descricao(descricao: str) -> dict[str, str]:
    """
    Analisa a descrição minuciosamente para extrair F, H, R, A, PdF.
    Busca padrões como "F4", "H3", "R6", "A4", "PdF0", "têm H3", "tem H0",
    "Invulnerabilidade", "Vulnerabilidade", "Armadura 0/2", etc.
    """
    resultado: dict[str, str] = {}
    texto = descricao or ""
    texto_lower = texto.lower()

    # Padrões explícitos: F4, H3, R6, A4, PdF0 (com variações)
    for stat, pattern in [
        ("F", r"\bF\s*(\d+(?:\s*[-–/]\s*\d+)?)\b"),
        ("H", r"\bH\s*(\d+(?:\s*[-–/]\s*\d+)?)\b"),
        ("R", r"\bR\s*(\d+(?:\s*[-–/]\s*\d+)?)\b"),
        ("A", r"\bA\s*(\d+(?:\s*[-–/]\s*\d+)?)\b"),
        ("PdF", r"\bPdF\s*(\d+(?:\s*[-–/]\s*\d+)?)\b"),
    ]:
        m = re.search(pattern, texto, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Pegar o maior/mais completo se houver múltiplas menções
            if stat not in resultado or len(val) >= len(resultado.get(stat, "")):
                resultado[stat] = val.replace(" ", "")

    # "têm H3", "tem H0", "tem HO" (corpo vs tentáculos)
    if "H" not in resultado:
        for m in re.finditer(r"t[eê]n?[m]?\s+H\s*(\d+)", texto, re.I):
            resultado["H"] = m.group(1)
            break

    # "Armadura 0/2", "A4" no contexto de núcleo
    if "A" not in resultado:
        m = re.search(r"[Aa]rmadura\s*(\d+(?:/\d+)?)", texto)
        if m:
            resultado["A"] = m.group(1).replace("/", "-")

    # Invulnerabilidade / Vulnerabilidade → habilidades, não F/H/R/A
    # (podem indicar A alto ou baixo em contextos específicos)

    return resultado


def buscar_no_bestiario(nome: str, bestiario: list[dict]) -> dict | None:
    """
    Busca monstro no bestiário por nome (fuzzy).
    Retorna o monstro encontrado ou None.
    Ignora monstros do Guia Daemon.
    """
    nome_limpo = _normalizar_nome_busca(nome)
    if not nome_limpo:
        return None

    for m in bestiario:
        livro = (m.get("livro") or "").lower()
        if "daemon" in livro or "guia" in livro:
            continue
        nome_cand = _normalizar_nome_busca(m.get("nome", ""))
        if nome_cand and nome_limpo == nome_cand:
            return m
        # Match parcial (ex: "Ameba-Gigante" vs "Ameba Gigante")
        if nome_cand and (nome_limpo in nome_cand or nome_cand in nome_limpo):
            return m
    return None


def _normalizar_nome_busca(nome: str) -> str:
    """Normaliza nome para comparação fuzzy."""
    if not nome:
        return ""
    n = nome.lower().strip()
    n = re.sub(r"[\s\-_]+", " ", n)
    n = re.sub(r"[àáâãäå]", "a", n)
    n = re.sub(r"[èéêë]", "e", n)
    n = re.sub(r"[ìíîï]", "i", n)
    n = re.sub(r"[òóôõö]", "o", n)
    n = re.sub(r"[ùúûü]", "u", n)
    n = re.sub(r"[ç]", "c", n)
    return n.strip()


def carregar_bestiario() -> list[dict]:
    """Carrega monstros_extraidos.json (excluindo Daemon para cross-ref)."""
    path = Path(__file__).resolve().parents[1].parent / "data" / "processed" / "monstros" / "monstros_extraidos.json"
    if not path.exists():
        return []
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    return [m for m in data if "daemon" not in (m.get("livro") or "").lower()]


def mesclar_stats(
    stats_bloco: dict[str, str] | None,
    stats_descricao: dict[str, str],
    stats_bestiario: dict[str, str] | None,
) -> dict[str, str]:
    """
    Mescla stats de três fontes. Prioridade: bloco > descrição > bestiário.
    Preenche apenas campos faltantes.
    """
    padrao = {"F": "0", "H": "0", "R": "0", "A": "0", "PdF": "0"}
    for fonte in [stats_bloco, stats_descricao, stats_bestiario]:
        if not fonte:
            continue
        for k, v in fonte.items():
            if k in padrao and v and (not padrao[k] or padrao[k] == "0"):
                padrao[k] = _normalizar_stat(v)
    return padrao
