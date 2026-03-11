"""
Formata monstros para exibição com siglas no padrão Nome(Sigla).
Ex.: F2-3, H3, R3-5 → Força(F) 2-3, Habilidade(H) 3, Resistência(R) 3-5

Formato padrão: docs/FORMATO_FICHA_MONSTRO.md — tabela completa com todos os campos.
"""

from __future__ import annotations

from typing import Any

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.utils.normalizar_ocr import normalizar_ocr

VAZIO = "—"

LABELS_CARAC = {
    "F": "Força(F)",
    "H": "Habilidade(H)",
    "R": "Resistência(R)",
    "A": "Armadura(A)",
    "PdF": "Poder de Fogo(PdF)",
}


def formatar_caracteristicas(caracteristicas: dict[str, str]) -> str:
    """Formata características com Nome(Sigla) valor."""
    if not caracteristicas:
        return ""
    partes = []
    for k, v in caracteristicas.items():
        label = LABELS_CARAC.get(k, k)
        partes.append(f"{label} {v}")
    return ", ".join(partes)


def formatar_monstro_para_exibicao(monstro: dict) -> str:
    """
    Gera texto completo do monstro para exibição (RAG, UI).
    Inclui: descrição, características, habilidades, fraqueza/vulnerabilidades.
    """
    nome = monstro.get("nome", "")
    carac = monstro.get("caracteristicas") or {}
    carac_str = formatar_caracteristicas(carac)
    descricao = monstro.get("descricao", "").strip()
    habilidades = monstro.get("habilidades") or []
    vulnerabilidades = monstro.get("vulnerabilidades") or []
    fraqueza = monstro.get("fraqueza", "").strip()

    partes = [
        nome,
        f"Tipo: {monstro.get('tipo', '')}.",
        f"Características: {carac_str}.",
        f"PV: {monstro.get('pv', '')}. PM: {monstro.get('pm', '')}.",
    ]
    partes.append("Habilidades: " + ("; ".join(habilidades) if habilidades else "nenhuma") + ".")
    if vulnerabilidades:
        partes.append("Vulnerabilidades: " + ", ".join(vulnerabilidades) + ".")
    if fraqueza:
        partes.append("Fraqueza: " + fraqueza + ".")
    partes.append(f"Fonte: {monstro.get('livro', '')}.")

    texto_stats = " ".join(p for p in partes if p)
    if descricao:
        return f"{descricao}\n\n{texto_stats}"
    return texto_stats


def _valor(v: Any, corrigir_ocr: bool = False) -> str:
    """Retorna valor ou — se vazio. Se corrigir_ocr, aplica normalização OCR."""
    if v is None:
        return VAZIO
    if isinstance(v, (list, dict)) and not v:
        return VAZIO
    if isinstance(v, str) and not v.strip():
        return VAZIO
    s = str(v).strip()
    return normalizar_ocr(s) if corrigir_ocr and s else s


def _resumir_ataques(ataques: list[dict] | None) -> str:
    """Resume ataques_especificos em texto."""
    if not ataques:
        return VAZIO
    partes = []
    for a in ataques:
        nome = a.get("nome", "")
        fa_fd = a.get("fa_fd", "")
        dano = a.get("dano", "")
        p = nome
        if fa_fd:
            p += f" ({fa_fd})"
        if dano:
            p += f" dano {dano}"
        partes.append(p)
    return "; ".join(partes) if partes else VAZIO


def _juntar_habilidades(monstro: dict) -> str:
    """Junta habilidades + habilidades_extra."""
    hab = monstro.get("habilidades") or []
    extra = monstro.get("habilidades_extra")
    partes = list(hab) if isinstance(hab, list) else [str(hab)]
    if extra:
        partes.append(str(extra))
    return "; ".join(partes) if partes else VAZIO


def formatar_ficha_monstro_tabela(monstro: dict, incluir_descricao: bool = True) -> str:
    """
    Formata monstro no padrão completo e tabelado (docs/FORMATO_FICHA_MONSTRO.md).
    Todos os campos na ordem definida; vazios = —.
    """
    c = monstro.get("caracteristicas") or {}
    carac = f"F{c.get('F','')}, H{c.get('H','')}, R{c.get('R','')}, A{c.get('A','')}, PdF{c.get('PdF','')}"

    _v = lambda x, ocr=True: _valor(x, corrigir_ocr=ocr)
    linhas = [
        ("Nome", _valor(monstro.get("nome"))),
        ("Características", carac if c else VAZIO),
        ("PV / PM", f"{_valor(monstro.get('pv'))} / {_valor(monstro.get('pm'))}"),
        ("Escala", _v(monstro.get("escala"))),
        ("Comportamento", _v(monstro.get("comportamento"))),
        ("Tamanho", _v(monstro.get("altura_tamanho"))),
        ("Peso", _v(monstro.get("peso"))),
        ("Habitat", _v(monstro.get("habitat"))),
        ("Comportamento dia/noite", _v(monstro.get("comportamento_dia_noite"))),
        ("Combate", _v(monstro.get("comportamento_combate"))),
        ("Ataques", _resumir_ataques(monstro.get("ataques_especificos"))),
        ("Imunidades", ", ".join(normalizar_ocr(str(i)) for i in (monstro.get("imunidades") or [])) or VAZIO),
        ("Fraquezas", ", ".join(normalizar_ocr(str(f)) for f in (monstro.get("fraquezas") or [])) if isinstance(monstro.get("fraquezas"), list) else _v(monstro.get("fraquezas") or monstro.get("fraqueza"))),
        ("Habilidades", _v(_juntar_habilidades(monstro))),
        ("Movimento", _v(monstro.get("movimento"))),
        ("Origem criação", _v(monstro.get("origem_criacao"))),
        ("Uso cultural", _v(monstro.get("uso_cultural"))),
        ("Vínculo montaria", _v(monstro.get("vinculo_montaria"))),
        ("Veneno", _v(monstro.get("veneno_detalhado"))),
        ("Resistência controle", _v(monstro.get("resistencia_controle"))),
        ("Necessidades", _v(monstro.get("necessidades"))),
        ("Recuperação", _v(monstro.get("recuperacao_pv"))),
        ("Táticas", _v(monstro.get("taticas"))),
        ("Tesouro", _v(monstro.get("tesouro"))),
        ("Fonte", _valor(monstro.get("fonte_referencia")) or _valor(monstro.get("livro"))),
    ]

    # Tabela Markdown
    out = ["| Campo | Valor |", "|-------|-------|"]
    for campo, valor in linhas:
        val = (valor or VAZIO).replace("\n", " ").strip()
        if len(val) > 200:
            val = val[:197] + "..."
        out.append(f"| **{campo}** | {val} |")

    if incluir_descricao and monstro.get("descricao"):
        desc = normalizar_ocr((monstro.get("descricao") or "").strip())
        if len(desc) > 500:
            desc = desc[:497] + "..."
        out.append("")
        out.append("| **Descrição** | " + desc.replace("\n", " ").replace("|", "\\|") + " |")

    return "\n".join(out)
