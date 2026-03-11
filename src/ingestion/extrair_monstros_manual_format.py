"""
Extrator para o formato do Manual dos Monstros (3D&T Alpha).
Segue o padrão do livro:
- Nome Variante, 19N ou 61S ou 84K (escala: N=Ningen, S=Sugoi, K=Kiodai)
- F2 (esmagamento), H2, R4, A3, PdF0; 20 PVs, 20 PMs; Habilidades; Desvantagens.
- Táticas
- Tesouro
"""

from __future__ import annotations

import re
from typing import Any


# Padrão: Nome, Número + escala (N/S/K) em uma linha, depois F/H/R/A/PdF; PVs, PMs; habilidades
# Ex: "Gárgula de Abadia, 19N" ou "Dragão-de-Aço, 61S" ou "Kobold Comum, 1N"
# Aceita PVs sem PMs: "70 PVs; Kobold, Horda"
# Aceita: "Nome, Variante, 58S" (ex.: Daresha, Guerreira Deicida, 58S)
MANUAL_PATTERN = re.compile(
    r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*,\s*"
    r"(?:(?P<variant>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*,\s*)?"
    r"(\d+)([NSK]?)\s*\n\s*"
    r"F\s*(\d+)\s*(?:\([^)]+\))?\s*,\s*"
    r"H\s*(\d+)\s*,\s*"
    r"R\s*(\d+)\s*,\s*"
    r"A\s*(\d+)\s*,\s*"
    r"PdF\s*(\d+)\s*(?:\([^)]+\))?\s*;\s*"
    r"([^.\n]+?)(?=\.\s*\n|\n[A-Za-zÀ-ÿ]|\n\n|\Z)",
    re.IGNORECASE | re.DOTALL,
)

# Extrai PV e PM do bloco após ";"
# Formatos: "35 PVs, 55 PMs" | "70 PVs;" (sem PMs) | "1d+6, 0"
PV_PM_PATTERN = re.compile(
    r"(?:^|;)\s*"
    r"(?:(?P<pv_num>\d+)\s*PVs?|(?P<pv_dice>1d\s*[\+\-]\s*\d+)|(?P<pv_var>vari[aá]vel))"
    r"\s*[,;]?\s*"
    r"(?:(?P<pm_num>\d+)\s*PMs?|(?P<pm_var>vari[aá]vel))?",
    re.IGNORECASE,
)


def _extrair_pv_pm(bloco: str) -> tuple[str, str]:
    """Extrai PV e PM do bloco de stats. Retorna (pv, pm). PM pode ser '0' se ausente."""
    pv, pm = "variável", "0"
    m = PV_PM_PATTERN.search(bloco)
    if m:
        if m.group("pv_num"):
            pv = m.group("pv_num")
        elif m.group("pv_dice"):
            pv = m.group("pv_dice").replace(" ", "")
        elif m.group("pv_var"):
            pv = "variável"
        if m.group("pm_num"):
            pm = m.group("pm_num")
        elif m.group("pm_var"):
            pm = "variável"
    return (pv, pm)


def _parsear_habilidades_bloco(bloco: str) -> list[str]:
    """Extrai habilidades do bloco após PV/PM. Formato: 'X PVs, Y PMs; H1; H2; H3.'"""
    pv_pm_end = PV_PM_PATTERN.search(bloco)
    if not pv_pm_end:
        return []
    resto = bloco[pv_pm_end.end() :].strip()
    if not resto or resto.startswith("."):
        return []
    # Remove ponto final e split por ";"
    resto = re.sub(r"\.\s*$", "", resto)
    partes = [p.strip() for p in resto.split(";") if len(p.strip()) > 1]
    return partes[:25]


def _extrair_taticas_tesouro(bloco: str) -> tuple[str, str]:
    """Extrai seções Táticas e Tesouro do bloco após o stat block."""
    taticas, tesouro = "", ""
    bloco_lower = bloco.lower()

    # Táticas: da linha "Táticas" até "Tesouro" ou fim
    m_tat = re.search(r"\bTáticas\b\s*\n(.*?)(?=\bTesouro\b|$)", bloco, re.IGNORECASE | re.DOTALL)
    if m_tat:
        taticas = re.sub(r"\s+", " ", m_tat.group(1).strip())[:3000]

    # Tesouro: da linha "Tesouro" até próximo título de monstro ou fim
    m_tes = re.search(r"\bTesouro\b\s*\n(.*?)(?=\n[A-ZÀ-ÿ][a-zà-ÿ\s\-]{3,40}\s*\n|\d+/\d+|$)", bloco, re.IGNORECASE | re.DOTALL)
    if m_tes:
        tesouro = re.sub(r"\s+", " ", m_tes.group(1).strip())[:4000]

    return (taticas, tesouro)


