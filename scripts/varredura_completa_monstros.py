"""
Pipeline completo: varredura de monstros do Livro de Arton e Manual dos Monstros.
1. Re-extrai do PDF Guia Daemon com descrições completas (merge de páginas)
2. Extrai monstros do Manual dos Monstros (formato Nome, 61S; F7...; 35 PVs, 55 PMs)
3. Aplica modelo enriquecido com varredura completa (padrões ampliados)

Executar: python scripts/varredura_completa_monstros.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _extrair_manual_dos_monstros(pdf_dir: Path) -> list[dict]:
    """Extrai monstros do PDF Manual dos Monstros (formato 3D&T Alpha).
    Concatena páginas para que intros longos (ex.: Dragão Bestial) sejam capturados
    mesmo quando o stat block está em página diferente do intro."""
    manual_path = None
    for p in pdf_dir.rglob("*.pdf"):
        if "manual" in p.name.lower() and "monstros" in p.name.lower() and "daemon" not in p.name.lower():
            manual_path = p
            break
    if not manual_path:
        return []
    try:
        from src.ingestion.pdf_text_extractor import extrair_texto_dual
        from src.ingestion.extrair_monstros_manual_format import extrair_monstros_manual_completo
        livro = manual_path.stem.replace("_", " ").replace("-", " ")
        texto_por_pagina, _, _ = extrair_texto_dual(manual_path)
        monstros = extrair_monstros_manual_completo(texto_por_pagina, livro)
        return monstros
    except Exception as e:
        print(f"   Erro ao extrair Manual dos Monstros: {e}")
        return []


def main() -> None:
    print("=== Varredura completa de monstros (Arton + Manual dos Monstros) ===\n")

    # 1. Re-extrair do PDF com merge de páginas (descrições longas)
    try:
        from src.config import paths
        pdf_dir = paths.source_pdf_dir
        pdf_path = None
        if pdf_dir.exists():
            for p in pdf_dir.rglob("*.pdf"):
                if "daemon" in p.name.lower() and "guia" in p.name.lower():
                    pdf_path = p
                    break

        if pdf_path:
            out_dir = Path("data/processed/monstros")
            print("1. Re-extraindo do PDF (extrator + estratégias faltantes)...")
            from src.ingestion.pdf_text_extractor import extrair_texto_dual
            from src.ingestion.daemon_stats_fallback import carregar_bestiario
            from src.ingestion.daemon_extractor_dedicado import extrair_monstros_texto_completo
            from src.ingestion.daemon_extractor_con_format import extrair_por_con_format
            from src.ingestion.daemon_extractor_por_indice import extrair_por_indice, INDICE_ARTON
            from src.ingestion.daemon_extractor_patterns_relaxed import extrair_com_patterns_relaxed
            from src.ingestion.daemon_extractor_subvariantes import extrair_subvariantes

            livro = pdf_path.stem.replace("_", " ").replace("-", " ")
            texto_por_pagina, _, _ = extrair_texto_dual(pdf_path)
            bestiario = carregar_bestiario()
            paginas_ord = sorted(texto_por_pagina.keys())
            partes = [texto_por_pagina[pg] for pg in paginas_ord]
            texto = "\n\n".join(partes)
            page_breaks = [0]
            acc = 0
            for p in partes:
                acc += len(p) + 2
                page_breaks.append(acc)

            principais = extrair_monstros_texto_completo(texto_por_pagina, livro, bestiario)
            nomes_existentes = {m.get("nome", "") for m in principais}
            pos_extraidos = set()

            faltantes_path = out_dir / "faltantes_arton.json"
            faltantes = []
            if faltantes_path.exists():
                fd = json.loads(faltantes_path.read_text(encoding="utf-8"))
                faltantes = fd.get("faltantes", [])

            def _nome_dup(n, s): return any(n.lower().replace("-"," ") in ex.lower().replace("-"," ") or ex.lower().replace("-"," ") in n.lower().replace("-"," ") for ex in s)

            novos = []
            for m in extrair_por_con_format(texto, livro, bestiario, pos_extraidos, page_breaks):
                if not _nome_dup(m["nome"], nomes_existentes):
                    novos.append(m); nomes_existentes.add(m["nome"])
            for m in extrair_por_indice(texto, livro, bestiario, faltantes or list(INDICE_ARTON)[:50], nomes_existentes, page_breaks):
                if not _nome_dup(m["nome"], nomes_existentes):
                    novos.append(m); nomes_existentes.add(m["nome"])
            for m in extrair_com_patterns_relaxed(texto, livro, bestiario, pos_extraidos, page_breaks):
                if not _nome_dup(m["nome"], nomes_existentes):
                    novos.append(m); nomes_existentes.add(m["nome"])
            for m in extrair_subvariantes(texto, livro, bestiario, principais, page_breaks):
                if not _nome_dup(m["nome"], nomes_existentes):
                    novos.append(m); nomes_existentes.add(m["nome"])

            for m in principais + novos:
                m.pop("_fonte", None)
            daemon_monstros = principais + novos

            # Extrair Manual dos Monstros (formato Nome, 61S; 35 PVs, 55 PMs)
            manual_monstros = _extrair_manual_dos_monstros(pdf_dir)
            if manual_monstros:
                print(f"   {len(manual_monstros)} monstros Manual dos Monstros (PV/PM explícitos)")

            # Substituir no ecossistema
            main_path = out_dir / "monstros_extraidos.json"
            livro_daemon = "tormenta daemon guia de monstros de arton biblioteca elfica"
            livro_manual = "3dt alpha manual dos monstros"

            if main_path.exists():
                existentes = json.loads(main_path.read_text(encoding="utf-8"))
                outros = [m for m in existentes if (m.get("livro") or "").lower() != livro_daemon]
                # Substituir monstros do Manual pela extração nova (com intro de páginas adjacentes)
                if manual_monstros:
                    outros = [m for m in outros if (m.get("livro") or "").lower() != livro_manual]
                todos = outros + manual_monstros + daemon_monstros
            else:
                todos = manual_monstros + daemon_monstros

            out_dir.mkdir(parents=True, exist_ok=True)
            main_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"   {len(daemon_monstros)} monstros Daemon. Total: {len(todos)}")
        else:
            print("1. PDF do Guia Daemon não encontrado.")
            # Mesmo assim, tentar extrair Manual dos Monstros
            if pdf_dir.exists():
                manual_monstros = _extrair_manual_dos_monstros(pdf_dir)
                if manual_monstros:
                    out_dir = Path("data/processed/monstros")
                    main_path = out_dir / "monstros_extraidos.json"
                    existentes = json.loads(main_path.read_text(encoding="utf-8")) if main_path.exists() else []
                    todos = existentes + manual_monstros
                    out_dir.mkdir(parents=True, exist_ok=True)
                    main_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"   {len(manual_monstros)} monstros Manual dos Monstros adicionados. Total: {len(todos)}")
            else:
                print("   Usando monstros_extraidos.json existente.")
    except Exception as e:
        print(f"1. Erro na extração do PDF: {e}")
        print("   Continuando com dados existentes...")

    # 2. Aplicar modelo enriquecido com varredura completa
    print("\n2. Aplicando varredura completa (modelo enriquecido)...")
    from scripts.extrair_monstros_modelo_enriquecido import extrair_monstros_arton

    monstros = extrair_monstros_arton()
    out_dir = Path("data/processed/monstros")
    out_path = out_dir / "monstros_modelo_enriquecido.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(monstros, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"   {len(monstros)} monstros processados")
    print(f"\n[OK] Salvos em {out_path}")

    # Estatísticas
    com_comportamento = sum(1 for m in monstros if m.get("comportamento"))
    com_habitat = sum(1 for m in monstros if m.get("habitat"))
    com_altura = sum(1 for m in monstros if m.get("altura_tamanho"))
    com_fraquezas = sum(1 for m in monstros if m.get("fraquezas"))
    print(f"\nCampos preenchidos: comportamento={com_comportamento}, habitat={com_habitat}, altura={com_altura}, fraquezas={com_fraquezas}")


if __name__ == "__main__":
    main()
