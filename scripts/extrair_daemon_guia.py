"""
Extrator DEDICADO do Guia de Monstros de Arton (Daemon Editora).
Usa código específico para este livro; a descrição é crucial para tabulação.
Executar: python scripts/extrair_daemon_guia.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import paths


def _encontrar_pdf_daemon() -> Path | None:
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        return None
    for p in pdf_dir.rglob("*.pdf"):
        if "daemon" in p.name.lower() and "guia" in p.name.lower():
            return p
    return None


def _substituir_daemon_no_ecossistema(daemon_monstros: list[dict]) -> tuple[int, int]:
    """
    SUBSTITUI monstros do Guia Daemon no ecossistema (não mescla).
    Remove entradas antigas do mesmo livro e adiciona as novas.
    Retorna (total_final, quantidade_daemon).
    """
    out_dir = Path("data/processed/monstros")
    main_path = out_dir / "monstros_extraidos.json"

    livro_daemon = "tormenta daemon guia de monstros de arton biblioteca elfica"

    if not main_path.exists():
        with main_path.open("w", encoding="utf-8") as f:
            json.dump(daemon_monstros, f, ensure_ascii=False, indent=2)
        return len(daemon_monstros), len(daemon_monstros)

    existentes = json.loads(main_path.read_text(encoding="utf-8"))
    # Remover todos os monstros do Guia Daemon antigos
    outros = [m for m in existentes if (m.get("livro") or "").lower() != livro_daemon]
    # Adicionar os novos
    todos = outros + daemon_monstros

    with main_path.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    return len(todos), len(daemon_monstros)


def main() -> None:
    print("Extraindo monstros do Guia de Monstros de Arton (Daemon) — extrator dedicado...")
    pdf_path = _encontrar_pdf_daemon()
    if not pdf_path:
        print("PDF do Guia Daemon não encontrado em SOURCE_PDF_DIR.")
        return

    livro = pdf_path.stem.replace("_", " ").replace("-", " ")
    print(f"  Processando: {livro}")

    try:
        from src.ingestion.pdf_text_extractor import extrair_texto_dual
    except ImportError:
        print("Instale dependências: pip install pymupdf")
        return

    from src.ingestion.daemon_stats_fallback import carregar_bestiario
    from src.ingestion.daemon_extractor_dedicado import extrair_monstros_texto_completo

    texto_por_pagina, _, _ = extrair_texto_dual(pdf_path)
    bestiario = carregar_bestiario()

    # Varredura completa: concatena páginas para descrições longas (ex.: Minotauro)
    todos = extrair_monstros_texto_completo(texto_por_pagina, livro, bestiario)

    out_dir = Path("data/processed/monstros")
    out_dir.mkdir(parents=True, exist_ok=True)
    daemon_path = out_dir / "monstros_daemon_extraidos.json"

    with daemon_path.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(todos)} monstros extraídos em {daemon_path}")

    total, qtd_daemon = _substituir_daemon_no_ecossistema(todos)
    print(f"[OK] Guia Daemon: {qtd_daemon} monstros. Total no ecossistema: {total}")
    print("  Enriquecer descrições (comportamento, habitat, etc.): python scripts/enriquecer_descricao_monstros.py")


if __name__ == "__main__":
    main()
