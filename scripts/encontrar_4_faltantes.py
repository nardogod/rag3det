"""
Analisa as páginas do índice para encontrar as magias faltantes (296 vs 300).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import fitz
except ImportError:
    fitz = None


def _encontrar_pdf() -> Path | None:
    """Localiza o PDF do Manual da Magia."""
    from src.config import paths
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        return None
    for f in pdf_dir.rglob("*.pdf"):
        if "magia" in f.name.lower():
            return f
    return None


def encontrar_faltantes_indice(caminho_pdf: str | Path | None = None) -> list[str]:
    """
    Analisa as páginas 29-33 para encontrar as magias faltantes no índice.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (pip install pymupdf) necessario.")

    if caminho_pdf is None:
        pdf_path = _encontrar_pdf()
        if pdf_path is None:
            raise FileNotFoundError(
                "PDF do Manual da Magia nao encontrado. "
                "Configure SOURCE_PDF_DIR ou passe o caminho."
            )
        caminho_pdf = pdf_path
    else:
        caminho_pdf = Path(caminho_pdf)
        if not caminho_pdf.exists():
            raise FileNotFoundError(f"PDF nao encontrado: {caminho_pdf}")

    doc = fitz.open(str(caminho_pdf))

    # Formato real do índice: "Nome (MM, pg. XX)." ou "Nome ( M3D&T, pg. XX)." - SEM números
    todas_magias_pdf: list[str] = []
    texto_indice = ""

    try:
        for num_pagina in [28, 29, 30, 31]:
            if num_pagina >= len(doc):
                continue

            pagina = doc[num_pagina]
            texto = pagina.get_text()
            texto_indice += "\n" + texto

            if num_pagina == 29:  # Página 30 tem o índice
                print(f"\n--- Amostra PAGINA 30 (indice) ---")
                print(texto[:800])

        # Extrair pelo formato real: "Nome (ref)."
        partes = re.split(r"\)\.\s*", texto_indice)
        for part in partes:
            if "(" not in part or "pg" not in part.lower():
                continue
            try:
                nome, _ = part.rsplit("(", 1)
                nome = nome.strip()
                if "\n" in nome:
                    nome = nome.split("\n")[-1].strip()
                if len(nome) < 2:
                    continue
                if any(x in nome.lower() for x in ["lista completa", "300 magias", "m3d&t:", "md:", "mm:"]):
                    continue
                if len(nome) > 25 and any(w in nome.lower() for w in [" é ", " como ", " tendo "]):
                    continue
                todas_magias_pdf.append(nome)
            except ValueError:
                continue

        # Carregar nosso índice atual
        indice_path = Path("data/processed/indice_magias_3dt.txt")
        nosso_indice: list[str] = []
        if indice_path.exists():
            for linha in indice_path.read_text(encoding="utf-8").splitlines():
                if ". " in linha:
                    nosso_indice.append(linha.split(". ", 1)[1].strip())

        # Deduplicar PDF (ordem de aparição)
        pdf_unicos = list(dict.fromkeys(todas_magias_pdf))
        nosso_set = set(n.lower() for n in nosso_indice)
        pdf_set = set(n.lower() for n in pdf_unicos)

        no_pdf_nao_temos = sorted(pdf_set - nosso_set)
        temos_nao_no_pdf = sorted(nosso_set - pdf_set)

    finally:
        doc.close()

    print(f"\n{'='*60}")
    print("RESULTADO")
    print(f"{'='*60}")
    print(f"Magias no PDF (indice): {len(pdf_unicos)}")
    print(f"Magias no nosso indice: {len(nosso_indice)}")
    print(f"No PDF mas nao no nosso: {len(no_pdf_nao_temos)}")
    if no_pdf_nao_temos:
        print(f"  -> {no_pdf_nao_temos[:20]}")
    print(f"No nosso mas nao no PDF: {len(temos_nao_no_pdf)}")
    if temos_nao_no_pdf:
        print(f"  -> {temos_nao_no_pdf[:20]}")

    # As "4 faltantes" podem ser: 300 - 296 = 4 que estão no PDF mas não extraímos
    return no_pdf_nao_temos


if __name__ == "__main__":
    pdf_arg = sys.argv[1] if len(sys.argv) > 1 else None
    faltantes = encontrar_faltantes_indice(pdf_arg)
    print(f"\nMagias no PDF que nao estao no nosso indice: {faltantes}")
