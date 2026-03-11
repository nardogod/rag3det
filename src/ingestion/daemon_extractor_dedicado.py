"""
Extrator DEDICADO ao Guia de Monstros de Arton (Daemon Editora).
A descrição é parte crucial: captura o bloco completo (nome → citação → CON/#Ataques → F/H/R/A/PdF → descrição)
até o início do próximo monstro, evitando mistura de entradas.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Padrões F/H/R/A/PdF (estrito e flex)
STAT_PATTERN = re.compile(
    r"F\s*([\dOIlS\-]+)(?:\([^)]+\))?\s*[,;]?\s*"
    r"H\s*([\dOIlS\-]+)(?:/[\dOIlS\-\s]+)*\s*[,;]?\s*"
    r"R\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"(?:A|1\\|r\\|J\\|I\\)\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"PdF\s*['\"]?([\dOIlS\-]+)(?:\([^)]+\))?"
    r"(?:[,;]\s*([^.\n]+))?",
    re.IGNORECASE,
)

STAT_FLEX = re.compile(
    r"F\s*([\dOIlS\-]+)(?:\([^)]+\))?\s*[,;]?\s*"
    r"H\s*([\dOIlS\-]+)(?:/[\dOIlS\-\s]+)*\s*[,;]?\s*"
    r"R\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"[^P]*?([\dOIlS\-/]+)\s*[,;]?\s*PdF\s*['\"]?([\dOIlS\-]+)"
    r"(?:[,;]\s*([^.\n]+))?",
    re.IGNORECASE,
)


def _normalizar_stat(val: str) -> str:
    v = (val or "").strip()
    v = re.sub(r"\bO\b", "0", v)
    v = re.sub(r"\bl\b", "1", v)
    v = re.sub(r"\bI\b", "1", v)
    v = re.sub(r"\bS\b", "5", v)
    v = v.replace("/", "-")
    return v or "0"


def _encontrar_nome(texto: str, pos_stat: int) -> str | None:
    """Nome do monstro antes do bloco F/H/R/A/PdF."""
    antes = texto[:pos_stat]
    linhas = antes.split("\n")
    for i in range(len(linhas) - 1, -1, -1):
        ln = linhas[i].strip()
        if not ln or len(ln) < 3:
            continue
        if ln.startswith(('"', "'", "-")):
            continue
        if re.match(r"^CON\s|^#\s|^\d|^Mordida|^Garras|^Pancada|^Pinça|^Asfixia|^Bicada|^Cauda|^Bico", ln, re.I):
            continue
        if re.match(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{2,45}$", ln) and "(" not in ln:
            if ln not in ("d ' 'd", "var", "l", "O", "A", "I") and not re.match(r"^[d'\s]+$", ln):
                return ln
    return None


def _encontrar_fim_bloco_atual(
    texto: str, fim_stat: int, prox_stat: int, nome_proximo: str | None = None
) -> int:
    """
    Encontra onde termina o bloco do monstro atual (evita incluir o próximo).
    Se nome_proximo for dado, corta ao encontrar esse nome no texto (crucial quando
    monstros estão no mesmo parágrafo sem quebras de linha).
    """
    entre = texto[fim_stat:prox_stat]
    # 1) Cortar pelo nome do próximo monstro (funciona mesmo em texto contínuo)
    if nome_proximo and len(nome_proximo) >= 4:
        # Escapar para regex; buscar como palavra inteira
        esc = re.escape(nome_proximo)
        m = re.search(rf"\b{esc}\b", entre, re.I)
        if m:
            return fim_stat + m.start()
    # 2) Fallback: procurar por linhas que parecem início de novo monstro
    linhas = entre.split("\n")
    for i, ln in enumerate(linhas):
        ln_strip = ln.strip()
        if not ln_strip or len(ln_strip) < 3:
            continue
        if (re.match(r"^[A-ZÀ-ÿ][a-zà-ÿ\s\-']{1,40}$", ln_strip) or re.match(r"^[A-ZÀ-ÿ][A-ZÀ-ÿ\s\-']{1,40}$", ln_strip)) and "(" not in ln_strip:
            if i + 1 < len(linhas):
                prox = linhas[i + 1].strip()
                if prox.startswith(('"', "'", "-")) or re.match(r"^CON\s", prox, re.I):
                    pos = fim_stat + sum(len(l) + 1 for l in linhas[:i])
                    return pos
    return prox_stat


def _extrair_bloco_completo(
    texto: str, inicio_stat: int, fim_stat: int, prox_stat: int, nome_proximo: str | None = None
) -> str:
    """
    Extrai o bloco completo do monstro: ~500 chars antes do stat até o início do próximo.
    Inclui #Ataques, Mordida, Garras, etc. — crucial para tabulação.
    Evita incluir ataques do próximo monstro (corta em nome_proximo se fornecido).
    """
    fim_real = _encontrar_fim_bloco_atual(texto, fim_stat, prox_stat, nome_proximo)
    ctx_antes = 500
    start = max(0, inicio_stat - ctx_antes)
    return texto[start:fim_real]


def _extrair_descricao(texto: str, fim_stat: int, prox_stat: int) -> str:
    """Descrição narrativa após o stat block."""
    desc = texto[fim_stat:prox_stat]
    linhas = desc.split("\n")
    inicio = 0
    for i, ln in enumerate(linhas):
        ln_clean = ln.strip()
        if len(ln_clean) < 25:
            continue
        if not re.match(r"^(CON|FR|DEX|#|Mordida|Garras|Pancada|Bicada|Cauda|Bico|Asfixia)", ln_clean, re.I):
            inicio = i
            break
    desc = " ".join(linhas[inicio:])
    desc = re.sub(r"\s+", " ", desc).strip()
    return desc[:15000]


def _parsear_habilidades(s: str) -> list[str]:
    if not s or not s.strip():
        return []
    return [p.strip() for p in re.split(r"\s*,\s*", s.strip()) if len(p.strip()) > 2]


def _pagina_para_posicao(pos: int, page_breaks: list[int]) -> int:
    """Retorna o número da página (1-based) para a posição no texto concatenado."""
    for i in range(len(page_breaks) - 1):
        if page_breaks[i] <= pos < page_breaks[i + 1]:
            return i + 1
    return len(page_breaks)


def extrair_monstros_texto_completo(
    texto_por_pagina: dict[int, str],
    livro: str,
    bestiario: list[dict],
) -> list[dict]:
    """
    Extrai monstros do texto completo (páginas concatenadas).
    Permite descrições que atravessam páginas (ex.: Minotauro).
    """
    paginas_ord = sorted(texto_por_pagina.keys())
    partes = [texto_por_pagina[pg] for pg in paginas_ord]
    texto = "\n\n".join(partes)
    page_breaks = [0]
    acc = 0
    for p in partes:
        acc += len(p) + 2  # +2 para "\n\n"
        page_breaks.append(acc)

    return _extrair_monstros_impl(texto, livro, bestiario, page_breaks=page_breaks)


def _extrair_monstros_impl(
    texto: str,
    livro: str,
    bestiario: list[dict],
    pagina: int = 1,
    page_breaks: list[int] | None = None,
) -> list[dict]:
    """Implementação compartilhada: extração de monstros do texto."""
    from src.ingestion.daemon_stats_fallback import extrair_stats_da_descricao, buscar_no_bestiario, mesclar_stats
    from src.ingestion.extrair_habilidades_daemon import extrair_habilidades_daemon

    def _pagina_match(pos: int) -> int:
        if page_breaks and len(page_breaks) > 1:
            return _pagina_para_posicao(pos, page_breaks)
        return pagina

    resultados: list[dict] = []
    matches = list(STAT_PATTERN.finditer(texto))
    flex_matches = list(STAT_FLEX.finditer(texto))
    pos_extraidos: set[int] = set()

    def _processar_match(m: re.Match, flex: bool = False) -> dict | None:
        f, h, r, a, pdf = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        hab_linha = m.group(6) if m.lastindex >= 6 else None
        habilidades = _parsear_habilidades(hab_linha) if hab_linha else []

        nome = _encontrar_nome(texto, m.start())
        if not nome or len(nome) < 3 or len(nome) > 50:
            return None
        if re.match(r"^[\d\s\-]+$", nome) or re.match(r"^[d'\s]+$", nome) or "' '" in nome:
            return None

        fim_match = m.end()
        # Próximo stat: usar matches ou flex conforme o caso
        todos_starts = sorted({x.start() for x in matches + flex_matches if x.start() > fim_match})
        fim_prox = todos_starts[0] if todos_starts else len(texto)
        # Nome do próximo monstro: cortar bloco antes dele (evita mistura em parágrafos contínuos)
        nome_proximo = None
        if todos_starts:
            prox_match = next((x for x in matches + flex_matches if x.start() == todos_starts[0]), None)
            if prox_match:
                nome_proximo = _encontrar_nome(texto, prox_match.start())

        bloco_completo = _extrair_bloco_completo(texto, m.start(), fim_match, fim_prox, nome_proximo)
        descricao = _extrair_descricao(texto, fim_match, fim_prox)

        # Stats
        if flex:
            ref = buscar_no_bestiario(nome, bestiario)
            stats_ref = ref.get("caracteristicas") if ref else None
            stats_desc = extrair_stats_da_descricao(descricao)
            stats_parciais = {
                "F": _normalizar_stat(f),
                "H": _normalizar_stat(h),
                "R": _normalizar_stat(r),
                "A": _normalizar_stat(a),
                "PdF": _normalizar_stat(pdf),
            }
            caracteristicas = mesclar_stats(stats_parciais, stats_desc, stats_ref)
        else:
            caracteristicas = {
                "F": _normalizar_stat(f),
                "H": _normalizar_stat(h),
                "R": _normalizar_stat(r),
                "A": _normalizar_stat(a),
                "PdF": _normalizar_stat(pdf),
            }

        # Habilidades de combate: parser DEDICADO Daemon (bloco completo)
        hab_combate = extrair_habilidades_daemon(bloco_completo)

        return {
            "nome": nome.strip(),
            "tipo": "outro",
            "caracteristicas": caracteristicas,
            "pv": "variável",
            "pm": "0",
            "habilidades": habilidades,
            "habilidades_combate": hab_combate,
            "tesouro": "",
            "vulnerabilidades": [],
            "fraqueza": "",
            "descricao": descricao,
            "livro": livro,
            "pagina": _pagina_match(m.start()),
        }

    # Passo 1: padrão estrito
    for i, m in enumerate(matches):
        mon = _processar_match(m, flex=False)
        if mon:
            pos_extraidos.add(m.start())
            resultados.append(mon)

    # Passo 2: padrão flex (blocos não cobertos)
    for m in flex_matches:
        if m.start() in pos_extraidos:
            continue
        mon = _processar_match(m, flex=True)
        if mon:
            resultados.append(mon)

    return resultados


def extrair_monstros_pagina(
    texto: str,
    livro: str,
    pagina: int,
    bestiario: list[dict],
) -> list[dict]:
    """Extrai todos os monstros de uma página do Guia Daemon."""
    return _extrair_monstros_impl(texto, livro, bestiario, pagina=pagina)
