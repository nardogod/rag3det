"""
Estratégia 4: Extrair subvariantes como entradas separadas.
Detecta padrões: SOLDADO HOBGOBLIN, ARQUEIRO GOBLIN, XAMÃ GOBLIN, CAPITÃO BUGBEAR, etc.
dentro de blocos pais (Goblinóides, Gigantes, etc.).
"""

from __future__ import annotations

import re
from typing import Any

# Padrões de subvariantes: PREFIXO + NOME_RAÇA
SUBVARIANTE_PATTERN = re.compile(
    r"\b(SOLDADO|ARQUEIRO|XAMÃ|XAMAN|CAPITÃO|CAPITAO|SARGENTO|CHEFE|CAVALEIRO|"
    r"GUERREIRO|MAGO|BRUXO|LÍDER|LIDER|ELITE|VETERANO|RECRUTA)\s+"
    r"([A-ZÀ-ÿ][a-zà-ÿ\-]+(?:\s+[A-Za-zÀ-ÿ\-]+)?)\b",
    re.IGNORECASE,
)

# Também: NOME + (SOLDADO), (ARQUEIRO), etc.
SUBVARIANTE_PAREN = re.compile(
    r"\b([A-ZÀ-ÿ][a-zà-ÿ\-]+(?:-[A-Za-zÀ-ÿ]+)?)\s*"
    r"\(?\s*(soldado|arqueiro|xamã|xaman|capitão|chefe|guerreiro)\s*\)?",
    re.IGNORECASE,
)


def _normalizar_nome(n: str) -> str:
    return n.strip().upper().replace("  ", " ")


def _extrair_stats_do_contexto(texto: str) -> dict[str, str]:
    """Tenta extrair F/H/R/A/PdF do texto ao redor da subvariante."""
    from src.ingestion.daemon_stats_fallback import extrair_stats_da_descricao
    return extrair_stats_da_descricao(texto)


def extrair_subvariantes(
    texto: str,
    livro: str,
    bestiario: list[dict],
    monstros_principais: list[dict],
    page_breaks: list[int] | None = None,
) -> list[dict]:
    """
    Identifica subvariantes mencionadas no texto (ex.: SOLDADO HOBGOBLIN)
    que não estão em monstros_principais e extrai como entradas separadas.
    """
    from src.ingestion.daemon_stats_fallback import buscar_no_bestiario, mesclar_stats
    from src.ingestion.extrair_habilidades_daemon import extrair_habilidades_daemon

    nomes_principais = {_normalizar_nome(m.get("nome", "")) for m in monstros_principais}
    subvariantes_extraidas: set[str] = set()
    resultados: list[dict] = []

    def _pagina(pos: int) -> int:
        if page_breaks and len(page_breaks) > 1:
            for i in range(len(page_breaks) - 1):
                if page_breaks[i] <= pos < page_breaks[i + 1]:
                    return i + 1
        return 1

    for m in SUBVARIANTE_PATTERN.finditer(texto):
        prefixo, raca = m.group(1), m.group(2)
        nome_completo = f"{prefixo} {raca}"
        nome_norm = _normalizar_nome(nome_completo)
        if nome_norm in nomes_principais or nome_norm in subvariantes_extraidas:
            continue
        # Evitar falsos positivos genéricos
        if raca.lower() in ("de", "da", "do", "das", "dos", "e", "ou"):
            continue

        # Extrair contexto (500 chars ao redor)
        start = max(0, m.start() - 250)
        fim = min(len(texto), m.end() + 500)
        contexto = texto[start:fim]

        stats = _extrair_stats_do_contexto(contexto)
        ref = buscar_no_bestiario(nome_completo, bestiario)
        stats_ref = ref.get("caracteristicas") if ref else None
        # Também buscar pela raça base
        ref_base = buscar_no_bestiario(raca, bestiario)
        if ref_base and not ref:
            stats_ref = ref_base.get("caracteristicas")
        caracteristicas = mesclar_stats(
            {"F": "0", "H": "0", "R": "0", "A": "0", "PdF": "0"},
            stats,
            stats_ref,
        )
        hab_combate = extrair_habilidades_daemon(contexto)

        resultados.append({
            "nome": nome_completo.strip(),
            "tipo": "outro",
            "caracteristicas": caracteristicas,
            "pv": "variável",
            "pm": "0",
            "habilidades": [],
            "habilidades_combate": hab_combate,
            "tesouro": "",
            "vulnerabilidades": [],
            "fraqueza": "",
            "descricao": contexto[:2000],
            "livro": livro,
            "pagina": _pagina(m.start()),
            "_fonte": "daemon_subvariantes",
        })
        subvariantes_extraidas.add(nome_norm)

    return resultados
