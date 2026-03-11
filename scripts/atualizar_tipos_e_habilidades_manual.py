"""
Atualiza tipos e gera habilidades dos 284 monstros do Manual (revisado).
Usa APENAS os dados dos monstros (descricao, habilidades_extra, comportamento, taticas, tesouro).
Não consulta livros externos — as descrições completas estão nos próprios monstros.

1. Atualiza tipo em monstros.json
2. Extrai habilidades e descrições dos textos dos monstros

Executar: python scripts/atualizar_tipos_e_habilidades_manual.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Paths
MONSTROS_JSON = ROOT / "frontend" / "src" / "data" / "monstros.json"
HABILIDADES_OUT = ROOT / "frontend" / "src" / "data" / "habilidades_monstros.json"

LIVRO_MANUAL = "manual-dos-monstros-criaturas-fantasticas-revisado"

# Campos de texto dos monstros para extrair descrições (ordem de prioridade)
CAMPOS_TEXTO_MONSTRO = (
    "descricao",
    "habilidades_extra",
    "comportamento",
    "comportamento_combate",
    "taticas",
    "tesouro",
)


def obter_tipo_manual(nome: str) -> str:
    """Tipos conforme Manual: Construtos, Feras, Humanoides, Mortos-Vivos, Youkai."""
    from tipo_manual_monstros import obter_tipo_manual as _obter
    return _obter(nome.strip())


def normalizar_nome_habilidade(raw: str) -> str:
    """Extrai o nome base da habilidade (remove parênteses, variantes, etc.)."""
    # Ex: "Ataque Especial (Travar no Alvo: PdF; poderoso, preciso)" -> "Ataque Especial"
    # "Pontos de Magia Extras ×2" -> "Pontos de Magia Extras"
    s = raw.strip()
    if "(" in s:
        s = s.split("(")[0].strip()
    # Remove sufixos como ×2, x3, etc.
    s = re.sub(r"\s*[×x]\s*\d+\s*$", "", s, flags=re.I).strip()
    return s


def extrair_descricao_dos_monstros(
    nome_habilidade: str,
    monstros_com_habilidade: list[str],
    monstros_data: list[dict],
    buscar_em_todos: bool = False,
    todas_habilidades: set[str] | None = None,
) -> str | None:
    """
    Extrai descrição da habilidade das descrições/tesouro dos monstros.
    Padrões: "Nome: efeito", "Nome (X PEs): efeito", "Nome (efeito)".
    """
    nome_esc = re.escape(nome_habilidade)
    melhores: list[str] = []

    def _limpar(d: str) -> str:
        return re.sub(r"\s+", " ", d).strip()

    iterar_monstros = (
        monstros_data
        if buscar_em_todos
        else [m for m in monstros_data if m.get("nome") in monstros_com_habilidade]
    )
    for m in iterar_monstros:
        for campo in CAMPOS_TEXTO_MONSTRO:
            texto = m.get(campo)
            if not isinstance(texto, str):
                continue

            # Padrão 1: "Nome: texto" ou "Nome (X PEs): texto"
            p1 = re.compile(
                rf"{nome_esc}\s*(?:\(\d+\s*PEs?\))?\s*:\s*(.+?)(?=\s+[A-Za-zÀ-ú0-9][A-Za-zà-ú0-9\s\-']*:|\n\n|$)",
                re.IGNORECASE | re.DOTALL,
            )
            match = p1.search(texto)
            if match:
                desc = _limpar(match.group(1))
                # Evitar concatenar com texto de outro monstro (ex.: "...Barghest Um monstro...")
                if len(desc) > 350:
                    idx = desc.rfind(". ", 0, 350)
                    if idx > 100:
                        desc = desc[: idx + 1]
                if len(desc) > 5 and desc not in melhores:
                    melhores.append(desc)

            # Padrão 2: "Nome (efeito)" — descrição entre parênteses (não "X PEs")
            p2 = re.compile(
                rf"{nome_esc}\s+\(([^)]+)\)",
                re.IGNORECASE,
            )
            for m2 in p2.finditer(texto):
                conteudo = m2.group(1).strip()
                if re.match(r"^\d+\s*PEs?$", conteudo, re.I):
                    continue  # pular "20 PEs"
                desc = _limpar(conteudo)
                if len(desc) > 2 and desc not in melhores:
                    melhores.append(desc)

            # Padrão 3: "Nome. texto" — ponto como separador
            p3 = re.compile(
                rf"{nome_esc}\s*\.\s*(.+?)(?=\s+[A-Za-zÀ-ú][A-Za-zà-ú\s\-']*\.|\n\n|$)",
                re.IGNORECASE | re.DOTALL,
            )
            match = p3.search(texto)
            if match:
                desc = _limpar(match.group(1))
                if len(desc) > 5 and desc not in melhores:
                    melhores.append(desc)

            # Padrão 4: frase que contém o nome (ex.: "20 PMs presos em magias permanentes diversas.")
            # Ignorar quando a frase é só uma lista de habilidades (ex.: "A Grande Onda, Voz do Mar, Garras de Fera")
            if nome_habilidade in texto:
                idx = texto.lower().find(nome_habilidade.lower())
                if idx >= 0:
                    inicio = texto.rfind(".", 0, idx)
                    if inicio < 0:
                        inicio = texto.rfind(";", 0, idx)
                    if inicio < 0:
                        inicio = 0
                    else:
                        inicio += 1
                    fim = texto.find(".", idx)
                    if fim < 0:
                        fim = texto.find(";", idx)
                    if fim < 0:
                        fim = len(texto)
                    frase = texto[inicio:fim].strip()
                    if nome_habilidade.lower() in frase.lower() and len(frase) > len(nome_habilidade) + 3:
                        desc = _limpar(frase)
                        # Não usar se for só lista de nomes (várias vírgulas, sem : ou =)
                        if "," in desc and ":" not in desc and "=" not in desc and desc.count(",") >= 2:
                            pass  # provavelmente lista de habilidades
                        elif desc not in melhores:
                            melhores.append(desc)

    # Preferir descrição que descreve a habilidade correta (não outra)
    # Rejeitar quando começa com "X: " ou "X." ou "X (Y)." onde X é outra habilidade
    def _rejeitar_outra_habilidade(d: str, nome: str) -> bool:
        d = d.strip()
        if not d:
            return False
        # Rejeitar quando começa com outra habilidade conhecida (ex.: "Invisibilidade. Linguarudo: ..." para Aceleração)
        if todas_habilidades:
            d_lower = d.lower()
            for h in todas_habilidades:
                if h.lower() == nome.lower() or len(h) < 3:
                    continue
                # Começa com "Habilidade" seguido de . : ( + , ou espaço?
                h_lower = h.lower()
                if d_lower.startswith(h_lower):
                    restante = d_lower[len(h_lower):].lstrip()
                    if any(restante.startswith(c) for c in (".", ":", "(", "+", ",")):
                        return True
        if ":" in d:
            prefixo = d.split(":")[0].strip()
            if prefixo and prefixo.lower() != nome.lower() and len(prefixo) < 25:
                return True  # ex.: "Mutação: ..." para Anfíbio
        # Rejeitar "X (Y)." quando X é outra habilidade (ex.: "Clericato (Piscigeros)." para Anfíbio)
        if re.match(r"^[A-Za-zÀ-ú]+\s*\([^)]+\)\.?\s*$", d):
            prefixo = d.split("(")[0].strip().rstrip(".")
            if prefixo and prefixo.lower() != nome.lower():
                return True
        # Rejeitar fragmentos de efeito de item (ex.: "com Aceleração = H+2 fuga..." para Aceleração)
        if d.lower().startswith("com ") and len(d) < 80:
            return True
        # Rejeitar fragmentos curtos de item (ex.: "Aceleração sem gastar PMs")
        if len(d) < 45 and ("sem gastar" in d.lower() or "sem custo" in d.lower()):
            return True
        # Rejeitar frases táticas que começam com "Então," ou "gasta... para X e"
        if d.strip().lower().startswith("então,") or d.strip().lower().startswith("então "):
            return True
        return False

    def _score(d: str) -> tuple:
        tem_regras = ("=" in d or "teste" in d or "PMs" in d or "PVs" in d or "dano" in d.lower())
        # Preferir definições de vantagem (recebe, consome, Vantagem) sobre táticas (aproximar, atacar)
        eh_definicao = any(
            k in d.lower() for k in ("recebe", "consome", "vantagem", "impon", "impose", "gasta")
        )
        eh_tatica = any(k in d.lower() for k in ("aproximar, atacar", "perseguem até"))
        return (not eh_tatica, eh_definicao, tem_regras, len(d), d)

    filtradas = [
        d for d in melhores
        if not _rejeitar_outra_habilidade(d, nome_habilidade)
        and (len(d) > 15 or "=" in d or "teste" in d)
    ]
    if not filtradas:
        filtradas = [d for d in melhores if not _rejeitar_outra_habilidade(d, nome_habilidade) and len(d) > 8]
    candidatas = filtradas if filtradas else melhores
    return max(candidatas, key=_score) if candidatas else None


def obter_descricao_fallback(
    nome_habilidade: str,
    monstros_com_habilidade: list[str],
    monstros_data: list[dict],
) -> str | None:
    """
    Fallback: usa descricao do monstro quando a habilidade é mencionada.
    As descrições completas estão nos próprios monstros.
    """
    for nome_monstro in monstros_com_habilidade:
        m = next((x for x in monstros_data if x.get("nome") == nome_monstro), None)
        if not m:
            continue
        desc = m.get("descricao")
        if not isinstance(desc, str) or len(desc) < 30:
            continue
        # Só usar se a habilidade é mencionada na descrição
        if nome_habilidade.lower() in desc.lower():
            return re.sub(r"\s+", " ", desc).strip()
        # Habilidades únicas (1 monstro): usar descricao completa do monstro
        if len(monstros_com_habilidade) == 1:
            return re.sub(r"\s+", " ", desc).strip()
    return None


def main() -> None:
    monstros = json.loads(MONSTROS_JSON.read_text(encoding="utf-8"))

    # 1. Atualizar tipos dos 284 monstros do Manual
    for m in monstros:
        if m.get("livro") == LIVRO_MANUAL:
            m["tipo"] = obter_tipo_manual(m.get("nome", ""))
    count_manual = sum(1 for m in monstros if m.get("livro") == LIVRO_MANUAL)

    # 2. Extrair habilidades únicas dos 284 monstros (apenas array habilidades)
    habilidades_raw: set[str] = set()
    habilidade_por_monstro: dict[str, list[str]] = {}

    def _eh_habilidade_valida(s: str) -> bool:
        s = s.strip()
        if not s or len(s) < 2:
            return False
        if s.startswith("(") or s.startswith(")") or s.endswith("("):
            return False
        if re.match(r"^[\d)x]+$", s):  # só números/pontuação
            return False
        return True

    hab_por_monstro_todos: dict[str, list[str]] = {}  # para extração (todos os livros)
    for m in monstros:
        nome_monstro = m.get("nome", "")
        habs: list[str] = []
        for h in m.get("habilidades") or []:
            if isinstance(h, str) and _eh_habilidade_valida(h):
                h = h.strip()
                habs.append(h)
        if habs:
            hab_por_monstro_todos[nome_monstro] = habs
            if m.get("livro") == LIVRO_MANUAL:
                habilidade_por_monstro[nome_monstro] = habs
                for h in habs:
                    habilidades_raw.add(h)

    # 3. Montar habilidades_monstros.json
    habilidades_map: dict[str, dict] = {}  # nome_normalizado -> { descricao, fonte, monstros, nomes_originais }

    monstros_manual = [m for m in monstros if m.get("livro") == LIVRO_MANUAL]
    monstros_todos = monstros

    # Conjunto de todas as habilidades (para rejeitar descrições que começam com outra)
    todas_habilidades_set: set[str] = set()
    for habs in habilidade_por_monstro.values():
        for h in habs:
            n = normalizar_nome_habilidade(h)
            if n:
                todas_habilidades_set.add(n)

    for raw in sorted(habilidades_raw):
        nome_base = normalizar_nome_habilidade(raw)
        if not nome_base:
            continue
        monstros_com = [nome for nome, habs in habilidade_por_monstro.items() if raw in habs]
        monstros_com_todos = [nome for nome, habs in hab_por_monstro_todos.items() if raw in habs]
        descricao = None
        fonte = "Manual dos Monstros: Criaturas Fantásticas (revisado)"

        # 1. Extrair das descrições — APENAS dos 284 monstros do Manual (concentro nos 284)
        if monstros_com:
            descricao = extrair_descricao_dos_monstros(
                nome_base, monstros_com, monstros_manual, todas_habilidades=todas_habilidades_set
            )
        # 1b. Se não achou boa descrição, buscar em TODOS os monstros (ex.: Anfíbio no Avatar/Bestiário)
        if not descricao or (descricao and len(descricao) < 50):
            desc_todos = extrair_descricao_dos_monstros(
                nome_base, monstros_com_todos or [""], monstros_todos,
                buscar_em_todos=True, todas_habilidades=todas_habilidades_set
            )
            if desc_todos and (not descricao or len(desc_todos) > len(descricao)):
                descricao = desc_todos

        # 2. Se a variante raw já tem "Nome: efeito", usar o efeito
        if not descricao and ":" in raw and raw.strip().startswith(nome_base):
            parte = raw.split(":", 1)[1].strip()
            if len(parte) > 5 and not parte.lower().startswith("http"):
                descricao = parte

        # 3. Fallback: usar descricao completa do monstro (textos completos enviados)
        # Também quando descricao extraída é muito curta/insuficiente (ex.: "apenas animais" para 1ª Lei de Asimov)
        if not descricao and monstros_com:
            descricao = obter_descricao_fallback(nome_base, monstros_com, monstros_todos)
        elif descricao and len(descricao) < 40 and len(monstros_com) == 1:
            fallback = obter_descricao_fallback(nome_base, monstros_com, monstros_todos)
            if fallback and len(fallback) > len(descricao):
                descricao = fallback

        if nome_base not in habilidades_map:
            habilidades_map[nome_base] = {
                "nome": nome_base,
                "descricao": descricao or "Descrição não extraída. Ver ficha do monstro.",
                "fonte": fonte,
                "monstros": monstros_com,
                "variantes": [],
            }
        if raw != nome_base and raw not in habilidades_map[nome_base]["variantes"]:
            habilidades_map[nome_base]["variantes"].append(raw)

    # Ordenar por nome, filtrar vazios
    habilidades_list = [
        x for x in sorted(habilidades_map.values(), key=lambda x: x["nome"].lower())
        if x["nome"]
    ]

    # 4. Salvar
    MONSTROS_JSON.write_text(json.dumps(monstros, ensure_ascii=False, indent=2), encoding="utf-8")
    HABILIDADES_OUT.parent.mkdir(parents=True, exist_ok=True)
    HABILIDADES_OUT.write_text(json.dumps(habilidades_list, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Tipos atualizados: {count_manual} monstros do Manual")
    print(f"[OK] Habilidades extraídas: {len(habilidades_list)} únicas")
    print(f"[OK] {MONSTROS_JSON.name} e {HABILIDADES_OUT.name} salvos.")


if __name__ == "__main__":
    main()
