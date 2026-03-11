"""
Verifica se o Manual 3D&T Turbinado Digital contém capítulo ou conteúdo de magias.
Executar: python scripts/verificar_magias_turbinado.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import paths


def main() -> None:
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        print(f"Diretório de PDFs não existe: {pdf_dir}")
        return

    # Buscar Manual Turbinado Digital
    turbinado = [
        p for p in pdf_dir.rglob("*.pdf")
        if "turbinado" in p.name.lower() and "digital" in p.name.lower()
    ]
    if not turbinado:
        turbinado = [p for p in pdf_dir.rglob("*.pdf") if "turbinado" in p.name.lower()]

    if not turbinado:
        print("PDF do Manual Turbinado não encontrado.")
        return

    pdf_path = turbinado[0]
    print(f"Analisando: {pdf_path.name}")

    try:
        from src.ingestion.pdf_text_extractor import extrair_texto_dual
        texto_por_pagina, _, texto_completo = extrair_texto_dual(pdf_path)
    except ImportError:
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            texto_completo = ""
            texto_por_pagina = {}
            for i, page in enumerate(doc):
                t = page.get_text()
                texto_por_pagina[i] = t
                texto_completo += t + "\n"
            doc.close()
        except Exception as e:
            print(f"Erro ao abrir PDF: {e}")
            return

    # Indicadores de capítulo de magias
    indicadores = [
        "magia", "Bola de Fogo", "Invisibilidade", "Cura", "lista de magias",
        "capítulo.*magia", "magias do", "escola", "Focus", "PMs"
    ]
    texto_lower = texto_completo.lower()
    total_chars = len(texto_completo)

    print(f"\nTotal de páginas: {len(texto_por_pagina)}")
    print(f"Total de caracteres: {total_chars}")

    encontrados = []
    for ind in indicadores:
        if ind.lower() in texto_lower:
            encontrados.append(ind)

    print(f"\nIndicadores encontrados: {encontrados}")

    # Contar ocorrências de termos mágicos
    termos = ["magia", "Bola de Fogo", "Invisibilidade", "Cura", "Focus", "PMs", "conjurar"]
    for termo in termos:
        count = texto_lower.count(termo.lower())
        if count > 0:
            print(f"  '{termo}': {count} ocorrências")

    if "magia" in texto_lower and total_chars > 10000:
        print("\n[CONCLUSÃO] O Manual Turbinado parece conter conteúdo relacionado a magias.")
        print("Recomendação: Incluir na extração de magias (extrair_magias_agressivo) ou")
        print("verificar índice/capítulo específico de magias.")
    else:
        print("\n[CONCLUSÃO] Pouco ou nenhum conteúdo de magias detectado.")
        print("O Manual Turbinado pode não ter capítulo dedicado de magias;")
        print("magias básicas podem estar no Manual da Magia ou Alpha.")


if __name__ == "__main__":
    main()
