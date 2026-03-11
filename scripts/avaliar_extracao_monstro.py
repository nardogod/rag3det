"""
Avalia extração de monstro: compara extraído vs referência (livro) e reporta lacunas.

Fluxo:
  1. Extrair: monstros_extraidos.json (saída da varredura)
  2. Avaliar: compara campos extraídos vs referência
  3. Comparar: gera relatório livro vs extraído
  4. Preencher: PILOTO_EXTRA garante consistência (atualizar manualmente)

Uso:
  python scripts/avaliar_extracao_monstro.py Harpia
  python scripts/avaliar_extracao_monstro.py Harpia --referencia data/referencia_monstros/harpia.json
  python scripts/avaliar_extracao_monstro.py Harpia --referencia data/referencia_monstros/harpia.json --saida docs/comparacao_harpia.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Campos a comparar (ordem do formato de ficha)
CAMPOS_COMPARACAO = [
    "nome",
    "caracteristicas",
    "pv",
    "pm",
    "descricao",
    "comportamento",
    "altura_tamanho",
    "habitat",
    "comportamento_combate",
    "habilidades",
    "taticas",
    "tesouro",
    "imunidades",
    "fraquezas",
    "ataques_especificos",
    "movimento",
    "origem_criacao",
    "uso_cultural",
    "fonte_referencia",
]


def _normalizar_para_comparacao(val: object) -> str:
    """Normaliza valor para comparação (string)."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return json.dumps(val, sort_keys=True, ensure_ascii=False)
    if isinstance(val, list):
        return json.dumps(val, sort_keys=True, ensure_ascii=False)
    return str(val).strip()


def _valor_resumido(val: object, max_len: int = 120) -> str:
    """Retorna resumo do valor para exibição."""
    s = _normalizar_para_comparacao(val)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s if s else "—"


