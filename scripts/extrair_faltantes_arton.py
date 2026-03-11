"""
Orquestrador: extrai criaturas faltantes do Livro de Arton.
Executa as 4 estratégias e mescla com o ecossistema principal.

Fluxo:
1. Identificar faltantes (identificar_faltantes_arton.py)
2. Extrair com extrator principal (daemon_extractor_dedicado)
3. Estratégias 1-4 (CON/FR/DEX, por índice, padrões relaxados, subvariantes)
4. Mesclar resultados (evitar duplicatas)
5. Substituir no ecossistema

Executar: python scripts/extrair_faltantes_arton.py
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


def _carregar_faltantes() -> list[str]:
    path = Path("data/processed/monstros/faltantes_arton.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("faltantes", [])


def _carregar_extraidos_arton() -> tuple[list[dict], set[str]]:
    """Retorna (lista de monstros Arton, set de nomes normalizados)."""
    path = Path("data/processed/monstros/monstros_extraidos.json")
    livro = "tormenta daemon guia de monstros de arton biblioteca elfica"
    if not path.exists():
        return [], set()
    data = json.loads(path.read_text(encoding="utf-8"))
    arton = [m for m in data if (m.get("livro") or "").lower() == livro]
    nomes = {m.get("nome", "").strip().lower().replace("-", " ") for m in arton}
    return arton, nomes


def _normalizar_nome(n: str) -> str:
    return n.strip().lower().replace("-", " ").replace("  ", " ")


def _nome_duplicado(nome: str, existentes: set[str]) -> bool:
    n = _normalizar_nome(nome)
    for ex in existentes:
        if n == _normalizar_nome(ex) or n in _normalizar_nome(ex) or _normalizar_nome(ex) in n:
            return True
    return False


def main() -> None:
    print("=== Extração de criaturas faltantes — Guia de Monstros de Arton ===\n")

    pdf_path = _encontrar_pdf_daemon()
    if not pdf_path:
        print("PDF do Guia Daemon não encontrado em SOURCE_PDF_DIR.")
        return

    # 1. Identificar faltantes
    print("1. Identificando faltantes...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/identificar_faltantes_arton.py"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print("   Executando identificar_faltantes manualmente...")
    faltantes = _carregar_faltantes()
    print(f"   Faltantes: {len(faltantes)}")

    # 2. Extrair texto do PDF
    try:
        from src.ingestion.pdf_text_extractor import extrair_texto_dual
    except ImportError:
        print("Instale: pip install pymupdf")
        return

    texto_por_pagina, _, _ = extrair_texto_dual(pdf_path)
    paginas_ord = sorted(texto_por_pagina.keys())
    partes = [texto_por_pagina[pg] for pg in paginas_ord]
    texto = "\n\n".join(partes)
    page_breaks = [0]
    acc = 0
    for p in partes:
        acc += len(p) + 2
        page_breaks.append(acc)

    livro = pdf_path.stem.replace("_", " ").replace("-", " ")
    from src.ingestion.daemon_stats_fallback import carregar_bestiario
    bestiario = carregar_bestiario()

    # 3. Extrator principal
    print("2. Executando extrator principal...")
    from src.ingestion.daemon_extractor_dedicado import extrair_monstros_texto_completo
    principais = extrair_monstros_texto_completo(texto_por_pagina, livro, bestiario)
    pos_extraidos = set()  # Posições de blocos já extraídos (vazio = dedup por nome)
    print(f"   Principais: {len(principais)}")

    # 4. Estratégias alternativas
    novos: list[dict] = []
    nomes_existentes = {m.get("nome", "") for m in principais}

    print("3. Estratégia CON/FR/DEX...")
    con_format = __import__(
        "src.ingestion.daemon_extractor_con_format",
        fromlist=["extrair_por_con_format"],
    ).extrair_por_con_format(texto, livro, bestiario, pos_extraidos, page_breaks)
    for m in con_format:
        if not _nome_duplicado(m["nome"], nomes_existentes):
            novos.append(m)
            nomes_existentes.add(m["nome"])
    print(f"   +{len([m for m in con_format if not _nome_duplicado(m['nome'], set())])} novos")

    print("4. Estratégia por índice...")
    por_indice = __import__(
        "src.ingestion.daemon_extractor_por_indice",
        fromlist=["extrair_por_indice"],
    ).extrair_por_indice(
        texto, livro, bestiario, faltantes, nomes_existentes, page_breaks
    )
    for m in por_indice:
        if not _nome_duplicado(m["nome"], nomes_existentes):
            novos.append(m)
            nomes_existentes.add(m["nome"])
    print(f"   +{len(por_indice)} candidatos")

    print("5. Estratégia padrões relaxados...")
    relaxed = __import__(
        "src.ingestion.daemon_extractor_patterns_relaxed",
        fromlist=["extrair_com_patterns_relaxed"],
    ).extrair_com_patterns_relaxed(
        texto, livro, bestiario, pos_extraidos, page_breaks
    )
    for m in relaxed:
        if not _nome_duplicado(m["nome"], nomes_existentes):
            novos.append(m)
            nomes_existentes.add(m["nome"])
    print(f"   +{len(relaxed)} candidatos")

    print("6. Estratégia subvariantes...")
    subvar = __import__(
        "src.ingestion.daemon_extractor_subvariantes",
        fromlist=["extrair_subvariantes"],
    ).extrair_subvariantes(
        texto, livro, bestiario, principais, page_breaks
    )
    for m in subvar:
        if not _nome_duplicado(m["nome"], nomes_existentes):
            novos.append(m)
            nomes_existentes.add(m["nome"])
    print(f"   +{len(subvar)} candidatos")

    # 5. Mesclar e limpar _fonte
    todos_arton = principais + novos
    for m in todos_arton:
        m.pop("_fonte", None)

    # 6. Substituir no ecossistema
    out_dir = Path("data/processed/monstros")
    main_path = out_dir / "monstros_extraidos.json"
    livro_key = "tormenta daemon guia de monstros de arton biblioteca elfica"

    if main_path.exists():
        existentes = json.loads(main_path.read_text(encoding="utf-8"))
        outros = [m for m in existentes if (m.get("livro") or "").lower() != livro_key]
        todos = outros + todos_arton
    else:
        todos = todos_arton

    with main_path.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    # Salvar também só Arton para referência
    daemon_path = out_dir / "monstros_daemon_extraidos.json"
    with daemon_path.open("w", encoding="utf-8") as f:
        json.dump(todos_arton, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Arton: {len(todos_arton)} monstros (principais + estratégias)")
    print(f"[OK] Total ecossistema: {len(todos)}")
    print(f"[OK] Salvos em {main_path} e {daemon_path}")
    print("\nPróximo: python scripts/varredura_completa_monstros.py (modelo enriquecido)")


if __name__ == "__main__":
    main()
