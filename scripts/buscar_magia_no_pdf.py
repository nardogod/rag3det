"""
Teste rápido: verifica se o texto da magia existe no PDF raw.
Uso:
  python scripts/buscar_magia_no_pdf.py "Brilho de Espírito"
  python scripts/buscar_magia_no_pdf.py  # busca as 13 não encontradas em todos os PDFs
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pdfplumber


def buscar_magia_no_pdf(caminho_pdf: Path, nome_magia: str) -> list[tuple[int, str]]:
    """Retorna lista de (página, trecho) onde a magia aparece."""
    resultados = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            texto = page.extract_text()
            if texto and nome_magia.lower() in texto.lower():
                resultados.append((i + 1, texto[:800]))
    return resultados


def main():
    from src.config import paths

    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        print(f"Diretório não encontrado: {pdf_dir}")
        return

    pdfs = sorted(pdf_dir.rglob("*.pdf"))

    if len(sys.argv) > 1:
        magias = [" ".join(sys.argv[1:])]
    else:
        # Carrega as 13 não encontradas
        path_nao = Path("data/processed/magias/magias_nao_encontradas.txt")
        if not path_nao.exists():
            print("Passe o nome da magia: python scripts/buscar_magia_no_pdf.py 'Brilho de Espírito'")
            return
        magias = []
        for line in path_nao.read_text(encoding="utf-8").strip().splitlines():
            if ". " in line:
                _, nome = line.split(". ", 1)
                magias.append(nome)

    for nome_magia in magias:
        print(f"\n{'='*60}")
        print(f"Buscando: {nome_magia}")
        print("=" * 60)
        encontrou = False
        for pdf_path in pdfs:
            resultados = buscar_magia_no_pdf(pdf_path, nome_magia)
            if resultados:
                encontrou = True
                print(f"\n  {pdf_path.name}:")
                for pagina, trecho in resultados:
                    print(f"    Página {pagina}:")
                    print(f"    {trecho[:400]}...")
                    print("    ---")
        if not encontrou:
            print("  (não encontrado em nenhum PDF)")


if __name__ == "__main__":
    main()
