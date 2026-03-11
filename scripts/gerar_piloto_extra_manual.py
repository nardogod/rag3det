"""
Gera entradas PILOTO_EXTRA para todos os monstros do Manual dos Monstros.

Usa chunks.json para reconstruir o texto do manual e o extrator melhorado
para obter descrição, táticas e tesouro com boundaries corretos.

Uso: python scripts/gerar_piloto_extra_manual.py [--saida piloto_extra_manual.json]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.extrair_monstros_manual_format import extrair_monstros_manual_completo


def _reconstruir_texto_manual(chunks_path: Path) -> dict[int, str]:
    """Reconstrói texto por página do Manual dos Monstros a partir dos chunks."""
    if not chunks_path.exists():
        return {}
    data = json.loads(chunks_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        chunks = data
    elif isinstance(data, dict) and "chunks" in data:
        chunks = data["chunks"]
    else:
        chunks = list(data.values()) if isinstance(data, dict) else []

    manual_source = "3dt-alpha-manual-dos-monstros.pdf"
    # Agrupar chunks por (page, ordem) para preservar sequência
    paginas: dict[int, list[tuple[int, str]]] = {}
    for i, c in enumerate(chunks):
        if isinstance(c, dict):
            meta = c.get("metadata", {})
            source = meta.get("source") or ""
            if manual_source in source:
                pg = meta.get("page") or meta.get("page_label")
                if pg is not None:
                    try:
                        pg = int(pg)
                    except (ValueError, TypeError):
                        continue
                    content = c.get("page_content", "")
                    if content:
                        if pg not in paginas:
                            paginas[pg] = []
                        paginas[pg].append((i, content))
    # Concatenar chunks de cada página em ordem
    texto_por_pagina = {}
    for pg in sorted(paginas.keys()):
        partes = [p[1] for p in sorted(paginas[pg], key=lambda x: x[0])]
        texto_por_pagina[pg] = "\n\n".join(partes)
    return texto_por_pagina


def _monstro_para_piloto(m: dict) -> dict:
    """Converte monstro extraído em formato PILOTO_EXTRA (campos essenciais)."""
    out = {}
    if m.get("nome"):
        out["nome"] = m["nome"]
    if m.get("escala"):
        out["escala"] = m["escala"]
    if m.get("caracteristicas"):
        out["caracteristicas"] = m["caracteristicas"]
    if m.get("pv"):
        out["pv"] = str(m["pv"])
    if m.get("pm"):
        out["pm"] = str(m["pm"])
    if m.get("descricao"):
        out["descricao"] = m["descricao"][:4000]
    if m.get("taticas"):
        out["taticas"] = m["taticas"][:2000]
    if m.get("tesouro"):
        out["tesouro"] = m["tesouro"][:2000]
    if m.get("habilidades"):
        hab = m["habilidades"]
        if isinstance(hab, list):
            out["habilidades"] = [str(h)[:200] for h in hab if h]
        elif isinstance(hab, str):
            out["habilidades"] = [h.strip() for h in hab.split(";") if h.strip()][:20]
    out["fonte_referencia"] = "Manual dos Monstros 3D&T Alpha"
    return out


def main():
    base = Path(__file__).resolve().parent.parent
    chunks_path = base / "data" / "processed" / "chunks.json"
    saida = base / "data" / "processed" / "monstros" / "piloto_extra_manual.json"

    if "--saida" in sys.argv:
        idx = sys.argv.index("--saida")
        if idx + 1 < len(sys.argv):
            saida = Path(sys.argv[idx + 1])

    print("Reconstruindo texto do Manual dos Monstros...")
    texto_por_pagina = _reconstruir_texto_manual(chunks_path)
    if not texto_por_pagina:
        print("  [AVISO] Nenhum chunk do manual encontrado. Verifique data/processed/chunks.json")
        # Tenta extrair de monstros_extraidos como fallback
        extraidos = base / "data" / "processed" / "monstros" / "monstros_extraidos.json"
        if extraidos.exists():
            data = json.loads(extraidos.read_text(encoding="utf-8"))
            manual = [m for m in data if (m.get("livro") or "").lower() == "3dt alpha manual dos monstros"]
            print(f"  Usando {len(manual)} monstros de monstros_extraidos.json como fallback")
            piloto = {m["nome"]: _monstro_para_piloto(m) for m in manual if m.get("nome")}
        else:
            piloto = {}
    else:
        print(f"  {len(texto_por_pagina)} páginas encontradas")
        livro = "3dt alpha manual dos monstros"
        monstros = extrair_monstros_manual_completo(texto_por_pagina, livro)
        print(f"  {len(monstros)} monstros extraídos")
        piloto = {m["nome"]: _monstro_para_piloto(m) for m in monstros if m.get("nome")}

    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(piloto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Salvos em {saida}")


if __name__ == "__main__":
    main()
