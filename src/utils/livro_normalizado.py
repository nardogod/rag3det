"""
Mapeamento de nomes de livros para exibição consistente no RAG.
Usado para padronizar citações (ex.: 3dt-manual-da-magia-biblioteca-elfica.pdf → Manual da Magia).
"""

from __future__ import annotations

import json
from pathlib import Path

# Mapeamento padrão: nome do arquivo ou variação → nome normalizado para exibição
_MAPEAMENTO_PADRAO: dict[str, str] = {
    "3dt-manual-da-magia-biblioteca-elfica.pdf": "Manual da Magia",
    "3dt-manual-da-magia-biblioteca-elfica": "Manual da Magia",
    "3dt-alpha-manual-da-magia-biblioteca-elfica.pdf": "Manual da Magia Alpha",
    "3dt-alpha-manual-revisado-biblioteca-elfica.pdf": "Manual Revisado (Alpha)",
    "3dt-manual-revisado-ampliado-e-turbinado-biblioteca-elfica.pdf": "Manual Revisado Ampliado e Turbinado",
    "3dt-alpha-manual-dos-dragoes-biblioteca-elfica.pdf": "Manual dos Dragões",
    "3dt-alpha-manual-dos-monstros.pdf": "Manual dos Monstros",
    "manual da magia": "Manual da Magia",
    "manual da magia 3dt": "Manual da Magia",
    "manual 3d&t turbinado": "Manual 3D&T Turbinado",
    "manual 3d&t turbinado digital": "Manual 3D&T Turbinado",
    "manual turbinado": "Manual 3D&T Turbinado",
    "manual do aventureiro": "Manual do Aventureiro",
    "manual do aventureiro 3dt": "Manual do Aventureiro",
    "manual alpha": "Manual Alpha",
    "3det alpha magias": "Manual Alpha",
    "manual revisado alpha": "Manual Revisado (Alpha)",
    "manual revisado ampliado e turbinado": "Manual Revisado Ampliado e Turbinado",
    "manual dos monstros": "Manual dos Monstros",
    "bestiario alpha": "Bestiário Alpha",
    "Manual dos Monstros": "Manual dos Monstros",
    "Manual da Magia": "Manual da Magia",
    "Manual 3D&T Turbinado": "Manual 3D&T Turbinado",
    "Manual do Aventureiro": "Manual do Aventureiro",
    "Manual Alpha": "Manual Alpha",
    "Bestiário Alpha": "Bestiário Alpha",
    "Manual dos Dragões": "Manual dos Dragões",
}


def _carregar_politica() -> dict:
    """Carrega política de prioridade se existir."""
    base = Path(__file__).resolve().parents[2]
    path = base / "data" / "processed" / "politica_prioridade_fontes.json"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def normalizar_livro(livro: str | None) -> str:
    """
    Retorna o nome normalizado do livro para exibição consistente.

    - Se livro for None ou vazio, retorna string vazia.
    - Caso contrário, usa mapeamento ou retorna o próprio valor se não houver mapeamento.
    """
    if not livro or not isinstance(livro, str):
        return ""
    livro_clean = livro.strip()
    if not livro_clean:
        return ""
    # Busca exata
    if livro_clean in _MAPEAMENTO_PADRAO:
        return _MAPEAMENTO_PADRAO[livro_clean]
    # Busca case-insensitive
    for k, v in _MAPEAMENTO_PADRAO.items():
        if k.lower() == livro_clean.lower():
            return v
    return livro_clean


def obter_prioridade_fonte(livro: str | None) -> int:
    """
    Retorna prioridade da fonte (menor = maior prioridade).
    Usado para ordenar/merge quando o mesmo item aparece em vários livros.
    """
    if not livro:
        return 999
    politica = _carregar_politica()
    ordem = politica.get("ordem_prioridade", [])
    livro_norm = normalizar_livro(livro) or livro
    for i, fonte in enumerate(ordem):
        if fonte.lower() == livro_norm.lower():
            return i
        if livro_norm.lower() in fonte.lower() or fonte.lower() in livro_norm.lower():
            return i
    return 999


def escolher_fonte_prioritaria(livro1: str | None, livro2: str | None) -> str | None:
    """
    Dado dois livros, retorna o que tem maior prioridade (menor índice).
    Retorna o primeiro se empate ou ambos vazios.
    """
    p1 = obter_prioridade_fonte(livro1)
    p2 = obter_prioridade_fonte(livro2)
    if p1 <= p2:
        return livro1 or livro2
    return livro2 or livro1
