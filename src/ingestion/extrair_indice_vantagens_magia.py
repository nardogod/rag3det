"""
Camada 1: Extração do Índice de Vantagens e Desvantagens do Manual da Magia.
Extrai nomes do capítulo "NOVAS VANTAGENS E DESVANTAGENS" (~pg. 95).
Padrões: "Nome (X pontos)", "Nome (especial)", "Nome (X ponto cada)".
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


def _encontrar_pdf_manual_magia(pdf_dir: Path) -> Path | None:
    """Manual da Magia (sem Alpha) - prioridade para o que tem Objetos Mágicos completo."""
    if not pdf_dir.exists():
        return None
    pdfs = list(pdf_dir.rglob("*.pdf"))
    # Prioriza manual-da-magia sem "alpha"
    manual = [p for p in pdfs if "manual" in p.name.lower() and "magia" in p.name.lower()]
    sem_alpha = [p for p in manual if "alpha" not in p.name.lower()]
    return sem_alpha[0] if sem_alpha else (manual[0] if manual else None)


def extrair_indice_vantagens_magia(
    caminho_pdf: str | Path | None = None,
    paginas: List[int] | None = None,
) -> List[Tuple[str, str]]:
    """
    Extrai nomes e custos de Vantagens/Desvantagens do Manual da Magia.
    Retorna lista de (nome, custo) onde custo é "X pontos", "especial", etc.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (pip install pymupdf) necessário.")

    if caminho_pdf is None:
        from src.config import paths
        pdf_path = _encontrar_pdf_manual_magia(paths.source_pdf_dir)
        if pdf_path is None:
            raise FileNotFoundError(
                "PDF do Manual da Magia não encontrado. Configure SOURCE_PDF_DIR."
            )
        caminho_pdf = pdf_path
    else:
        caminho_pdf = Path(caminho_pdf)

    doc = fitz.open(str(caminho_pdf))
    resultados: List[Tuple[str, str]] = []
    seen: set[str] = set()

    # Páginas do capítulo (0-indexed). "NOVAS VANTAGENS E DESVANTAGENS" ~95
    if paginas is None:
        # Varre do pg 90 ao 120 (ajustar conforme necessário)
        paginas = list(range(89, min(121, len(doc))))

    padroes = [
        # "Arquimago (especial)" ou "Familiar (2 pontos)"
        re.compile(
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*\(\s*(especial|\d+\s*(?:a\s*\d+)?\s*pontos?(?:\s*cada)?)\s*\)",
            re.IGNORECASE,
        ),
        # "Nome (1 ponto)" ou "Nome (1 a 3 pontos)"
        re.compile(
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,40}?)\s*\(\s*(\d+(?:\s*a\s*\d+)?\s*pontos?)\s*\)",
            re.IGNORECASE,
        ),
        # "Nome (–1 ponto)" desvantagem
        re.compile(
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,40}?)\s*\(\s*([\-–]\d+\s*pontos?)\s*\)",
            re.IGNORECASE,
        ),
    ]

    try:
        for num_pag in paginas:
            if num_pag >= len(doc):
                continue
            texto = doc[num_pag].get_text()
            # Só processa páginas do capítulo Vantagens/Desvantagens
            if not any(
                x in texto
                for x in [
                    "Vantagem",
                    "Desvantagem",
                    "pontos)",
                    "Arquimago",
                    "Familiar",
                    "Elementalista",
                ]
            ):
                continue

            for padrao in padroes:
                for match in padrao.finditer(texto):
                    nome = match.group(1).strip()
                    custo = match.group(2).strip()
                    if "\n" in nome:
                        nome = nome.split("\n")[-1].strip()
                    if len(nome) < 3 or len(nome) > 50:
                        continue
                    if any(
                        x in nome.lower()
                        for x in [
                            "página", "capítulo", "parte", "lista", "seguir",
                            "uma forma", "para um", "para um ", "custo normal",
                            "ou grave", "e grave", "magia branca", "suave",
                        ]
                    ):
                        continue
                    # Fragmentos: começa com minúscula ou preposição
                    if nome[0].islower() or nome.lower().startswith(("para ", "uma ", "ou ", "e ")):
                        continue
                    key = nome.lower()
                    if key not in seen:
                        seen.add(key)
                        resultados.append((nome, custo))
    finally:
        doc.close()

    return resultados


def salvar_indice(
    itens: List[Tuple[str, str]],
    arquivo_saida: str | Path = "data/processed/vantagens_desvantagens/indice_vantagens_magia.txt",
) -> Path:
    """Salva o índice em arquivo."""
    path = Path(arquivo_saida)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i, (nome, custo) in enumerate(itens, 1):
            f.write(f"{i:03d}. {nome} | {custo}\n")
    print(f"[Camada 1] Índice de {len(itens)} vantagens/desvantagens salvo em {path}")
    return path


if __name__ == "__main__":
    try:
        itens = extrair_indice_vantagens_magia()
        if itens:
            salvar_indice(itens)
            for nome, custo in itens[:15]:
                print(f"  {nome} ({custo})")
            if len(itens) > 15:
                print(f"  ... e mais {len(itens) - 15}")
        else:
            print("Nenhuma vantagem/desvantagem encontrada.")
    except (ImportError, FileNotFoundError) as e:
        print(f"Erro: {e}")
