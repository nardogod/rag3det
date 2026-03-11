"""
Camada 1: Extração do Índice Completo das 300 Magias.
Lê o PDF diretamente (PyMuPDF) nas páginas do índice para garantir os 300 nomes.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


def _encontrar_pdf_manual_magia(pdf_dir: Path) -> Path | None:
    """Localiza o PDF do Manual da Magia no diretório de fontes."""
    if not pdf_dir.exists():
        return None
    padroes = ["*manual*magia*.pdf", "*magia*alpha*.pdf", "*3dt*magia*.pdf"]
    for p in padroes:
        for f in pdf_dir.rglob(p):
            return f
    for f in pdf_dir.rglob("*.pdf"):
        if "magia" in f.name.lower():
            return f
    return None


def extrair_indice_magias(
    caminho_pdf: str | Path | None = None,
    paginas: List[int] | None = None,
) -> List[str]:
    """
    Extrai os 300 nomes do índice do Manual da Magia.
    Formato no PDF: "Nome (MM, pg. 07). Nome2 ( M3D&T, pg. 84)."
    Ou numerado: "1. Bola de Fogo"
    """
    if fitz is None:
        raise ImportError("PyMuPDF (pip install pymupdf) necessário para extrair índice do PDF.")

    if caminho_pdf is None:
        from src.config import paths
        pdf_dir = paths.source_pdf_dir
        pdf_path = _encontrar_pdf_manual_magia(pdf_dir)
        if pdf_path is None:
            raise FileNotFoundError(
                f"PDF do Manual da Magia não encontrado em {pdf_dir}. "
                "Coloque o PDF em data/raw ou configure SOURCE_PDF_DIR."
            )
        caminho_pdf = pdf_path
    else:
        caminho_pdf = Path(caminho_pdf)
        if not caminho_pdf.exists():
            raise FileNotFoundError(f"PDF não encontrado: {caminho_pdf}")

    if paginas is None:
        # Páginas do índice (0-indexed). Lista Completa está em ~29-31 (page_label 30-32)
        paginas = [28, 29, 30, 31]

    doc = fitz.open(str(caminho_pdf))
    nomes: List[str] = []
    seen = set()

    # Padrão principal: "Nome (MM, pg. XX)." ou "Nome ( M3D&T, pg. XX)."
    re_indice = re.compile(
        r"([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9\s\-'\"\.\,\!\?]+?)\s*\(([^)]*?pg\.?\s*\d+[^)]*)\)",
        re.IGNORECASE,
    )
    # Padrão numerado: "1. Nome da Magia" ou "127 - Portal para o Saber"
    re_numerado = re.compile(
        r"^\s*(\d{1,3})[.\-]\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)(?=\s*\d|$|\n)",
        re.MULTILINE,
    )

    try:
        for num_pagina in paginas:
            if num_pagina >= len(doc):
                continue
            pagina = doc[num_pagina]
            texto = pagina.get_text()

            # Formato "Nome (ref)."
            for match in re_indice.finditer(texto):
                nome = match.group(1).strip()
                ref = match.group(2)
                if "\n" in nome:
                    nome = nome.split("\n")[-1].strip()
                if len(nome) < 2 or len(nome) > 60:
                    continue
                if any(x in nome.lower() for x in ["lista completa", "300 magias", "índice", "página"]):
                    continue
                if nome.lower() in ("lista", "completa", "alpha", "magias"):
                    continue
                # Filtra texto de descrição que vazou (ex: "gia é considerado como tendo a vantagem Vôo")
                n = nome.lower()
                if len(nome) > 25 and any(w in n for w in [" é ", " como ", " tendo ", " que ", " dessa ", " desta ", " são ", " foi ", " seja ", " pode ", " deve "]):
                    continue
                key = nome.lower()
                if key not in seen:
                    seen.add(key)
                    nomes.append(nome)

            # Formato numerado (fallback)
            for match in re_numerado.finditer(texto):
                nome = match.group(2).strip()
                if len(nome) < 3:
                    continue
                if any(x in nome.lower() for x in ["página", "manual", "magia", "capítulo", "lista"]):
                    continue
                key = nome.lower()
                if key not in seen:
                    seen.add(key)
                    nomes.append(nome)
    finally:
        doc.close()

    print(f"[Camada 1] Extraídos {len(nomes)} nomes do índice (págs. {paginas})")
    return nomes


def salvar_indice(
    nomes: List[str],
    arquivo_saida: str | Path = "data/processed/indice_magias_3dt.txt",
) -> Path:
    """Salva o índice em arquivo para referência."""
    path = Path(arquivo_saida)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i, nome in enumerate(nomes, 1):
            f.write(f"{i:03d}. {nome}\n")
    print(f"[Camada 1] Índice salvo em {path}")
    return path


if __name__ == "__main__":
    try:
        nomes = extrair_indice_magias()
        salvar_indice(nomes)
    except (ImportError, FileNotFoundError) as e:
        print(f"Erro: {e}")
