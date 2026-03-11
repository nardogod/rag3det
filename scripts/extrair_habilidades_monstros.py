"""
Extrai habilidades únicas dos 284 monstros do Manual dos Monstros (revisado)
e cruza com vantagens_turbinado.json e magias_3dt.json para obter descrições.

Executar: python scripts/extrair_habilidades_monstros.py
Saída: frontend/src/data/habilidades_monstros.json
"""

import json
import re
from pathlib import Path

LIVRO_MANUAL = "manual-dos-monstros-criaturas-fantasticas-revisado"


def normalizar_nome(nome: str) -> str:
    """Extrai o nome base da habilidade (remove parênteses e detalhes)."""
    match = re.match(r"^([^(]+)", nome.strip())
    if match:
        return match.group(1).strip()
    return nome.strip()


def eh_habilidade_valida(nome: str) -> bool:
    """Filtra fragmentos e ruído."""
    if not nome or len(nome) < 2:
        return False
    if nome[0] in "()0123456789":
        return False
    if nome.endswith(")") and "(" not in nome:
        return False
    if re.match(r"^\d+", nome):  # começa com número
        return False
    if re.match(r"^(até|em|por|para|que|com|de|da|do)\s", nome, re.I):  # fragmento
        return False
    if len(nome) > 80:  # provável bloco de texto
        return False
    return True


def extrair_habilidades(monstros: list[dict]) -> dict[str, list[str]]:
    """Retorna {habilidade_normalizada: [monstros que a possuem]}."""
    habilidades: dict[str, set[str]] = {}
    for m in monstros:
        if m.get("livro") != LIVRO_MANUAL:
            continue
        nome_monstro = m.get("nome", "")
        for campo in ("habilidades", "habilidades_extra"):
            val = m.get(campo)
            if not val:
                continue
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        base = normalizar_nome(item)
                        if eh_habilidade_valida(base):
                            habilidades.setdefault(base, set()).add(nome_monstro)
            elif isinstance(val, str):
                for part in re.split(r"\.\s+|\s*;\s*|\s*,\s*", val):
                    base = normalizar_nome(part)
                    if eh_habilidade_valida(base):
                        habilidades.setdefault(base, set()).add(nome_monstro)
    return {k: sorted(list(v)) for k, v in habilidades.items()}


def buscar_descricao(nome: str, vantagens: list[dict], magias: list[dict]) -> dict | None:
    """Busca efeito em vantagens ou magias (match exato ou por início)."""
    nome_lower = nome.lower()
    for v in vantagens:
        if v.get("nome", "").lower() == nome_lower:
            return {"fonte": "vantagem", "livro": v.get("livro", ""), "pagina": v.get("pagina"), "efeito": v.get("efeito", "")}
    for m in magias:
        if m.get("nome", "").lower() == nome_lower:
            return {"fonte": "magia", "livro": "Manual 3D&T Alpha", "pagina": m.get("pagina"), "efeito": m.get("descricao", "")}
    # Match parcial (nome da vantagem contém ou é contido)
    for v in vantagens:
        vn = v.get("nome", "").lower()
        if vn in nome_lower or nome_lower in vn:
            return {"fonte": "vantagem", "livro": v.get("livro", ""), "pagina": v.get("pagina"), "efeito": v.get("efeito", "")}
    return None


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    monstros_path = base / "frontend" / "src" / "data" / "monstros.json"
    vantagens_path = base / "frontend" / "src" / "data" / "vantagens_turbinado.json"
    magias_path = base / "frontend" / "src" / "data" / "magias_3dt.json"
    out_path = base / "frontend" / "src" / "data" / "habilidades_monstros.json"

    monstros = json.loads(monstros_path.read_text(encoding="utf-8"))
    vantagens = json.loads(vantagens_path.read_text(encoding="utf-8"))
    magias = json.loads(magias_path.read_text(encoding="utf-8"))

    hab_por_monstro = extrair_habilidades(monstros)
    resultado = []
    for nome, monstros_list in sorted(hab_por_monstro.items(), key=lambda x: x[0].lower()):
        desc = buscar_descricao(nome, vantagens, magias)
        item = {
            "nome": nome,
            "monstros": monstros_list,
            "quantidade_monstros": len(monstros_list),
        }
        if desc:
            item["fonte"] = desc["fonte"]
            item["livro"] = desc.get("livro", "")
            item["pagina"] = desc.get("pagina")
            item["efeito"] = desc.get("efeito", "")
        else:
            item["fonte"] = "manual_monstros"
            item["livro"] = "Manual dos Monstros 3D&T Alpha"
            item["pagina"] = None
            item["efeito"] = "Ver descrição no Manual dos Monstros: Criaturas Fantásticas."
        resultado.append(item)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(resultado)} habilidades em {out_path}")


if __name__ == "__main__":
    main()
