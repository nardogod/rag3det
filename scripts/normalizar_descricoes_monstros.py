#!/usr/bin/env python3
"""
Normaliza descrições e campos de texto de todos os monstros de Arton.
Remove artefatos de OCR (semicolons, n1→n), corrige erros comuns e melhora legibilidade.

Entrada: data/processed/monstros/monstros_modelo_enriquecido.json
Saída: sobrescreve o mesmo arquivo (e sincroniza com frontend)

Executar: python scripts/normalizar_descricoes_monstros.py
"""
import json
import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from src.utils.normalizar_ocr import normalizar_texto_legivel, normalizar_ocr

MONSTROS_PATH = BASE / "data" / "processed" / "monstros" / "monstros_modelo_enriquecido.json"
FRONTEND_PATH = BASE / "frontend" / "src" / "data" / "monstros.json"

CAMPOS_TEXTO = [
    "descricao", "comportamento", "altura_tamanho", "peso", "habitat",
    "comportamento_dia_noite", "comportamento_combate", "habilidades_extra",
    "movimento", "origem_criacao", "uso_cultural", "vinculo_montaria",
    "veneno_detalhado", "resistencia_controle", "necessidades", "recuperacao_pv",
    "tesouro", "fraqueza",
]


def _normalizar_valor(v):
    """Aplica normalização a string ou retorna v inalterado."""
    if v is None:
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return v
        return normalizar_texto_legivel(s)
    return v


def _normalizar_lista(lst):
    """Normaliza cada string em uma lista."""
    if not lst or not isinstance(lst, list):
        return lst
    return [_normalizar_valor(str(x)) if isinstance(x, str) else x for x in lst]


def normalizar_monstro(m: dict) -> dict:
    """Aplica normalização a todos os campos de texto do monstro."""
    out = dict(m)
    for campo in CAMPOS_TEXTO:
        if campo in out and out[campo] is not None:
            out[campo] = _normalizar_valor(out[campo])
    if "habilidades" in out and out["habilidades"]:
        out["habilidades"] = [normalizar_ocr(str(h)) for h in out["habilidades"]]
    if "vulnerabilidades" in out and out["vulnerabilidades"]:
        out["vulnerabilidades"] = _normalizar_lista(out["vulnerabilidades"])
    if "fraquezas" in out and isinstance(out["fraquezas"], list) and out["fraquezas"]:
        out["fraquezas"] = _normalizar_lista(out["fraquezas"])
    if "imunidades" in out and out["imunidades"]:
        out["imunidades"] = _normalizar_lista(out["imunidades"])
    if "ataques_especificos" in out and out["ataques_especificos"]:
        for atq in out["ataques_especificos"]:
            if isinstance(atq, dict):
                for k in ("nome", "fa_fd", "dano", "observacao"):
                    if k in atq and atq[k]:
                        atq[k] = _normalizar_valor(str(atq[k]))
    return out


def main():
    if not MONSTROS_PATH.exists():
        print(f"Arquivo não encontrado: {MONSTROS_PATH}")
        print("Execute primeiro: python scripts/enriquecer_todos_monstros.py")
        return 1
    data = json.loads(MONSTROS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("Formato inesperado: esperado lista de monstros")
        return 1
    for i, monstro in enumerate(data):
        data[i] = normalizar_monstro(monstro)
    MONSTROS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Normalizados {len(data)} monstros em {MONSTROS_PATH}")
    if FRONTEND_PATH.exists():
        FRONTEND_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Sincronizado com {FRONTEND_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
