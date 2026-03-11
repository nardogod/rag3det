"""
Enriquece TODOS os monstros do sistema.
Aplica varredura_completa (extrator automático + padrões ampliados) a cada monstro,
independente do livro de origem. Usa PILOTO_EXTRA e PILOTO_ARTON quando aplicável.

Executar: python scripts/enriquecer_todos_monstros.py
Saída: data/processed/monstros/monstros_modelo_enriquecido.json (todos os monstros)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.enriquecer_descricao_monstro import PILOTO_ARTON
from src.ingestion.varredura_extrator_completo import varredura_completa
from src.utils.normalizar_ocr import normalizar_ocr

# Dados completos manuais (prioridade máxima)
from scripts.extrair_monstros_modelo_enriquecido import PILOTO_EXTRA, CAMPOS_MODELO

# Alias: monstros que usam dados de outro (ex.: "Dragões Bicéfalos" → "Dragão Bicéfalo")
PILOTO_ALIAS: dict[str, str] = {
    "Dragões Bicéfalos": "Dragão Bicéfalo",
}

# Campos de texto que podem conter erros OCR (extraídos de PDFs)
_CAMPOS_TEXTO_OCR = [
    "descricao", "comportamento", "comportamento_dia_noite", "comportamento_combate",
    "habitat", "altura_tamanho", "peso", "movimento", "origem_criacao", "uso_cultural",
    "resistencia_controle", "necessidades", "recuperacao_pv", "habilidades_extra",
    "taticas", "tesouro",
]


def _completar_campos(base: dict[str, Any]) -> None:
    """Garante que todos os campos do modelo existam (None se vazio)."""
    for c in CAMPOS_MODELO:
        if c not in base:
            base[c] = None


def _aplicar_normalizacao_ocr(m: dict[str, Any]) -> None:
    """Corrige erros OCR em campos de texto do monstro (in-place)."""
    for k in _CAMPOS_TEXTO_OCR:
        v = m.get(k)
        if isinstance(v, str) and v.strip():
            m[k] = normalizar_ocr(v)
    for k in ("imunidades", "fraquezas"):
        lst = m.get(k)
        if isinstance(lst, list):
            m[k] = [normalizar_ocr(str(x)) if isinstance(x, str) else x for x in lst]


def enriquecer_monstro(m: dict[str, Any]) -> dict[str, Any]:
    """Aplica enriquecimento a um monstro. Retorna cópia enriquecida."""
    nome = (m.get("nome") or "").strip()
    base = dict(m)

    # Resolver alias (ex.: Dragões Bicéfalos → Dragão Bicéfalo)
    piloto_key = PILOTO_ALIAS.get(nome, nome)

    # 1. PILOTO_EXTRA (dados completos manuais)
    if piloto_key in PILOTO_EXTRA:
        for k, v in PILOTO_EXTRA[piloto_key].items():
            base[k] = v
        _completar_campos(base)
        base["fonte_referencia"] = "criatura ancestral"
        return base

    # 2. PILOTO_ARTON (dados parciais manuais)
    if nome in PILOTO_ARTON:
        for k, v in PILOTO_ARTON[nome].items():
            base[k] = v
        _completar_campos(base)
        base["fonte_referencia"] = "criatura ancestral"
        return base

    # 3. Extração automática da descrição (varredura completa)
    _completar_campos(base)
    auto = varredura_completa(base)
    for k, v in auto.items():
        if v is not None:
            base[k] = v
    base["fonte_referencia"] = base.get("fonte_referencia") or "criatura ancestral"
    _aplicar_normalizacao_ocr(base)
    return base


def main() -> None:
    out_dir = Path("data/processed/monstros")
    in_path = out_dir / "monstros_extraidos.json"
    out_path = out_dir / "monstros_modelo_enriquecido.json"

    if not in_path.exists():
        print(f"Arquivo não encontrado: {in_path}")
        print("Execute primeiro: python scripts/varredura_completa_monstros.py")
        return

    print("Enriquecendo todos os monstros do sistema...")
    data = json.loads(in_path.read_text(encoding="utf-8"))
    monstros = data if isinstance(data, list) else []

    # Deduplicar por (nome, livro) — manter primeira ocorrência
    seen: set[tuple[str, str]] = set()
    unicos: list[dict] = []
    for m in monstros:
        if not isinstance(m, dict) or not m.get("nome"):
            continue
        chave = (m.get("nome", "").strip(), (m.get("livro") or "").lower())
        if chave in seen:
            continue
        seen.add(chave)
        unicos.append(m)

    resultado: list[dict[str, Any]] = []
    total = len(unicos)
    for i, m in enumerate(unicos):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  Processando {i + 1}/{total}...")
        resultado.append(enriquecer_monstro(m))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    # Estatísticas
    com_comp = sum(1 for x in resultado if x.get("comportamento"))
    com_hab = sum(1 for x in resultado if x.get("habitat"))
    com_alt = sum(1 for x in resultado if x.get("altura_tamanho"))
    com_frq = sum(1 for x in resultado if x.get("fraquezas"))

    print(f"\n[OK] {len(resultado)} monstros enriquecidos em {out_path}")
    print(f"Campos preenchidos: comportamento={com_comp}, habitat={com_hab}, altura={com_alt}, fraquezas={com_frq}")


if __name__ == "__main__":
    main()