def carregar_extraido(nome: str, path: Path) -> dict | None:
    """Carrega monstro extraído (monstros_extraidos ou monstros_modelo_enriquecido)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        for m in data:
            if isinstance(m, dict) and m.get("nome", "").strip().lower() == nome.lower():
                return m
    return None


def carregar_referencia(nome: str, path: Path | None) -> dict | None:
    """Carrega referência do livro (JSON). Mapeia campos do JSON para schema de monstro."""
    if not path or not path.exists():
        return None
    ref = json.loads(path.read_text(encoding="utf-8"))
    if not ref:
        return None
    out = dict(ref)
    if "fonte" in out and "fonte_referencia" not in out:
        out["fonte_referencia"] = out.pop("fonte")
    return out


def carregar_piloto_extra(nome: str) -> dict | None:
    """Carrega PILOTO_EXTRA como referência."""
    from scripts.extrair_monstros_modelo_enriquecido import PILOTO_EXTRA

    return PILOTO_EXTRA.get(nome)


def comparar(extraido: dict, referencia: dict) -> list[tuple[str, str, str, str]]:
    """
    Compara extraído vs referência. Retorna lista de (campo, status, extraido, referencia).
    Status: OK | LACUNA | DIFERENTE | SOBRANDO
    """
    resultados: list[tuple[str, str, str, str]] = []
    ref_keys = set(referencia.keys())
    ext_keys = set(extraido.keys())

    for campo in CAMPOS_COMPARACAO:
        ext_val = extraido.get(campo)
        ref_val = referencia.get(campo)

        ext_s = _normalizar_para_comparacao(ext_val)
        ref_s = _normalizar_para_comparacao(ref_val)

        if not ref_s and not ext_s:
            continue
        if not ref_s:
            resultados.append((campo, "SOBRANDO", _valor_resumido(ext_val), "—"))
            continue
        if not ext_s:
            resultados.append((campo, "LACUNA", "—", _valor_resumido(ref_val)))
            continue
        if ext_s == ref_s:
            resultados.append((campo, "OK", _valor_resumido(ext_val), _valor_resumido(ref_val)))
        else:
            resultados.append((campo, "DIFERENTE", _valor_resumido(ext_val), _valor_resumido(ref_val)))

    return resultados


def gerar_relatorio(
    nome: str,
    extraido: dict | None,
    referencia: dict | None,
    comparacao: list[tuple[str, str, str, str]],
) -> str:
    """Gera relatório em Markdown."""
    linhas = [
        f"# Avaliação: {nome}",
        "",
        "## Resumo",
        "",
    ]
    if not extraido:
        linhas.append("- **Extraído:** não encontrado em monstros_extraidos.json")
    else:
        livro = extraido.get("livro", "?")
        linhas.append(f"- **Extraído:** {livro} (p. {extraido.get('pagina', '?')})")

    if not referencia:
        linhas.append("- **Referência:** não fornecida (use --referencia ou PILOTO_EXTRA)")
    else:
        fonte = referencia.get("fonte_referencia", referencia.get("fonte", "?"))
        linhas.append(f"- **Referência:** {fonte}")

    ok = sum(1 for _, s, _, _ in comparacao if s == "OK")
    lac = sum(1 for _, s, _, _ in comparacao if s == "LACUNA")
    dif = sum(1 for _, s, _, _ in comparacao if s == "DIFERENTE")
    linhas.append(f"- **Campos OK:** {ok} | **Lacunas:** {lac} | **Diferentes:** {dif}")
    linhas.append("")
    linhas.append("## Comparação por campo")
    linhas.append("")
    linhas.append("| Campo | Status | Extraído | Referência |")
    linhas.append("|-------|--------|----------|------------|")

    for campo, status, ext, ref in comparacao:
        ext_esc = ext.replace("|", "\\|")[:80]
        ref_esc = ref.replace("|", "\\|")[:80]
        linhas.append(f"| {campo} | {status} | {ext_esc} | {ref_esc} |")

    linhas.append("")
    linhas.append("## Recomendação")
    linhas.append("")
    if lac or dif:
        linhas.append("Atualizar PILOTO_EXTRA em `scripts/extrair_monstros_modelo_enriquecido.py` com os dados da referência para garantir consistência.")
    else:
        linhas.append("Extração alinhada com a referência.")
    linhas.append("")
    return "\n".join(linhas)


def main() -> None:
    # Garantir UTF-8 no stdout (Windows)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Avalia extração de monstro vs referência")
    parser.add_argument("monstro", help="Nome do monstro (ex.: Harpia)")
    parser.add_argument(
        "--referencia",
        type=Path,
        default=None,
        help="JSON de referência (livro). Ex.: data/referencia_monstros/harpia.json",
    )
    parser.add_argument(
        "--extraidos",
        type=Path,
        default=Path("data/processed/monstros/monstros_extraidos.json"),
        help="Caminho para monstros_extraidos.json",
    )
    parser.add_argument(
        "--modelo",
        type=Path,
        default=Path("data/processed/monstros/monstros_modelo_enriquecido.json"),
        help="Caminho para monstros_modelo_enriquecido.json",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=None,
        help="Salvar relatório em arquivo (ex.: docs/comparacao_harpia.md)",
    )
    args = parser.parse_args()

    nome = args.monstro.strip()
    if not nome:
        print("Erro: forneça o nome do monstro.")
        sys.exit(1)

    # 1. Carregar extraído (prioridade: modelo enriquecido, depois extraídos)
    extraido = carregar_extraido(nome, args.modelo)
    if not extraido:
        extraido = carregar_extraido(nome, args.extraidos)

    # 2. Carregar referência
    referencia: dict | None = None
    if args.referencia and args.referencia.exists():
        referencia = carregar_referencia(nome, args.referencia)
    if not referencia:
        referencia = carregar_piloto_extra(nome)

    if not referencia:
        print(f"Referência não encontrada para '{nome}'.")
        print("Use --referencia path/to/referencia.json ou adicione ao PILOTO_EXTRA.")
        sys.exit(1)

    # 3. Comparar
    comparacao = comparar(extraido or {}, referencia)

    # 4. Relatório
    relatorio = gerar_relatorio(nome, extraido, referencia, comparacao)
    print(relatorio)

    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(relatorio, encoding="utf-8")
        print(f"\n[OK] Relatório salvo em {args.saida}")


if __name__ == "__main__":
    main()
