"""
Estratégia 1: Extrair monstros do Guia Daemon usando bloco CON/FR/DEX/AGI.
Quando F/H/R/A/PdF não aparece, converte atributos Daemon para 3D&T:
  CON → R (Resistência)
  FR → F (Força)
  DEX → H (Habilidade)
  AGI → A (Armadura)
"""

from __future__ import annotations

import re
from typing import Any

# Padrão: CON X-Y, FR X-Y, DEX X-Y, AGI X-Y ... #Ataques
# Aceita #1\taques, #Ataques, # ataques (OCR)
CON_FR_DEX_PATTERN = re.compile(
    r"CON\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"FR\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"DEX\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"(?:AGI|AG)\s*([\dOIlS\-]+)\s*[,;]?\s*"
    r"(?:INT|WILL|CAR|PER[^#]*)?\s*#[\s\\\d]*[Aa]taques",
    re.IGNORECASE | re.DOTALL,
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
    """Nome do monstro antes do bloco CON/FR/DEX."""
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


def _extrair_bloco_e_descricao(
    texto: str, inicio: int, fim_match: int, fim_prox: int
) -> tuple[str, str]:
    """Retorna (bloco_completo, descricao)."""
    ctx = 500
    start = max(0, inicio - ctx)
    bloco = texto[start:fim_prox]
    desc = texto[fim_match:fim_prox]
    desc = re.sub(r"\s+", " ", desc).strip()
    return bloco, desc[:15000]


def extrair_por_con_format(
    texto: str,
    livro: str,
    bestiario: list[dict],
    pos_ja_extraidos: set[int],
    page_breaks: list[int] | None = None,
) -> list[dict]:
    """
    Extrai monstros que têm CON/FR/DEX mas não F/H/R/A/PdF.
    Retorna lista de monstros no formato padrão.
    """
    from src.ingestion.daemon_stats_fallback import buscar_no_bestiario, mesclar_stats
    from src.ingestion.extrair_habilidades_daemon import extrair_habilidades_daemon

    def _pagina(pos: int) -> int:
        if page_breaks and len(page_breaks) > 1:
            for i in range(len(page_breaks) - 1):
                if page_breaks[i] <= pos < page_breaks[i + 1]:
                    return i + 1
        return 1

    resultados: list[dict] = []
    matches = list(CON_FR_DEX_PATTERN.finditer(texto))

    for m in matches:
        if m.start() in pos_ja_extraidos:
            continue
        # Verificar se já existe F/H/R/A/PdF próximo (evitar duplicata)
        trecho = texto[max(0, m.start() - 100) : m.end() + 300]
        if re.search(r"F\s*\d.*H\s*\d.*R\s*\d.*PdF", trecho, re.I | re.DOTALL):
            continue

        con, fr, dex, agi = m.group(1), m.group(2), m.group(3), m.group(4)
        nome = _encontrar_nome(texto, m.start())
        if not nome or len(nome) < 3:
            continue

        # Próximo match ou fim do texto
        prox = [x for x in matches if x.start() > m.end()]
        fim_prox = prox[0].start() if prox else len(texto)
        bloco, descricao = _extrair_bloco_e_descricao(texto, m.start(), m.end(), fim_prox)

        # CON→R, FR→F, DEX→H, AGI→A. PdF: tentar da descrição ou bestiário
        caracteristicas = {
            "F": _normalizar_stat(fr),
            "H": _normalizar_stat(dex),
            "R": _normalizar_stat(con),
            "A": _normalizar_stat(agi),
            "PdF": "0",
        }
        ref = buscar_no_bestiario(nome, bestiario)
        stats_ref = ref.get("caracteristicas") if ref else None
        from src.ingestion.daemon_stats_fallback import extrair_stats_da_descricao
        stats_desc = extrair_stats_da_descricao(descricao)
        caracteristicas = mesclar_stats(caracteristicas, stats_desc, stats_ref)

        hab_combate = extrair_habilidades_daemon(bloco)

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
            "_fonte": "daemon_con_format",
        })

    return resultados