def _extrair_titulo_secao(texto_antes: str, nome_stat: str) -> str | None:
    """
    Extrai o título da seção do texto antes do stat block.
    Quando o livro tem "Daresha, a Caçadora de Keenn" como título e "Daresha, Guerreira Deicida, 58S"
    no stat block, retorna o título para usar como nome canônico.
    Procura linhas que parecem títulos (nome próprio seguido de vírgula e descrição, ex.: "X, a/o Y").
    """
    if not texto_antes or len(texto_antes) < 20:
        return None
    # Primeira parte do nome no stat (ex.: "Daresha" de "Daresha, Guerreira Deicida")
    nome_base = nome_stat.split(",")[0].strip() if "," in nome_stat else nome_stat
    if len(nome_base) < 4:
        return None
    # Procura por "NomeBase, a/o/de ..." em linhas próprias (título comum no Manual)
    linhas = [ln.strip() for ln in texto_antes.split("\n") if len(ln.strip()) > 10]
    for ln in linhas[:20]:  # primeiras 20 linhas
        if ln.startswith(nome_base + ",") and len(ln) > len(nome_base) + 5:
            # Título como "Daresha, a Caçadora de Keenn" (diferente do stat "Daresha, Guerreira Deicida")
            if "Guerreira" not in ln and "Deicida" not in ln and "Variante" not in ln.lower():
                return ln
    return None


def _extrair_descricao_lore(texto_antes: str, nome_criatura: str) -> str:
    """
    Tenta extrair a descrição/lore do texto antes do stat block.
    Remove Táticas e Tesouro do monstro anterior se presentes.
    Se o texto contém conteúdo do monstro anterior, procura o início da seção
    do monstro atual (ex.: "Homem-Sapo" como cabeçalho antes da citação).
    """
    if not texto_antes or len(texto_antes) < 20:
        return ""
    t = texto_antes
    # Nome base para buscar início da seção (ex.: "Homem-Sapo" de "Homem-Sapo, 8N")
    nome_base = nome_criatura.split(",")[0].strip() if "," in nome_criatura else nome_criatura
    # Tenta encontrar onde a seção DESTE monstro começa (evita pegar descrição do anterior)
    # Padrão: "\nHomem-Sapo\n" ou "\n\nHomem-Sapo\n" como cabeçalho de seção
    for padrao in [
        rf"\n\s*{re.escape(nome_base)}\s*\n",
        rf"\n\n\s*{re.escape(nome_base)}\s*\n",
    ]:
        m = re.search(padrao, t, re.IGNORECASE)
        if m:
            t = t[m.start() :]
            break
    # Remove seções Táticas e Tesouro do monstro anterior (ou do atual, se ainda presentes)
    if "\nTáticas\n" in t or "\nTáticas " in t:
        pos = t.lower().find("\ntáticas")
        if pos >= 0:
            t = t[:pos]
    if "\nTesouro\n" in t or "\nTesouro " in t:
        pos = t.lower().find("\ntesouro")
        if pos >= 0:
            t = t[:pos]
    # Remove números de página (ex: 13/144)
    t = re.sub(r"\n\s*\d+/\d+\s*\n", "\n", t)
    # Remove cabeçalhos repetidos (nome do monstro sozinho em linha)
    t = re.sub(r"\n\s*" + re.escape(nome_criatura) + r"\s*\n", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t.strip())
    if len(t) > 6000:
        t = t[:6000].rsplit(". ", 1)[0] + "..."
    return t.strip()


def _limpar_texto(txt: str, max_chars: int = 12000) -> str:
    if not txt or not txt.strip():
        return ""
    t = re.sub(r"\s+", " ", txt.strip())
    t = re.sub(r"\s*\.\s*", ". ", t)
    if len(t) > max_chars:
        t = t[: max_chars - 3].rsplit(". ", 1)[0] + "..."
    return t.strip()


def _pagina_para_posicao(pos: int, page_breaks: list[int]) -> int:
    """Retorna o número da página (1-based) para uma posição no texto concatenado."""
    for p in range(len(page_breaks) - 1, -1, -1):
        if pos >= page_breaks[p]:
            return p + 1
    return 1


