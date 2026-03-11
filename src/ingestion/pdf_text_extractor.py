"""
Extrator de texto de PDF com suporte a PyMuPDF e pdfplumber.
pdfplumber costuma extrair melhor PDFs com layout complexo ou OCR.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator


def extrair_texto_pymupdf(caminho: Path) -> tuple[dict[int, str], str]:
    """Extrai texto com PyMuPDF. Retorna (texto_por_pagina, texto_completo)."""
    try:
        import fitz
    except ImportError:
        return {}, ""

    doc = fitz.open(str(caminho))
    texto_por_pagina = {}
    try:
        for i in range(len(doc)):
            pagina = doc[i]
            texto_por_pagina[i] = pagina.get_text()
    finally:
        doc.close()

    todas = "\n".join(texto_por_pagina.values())
    return texto_por_pagina, todas


def extrair_texto_pdfplumber(caminho: Path) -> tuple[dict[int, str], str]:
    """Extrai texto com pdfplumber. Retorna (texto_por_pagina, texto_completo)."""
    try:
        import pdfplumber
    except ImportError:
        return {}, ""

    texto_por_pagina = {}
    with pdfplumber.open(caminho) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            texto_por_pagina[i] = t or ""

    todas = "\n".join(texto_por_pagina.values())
    return texto_por_pagina, todas


def extrair_texto_dual(
    caminho: Path, preferir_pdfplumber: bool = False
) -> tuple[dict[int, str], str, str]:
    """
    Extrai texto usando ambos os métodos.
    Retorna (texto_por_pagina, texto_completo, metodo_usado).
    Se preferir_pdfplumber, tenta pdfplumber primeiro para PDFs problemáticos.
    """
    if preferir_pdfplumber:
        paginas, texto = extrair_texto_pdfplumber(caminho)
        if texto.strip():
            return paginas, texto, "pdfplumber"
        paginas, texto = extrair_texto_pymupdf(caminho)
        return paginas, texto, "pymupdf"

    paginas, texto = extrair_texto_pymupdf(caminho)
    if texto.strip():
        return paginas, texto, "pymupdf"
    paginas, texto = extrair_texto_pdfplumber(caminho)
    return paginas, texto, "pdfplumber"
