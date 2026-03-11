"""
Estratégia 3: Padrões relaxados para F/H/R/A/PdF.
Amplia regex para capturar stats em formatos atípicos ou com OCR degradado.
"""

from __future__ import annotations

import re
from typing import Any

# Variações OCR: F?, H?, R?, A? (A pode ser 1\, r\, J\, I\)
# PdF pode ser pdf, Pdf, PDF, pdfo, pdf0
# Aceita valores em linhas separadas
STAT_RELAXED_1 = re.compile(
    r"F\s*[\'\"\s]*([\dOIlS\-]+)\s*[,;]?\s*"
    r"H\s*[\'\"\s]*([\dOIlS\-]+)(?:/[\dOIlS\-\s]+)*\s*[,;]?\s*"
    r"R\s*[\'\"\s]*([\dOIlS\-]+)\s*[,;]?\s*"
    r"(?:A|1\\|r\\|J\\|I\\|a)\s*[\'\"\s]*([\dOIlS\-]+)\s*[,;]?\s*"
    r"[Pp]d[Ff]\s*[\'\"\s]*([\dOIlS\-]+)",
    re.IGNORECASE,
)

# Blocos em linhas separadas: F2\nH1\nR3\nA0\nPdF0
STAT_RELAXED_2 = re.compile(
    r"(?:^|\s)F\s*([\dOIlS\-]+)\s*(?:\n|[,;])\s*"
    r"H\s*([\dOIlS\-]+)\s*(?:\n|[,;])\s*"
    r"R\s*([\dOIlS\-]+)\s*(?:\n|[,;])\s*"
    r"(?:A|1\\|r\\)\s*([\dOIlS\-]+)\s*(?:\n|[,;])\s*"
    r"[Pp]d[Ff]\s*([\dOIlS\-]+)",
    re.IGNORECASE | re.MULTILINE,
)

# Sem vírgula obrigatória entre stats
STAT_RELAXED_3 = re.compile(
    r"F\s*([\dOIlS\-]+)\s+H\s*([\dOIlS\-]+)\s+R\s*([\dOIlS\-]+)\s+"
    r"(?:A|1\\|r\\|J\\|I\\|i\\)\s*([\dOIlS\-]+)\s+[Pp]d[Ff]\s*([\dOIlS\-]+)",
    re.IGNORECASE,
)

# OCR: H.1 (R1), /\ 1 (A1), PdFl (PdF1) - ex.: Feras-Cactus
STAT_RELAXED_4 = re.compile(
    r"F\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"H\s*\.?\s*([\dOIlS\-]+)(?:/[\dOIlS\-\s]+)*\s*[,;]?\s*"
    r"(?:H\.|R)\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"(?:/\s*\\\\|A|1\\\\|r\\\\|i\\\\)\s*([\dOIlS\-]+)\s*[,;]?\s*"  # /\ = A (OCR)
    r"[Pp]d[Ff]\s*([l1\dOIlS\-]+)",  # PdFl = PdF1 (l=1 OCR)
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


def _encontrar_nome(texto: str, pos: int) -> str | None:
    antes = texto[:pos]
    linhas = antes.split("\n")
    for i in range(len(linhas) - 1, -1, -1):
        ln = linhas[i].strip()
        if not ln or len(ln) < 3 or len(ln) > 50:
            continue
        if ln.startswith(('"', "'", "-")) or re.match(r"^CON\s|^#\s|^\d", ln, re.I):
            continue
        if re.match(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{2,45}$", ln) and "(" not in ln:
            if ln not in ("d ' 'd", "var", "l", "O", "A", "I"):
                return ln
    return None


def extrair_com_patterns_relaxed(
    texto: str,
    livro: str,
    bestiario: list[dict],
    pos_ja_extraidos: set[int],
    page_breaks: list[int] | None = None,
) -> list[dict]:
    """
    Aplica padrões relaxados para capturar F/H/R/A/PdF em formatos atípicos.
    Evita duplicatas com pos_ja_extraidos (posições do extrator principal).
    """
    from src.ingestion.daemon_extractor_dedicado import (
        _encontrar_nome,
        _extrair_bloco_completo,
        _extrair_descricao,
    )
    from src.ingestion.daemon_stats_fallback import buscar_no_bestiario, mesclar_stats
    from src.ingestion.extrair_habilidades_daemon import extrair_habilidades_daemon

    def _pagina(pos: int) -> int:
        if page_breaks and len(page_breaks) > 1:
            for i in range(len(page_breaks) - 1):
                if page_breaks[i] <= pos < page_breaks[i + 1]:
                    return i + 1
        return 1

    def _prox_stat(pos: int, todos: list[re.Match]) -> int:
        for m in todos:
            if m.start() > pos:
                return m.start()
        return len(texto)

    resultados: list[dict] = []
    patterns = [STAT_RELAXED_1, STAT_RELAXED_2, STAT_RELAXED_3, STAT_RELAXED_4]
    todos_matches: list[re.Match] = []
    for pat in patterns:
        todos_matches.extend(pat.finditer(texto))

    for m in todos_matches:
        if m.start() in pos_ja_extraidos:
            continue
        f, h, r, a, pdf = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        nome = _encontrar_nome(texto, m.start())
        if not nome or len(nome) < 3:
            continue

        fim_match = m.end()
        fim_prox = _prox_stat(fim_match, sorted(todos_matches, key=lambda x: x.start()))
        nome_proximo = None
        for mm in todos_matches:
            if mm.start() == fim_prox:
                nome_proximo = _encontrar_nome(texto, mm.start())
                break

        bloco_completo = _extrair_bloco_completo(
            texto, m.start(), fim_match, fim_prox, nome_proximo
        )
        descricao = _extrair_descricao(texto, fim_match, fim_prox)

        ref = buscar_no_bestiario(nome, bestiario)
        stats_ref = ref.get("caracteristicas") if ref else None
        from src.ingestion.daemon_stats_fallback import extrair_stats_da_descricao
        stats_desc = extrair_stats_da_descricao(descricao)
        caracteristicas = mesclar_stats(
            {
                "F": _normalizar_stat(f),
                "H": _normalizar_stat(h),
                "R": _normalizar_stat(r),
                "A": _normalizar_stat(a),
                "PdF": _normalizar_stat(pdf),
            },
            stats_desc,
            stats_ref,
        )
        hab_combate = extrair_habilidades_daemon(bloco_completo)

        resultados.append({
            "nome": nome.strip(),
            "tipo": "outro",
            "caracteristicas": caracteristicas,
            "pv": "variável",
            "pm": "0",
            "habilidades": [],
            "habilidades_combate": hab_combate,
            "tesouro": "",
            "vulnerabilidades": [],
            "fraqueza": "",
            "descricao": descricao,
            "livro": livro,
            "pagina": _pagina(m.start()),
            "_fonte": "daemon_patterns_relaxed",
        })
        pos_ja_extraidos.add(m.start())

    return resultados
