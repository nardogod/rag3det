"""
Camada 2: Extração de magias por delimitador.
Usa o PDF diretamente e extrai blocos completos (Nome + Escola + Custo + Alcance + Duração + Descrição).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


@dataclass
class Magia:
    """Bloco de magia extraído do PDF."""
    nome: str
    escola: str
    custo: str
    alcance: str
    duracao: str
    descricao: str
    pagina: int
    texto_original: str


def _encontrar_pdf_manual_magia(pdf_dir: Path) -> Path | None:
    """Localiza o PDF do Manual da Magia."""
    if not pdf_dir.exists():
        return None
    for f in pdf_dir.rglob("*.pdf"):
        if "magia" in f.name.lower():
            return f
    return None


def extrair_magias_por_delimitador(
    caminho_pdf: str | Path | None = None,
    paginas_inicio: int = 5,
    paginas_fim: int | None = None,
) -> List[Magia]:
    """
    Extrai magias usando delimitadores lógicos.
    Cada magia começa com Nome + "Escola:" e termina antes da próxima magia.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (pip install pymupdf) necessário.")

    if caminho_pdf is None:
        from src.config import paths
        pdf_path = _encontrar_pdf_manual_magia(paths.source_pdf_dir)
        if pdf_path is None:
            raise FileNotFoundError("PDF do Manual da Magia não encontrado.")
        caminho_pdf = pdf_path
    else:
        caminho_pdf = Path(caminho_pdf)

    doc = fitz.open(str(caminho_pdf))
    magias: List[Magia] = []

    # Padrão: Nome (opcional "por Autor") + Escola:
    padrao_inicio = re.compile(
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*\n"
        r"(?:por\s+[^\n]+\n\s*)?"
        r"Escola:\s*([^.]+)\.",
        re.MULTILINE | re.IGNORECASE,
    )
    padrao_custo = re.compile(r"Custo:\s*([^.]+)\.", re.IGNORECASE)
    padrao_alcance = re.compile(r"Alcance:\s*([^;]+);", re.IGNORECASE)
    padrao_duracao = re.compile(r"Dura[çc][ãa]o:\s*([^.]+)\.", re.IGNORECASE)

    fim_paginas = paginas_fim if paginas_fim is not None else len(doc)
    paginas_range = range(paginas_inicio, min(fim_paginas, len(doc)))

    try:
        for num_pagina in paginas_range:
            pagina = doc[num_pagina]
            texto = pagina.get_text()

            matches = list(padrao_inicio.finditer(texto))

            for i, match in enumerate(matches):
                nome = match.group(1).strip()
                escola = match.group(2).strip()
                if "\n" in nome:
                    nome = nome.split("\n")[-1].strip()

                inicio = match.start()
                fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
                bloco = texto[inicio:fim]

                custo_m = padrao_custo.search(bloco)
                alcance_m = padrao_alcance.search(bloco)
                duracao_m = padrao_duracao.search(bloco)

                descricao = ""
                if duracao_m:
                    descricao = bloco[duracao_m.end() :].strip()
                elif alcance_m:
                    descricao = bloco[alcance_m.end() :].strip()

                magias.append(
                    Magia(
                        nome=nome,
                        escola=escola,
                        custo=custo_m.group(1).strip() if custo_m else "",
                        alcance=alcance_m.group(1).strip() if alcance_m else "",
                        duracao=duracao_m.group(1).strip() if duracao_m else "",
                        descricao=descricao,
                        pagina=num_pagina + 1,
                        texto_original=bloco,
                    )
                )
    finally:
        doc.close()

    print(f"[Camada 2] Extraídas {len(magias)} magias por delimitador")
    return magias