def extrair_monstros_manual_completo(
    texto_por_pagina: dict[int, str], livro: str
) -> list[dict[str, Any]]:
    """
    Extrai monstros do Manual dos Monstros usando texto concatenado de todas as páginas.
    Isso permite capturar intros longos (ex.: Dragão Bestial) mesmo quando o stat block
    está em página diferente do intro.
    """
    paginas_ord = sorted(texto_por_pagina.keys())
    partes = [texto_por_pagina[pg] for pg in paginas_ord]
    texto = "\n\n".join(partes)
    page_breaks = [0]
    acc = 0
    for p in partes:
        acc += len(p) + 2
        page_breaks.append(acc)

    resultados = extrair_monstros_manual(
        texto, livro, pagina=1, page_breaks=page_breaks
    )
    return resultados


def extrair_monstros_manual(
    texto: str, livro: str, pagina: int = 1, page_breaks: list[int] | None = None
) -> list[dict[str, Any]]:
    """
    Extrai monstros no formato do Manual dos Monstros.
    Retorna lista de dicts com nome, escala, características, pv, pm, táticas, tesouro, etc.
    Se page_breaks for fornecido, a página de cada monstro é calculada pela posição no texto.
    """
    resultados: list[dict[str, Any]] = []
    matches = list(MANUAL_PATTERN.finditer(texto))
    seen: set[tuple[str, str]] = set()

    for i, m in enumerate(matches):
        nome_base = m.group(1).strip()
        variant = m.group("variant")
        if variant:
            variant = variant.strip()
            nome = f"{nome_base}, {variant}"  # ex.: Daresha, Guerreira Deicida
        else:
            nome = nome_base
        if len(nome) < 3 or len(nome) > 70:
            continue
        if re.match(r"^[\d\s\-]+$", nome):
            continue

        num_escala = m.group(3)
        suf_escala = (m.group(4) or "").upper()
        escala = f"{num_escala}{suf_escala}" if suf_escala else num_escala  # 19N, 61S, 84K ou 61

        bloco_stats = m.group(10).strip()
        pv, pm = _extrair_pv_pm(bloco_stats)
        habilidades = _parsear_habilidades_bloco(bloco_stats)

        # Bloco após o stat: Táticas e Tesouro
        inicio = m.end()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        bloco_apos = texto[inicio:fim]
        taticas, tesouro = _extrair_taticas_tesouro(bloco_apos)

        # Descrição/lore: texto antes do stat block
        inicio_antes = matches[i - 1].end() if i > 0 else 0
        texto_antes = texto[inicio_antes : m.start()]
        # Preferir título da seção quando disponível (ex.: "Daresha, a Caçadora de Keenn" vs "Daresha, Guerreira Deicida")
        titulo = _extrair_titulo_secao(texto_antes, nome)
        if titulo and len(titulo) <= 70:
            nome = titulo
        descricao = _extrair_descricao_lore(texto_antes, nome)
        if not descricao and taticas:
            # Fallback: usar só Táticas+Tesouro, evitando incluir intro do próximo monstro
            fallback = (taticas + "\n" + tesouro).strip()
            if fallback:
                descricao = _limpar_texto(fallback, max_chars=3000)

        pg = (
            _pagina_para_posicao(m.start(), page_breaks)
            if page_breaks
            else pagina
        )
        key = (nome.lower(), livro)
        if key in seen:
            continue
        seen.add(key)

        mon = {
            "nome": nome,
            "escala": escala,
            "tipo": "outro",
            "caracteristicas": {
                "F": m.group(5).strip(),
                "H": m.group(6).strip(),
                "R": m.group(7).strip(),
                "A": m.group(8).strip(),
                "PdF": m.group(9).strip(),
            },
            "pv": pv,
            "pm": pm,
            "habilidades": habilidades,
            "tesouro": tesouro,
            "taticas": taticas,
            "vulnerabilidades": [],
            "fraqueza": "",
            "descricao": descricao,
            "livro": livro,
            "pagina": pg,
        }
        try:
            from src.ingestion.extrair_habilidades_combate import extrair_habilidades_combate
            texto_combate = f"{descricao} {taticas}"
            mon["habilidades_combate"] = extrair_habilidades_combate(texto_combate) or []
        except Exception:
            mon["habilidades_combate"] = []
        resultados.append(mon)
    return resultados
