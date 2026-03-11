"""
Extrator agressivo de Itens Mágicos 3D&T.
Busca cada item/poder do índice nos PDFs com múltiplas estratégias.
Estrutura: Tipo, Bônus, Custo (PEs), Efeito.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import fitz
except ImportError:
    fitz = None  # type: ignore

# PDFs que extraem melhor com pdfplumber
PDFS_PREFERIR_PDFPLUMBER = {"3dt-manual-revisado-ampliado-e-turbinado-biblioteca-elfica.pdf"}


@dataclass
class ItemMagicoExtraido:
    nome: str
    tipo: str | None = None  # arma, armadura, poção, etc.
    bonus: str | None = None  # F+2, A+1, etc.
    custo: str | None = None  # X PEs
    efeito: str | None = None
    pagina: int = 0
    confianca: float = 0.0
    fonte: str = ""
    livro: str = ""
    texto_bruto: str = ""


def _encontrar_pdfs() -> list[Path]:
    """Localiza todos os PDFs. Manual da Magia primeiro (tem cap. Objetos Mágicos)."""
    from src.config import paths
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {pdf_dir}")
    todos = sorted(pdf_dir.rglob("*.pdf"))
    if not todos:
        raise FileNotFoundError(f"Nenhum PDF encontrado em {pdf_dir}")
    # Prioriza Manual da Magia (anéis, poções, pergaminhos)
    # Manual SEM "alpha" primeiro: usa Preço: T$ (Tibares), formato mais completo
    manual_magia = [p for p in todos if "manual" in p.name.lower() and "magia" in p.name.lower()]
    sem_alpha = [p for p in manual_magia if "alpha" not in p.name.lower()]
    com_alpha = [p for p in manual_magia if "alpha" in p.name.lower()]
    outros = [p for p in todos if p not in manual_magia]
    return sorted(sem_alpha) + sorted(com_alpha) + outros


class ExtratorItensMagicosAgressivo:
    """Extrator que busca itens mágicos em PDFs com múltiplas estratégias."""

    def __init__(self, caminho_pdf: str | Path, nome_livro: str = ""):
        self.caminho = Path(caminho_pdf)
        self.nome_livro = nome_livro or self.caminho.name
        self.doc = None

        preferir_plumber = self.caminho.name in PDFS_PREFERIR_PDFPLUMBER
        try:
            from src.ingestion.pdf_text_extractor import extrair_texto_dual
            self.texto_por_pagina, self.todas_paginas, _ = extrair_texto_dual(
                self.caminho, preferir_pdfplumber=preferir_plumber
            )
        except Exception:
            if fitz is None:
                raise ImportError("PyMuPDF (pip install pymupdf) necessário.")
            self.doc = fitz.open(str(caminho_pdf))
            self.texto_por_pagina = {i: p.get_text() for i, p in enumerate(self.doc)}
            self.todas_paginas = "\n".join(self.texto_por_pagina.values())

    def close(self) -> None:
        if getattr(self, "doc", None) is not None:
            try:
                self.doc.close()
            except (ValueError, AttributeError):
                pass
            self.doc = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _extrair_campo(self, texto: str, padrao: str) -> str | None:
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extrair_campo_flexivel(self, texto: str, padroes: list[str]) -> str | None:
        for padrao in padroes:
            val = self._extrair_campo(texto, padrao)
            if val:
                return val
        return None

    def _qualidade_ocr_ruim(self, texto: str) -> bool:
        """Detecta artefatos de OCR (ex.: manual-revisado-ampliado). Rejeita blocos ilegíveis."""
        if not texto or len(texto) < 20:
            return False
        # Dígitos no meio de palavras (co1111Jm, peqiamlnho)
        if re.search(r"[a-záàâãéêíóôõúç][0-9]{2,}[a-záàâãéêíóôõúç]",
                     texto, re.IGNORECASE):
            return True
        # Sequências estranhas: l!ll, QQ, 1111 fora de números
        if re.search(r"[a-z][!@#$%&*]{2,}|[0-9]{4,}[a-z]|[a-z]{2,}[0-9]{3,}",
                     texto, re.IGNORECASE):
            return True
        # Proporção de letras muito baixa (muitos caracteres estranhos)
        letras = sum(1 for c in texto if c.isalpha() or c in "áàâãéêíóôõúç ")
        if letras / max(len(texto), 1) < 0.6:
            return True
        return False

    def _tem_indicador_item(self, contexto: str) -> bool:
        """Verifica se o contexto parece bloco de item mágico."""
        return bool(
            re.search(r"Tipo:", contexto, re.IGNORECASE)
            or re.search(r"B[oô]nus:", contexto, re.IGNORECASE)
            or re.search(r"Pre[cç]o:", contexto, re.IGNORECASE)
            or re.search(r"T\$\s*\d+", contexto)
            or re.search(r"PEs?\)", contexto, re.IGNORECASE)
            or re.search(r"\d+\s*PEs?", contexto)
            or re.search(r"Custo:", contexto, re.IGNORECASE)
            or re.search(r"Força \+|Armadura \+|Habilidade \+", contexto, re.IGNORECASE)
        )

    def extrair_por_nome(self, nome_item: str) -> ItemMagicoExtraido | None:
        """Dado um nome do índice, tenta encontrar a descrição no PDF."""
        estrategias = [
            self._estrategia_exata,
            self._estrategia_case_insensitive,
            self._estrategia_sem_acentos,
            self._estrategia_primeira_palavra,
        ]

        for estrategia in estrategias:
            resultado = estrategia(nome_item)
            if resultado:
                return resultado
        return None

    def _buscar_melhor_ocorrencia(
        self, nome: str, posicoes: list[int], max_tentativas: int = 10
    ) -> ItemMagicoExtraido | None:
        melhor = None
        for pos in posicoes[:max_tentativas]:
            item = self._extrair_contexto(nome, pos)
            if item.confianca > 0.2 and (melhor is None or item.confianca > melhor.confianca):
                melhor = item
                if item.confianca >= 0.6:
                    break
        return melhor

    def _estrategia_exata(self, nome: str) -> ItemMagicoExtraido | None:
        posicoes = []
        start = 0
        while True:
            pos = self.todas_paginas.find(nome, start)
            if pos == -1:
                break
            posicoes.append(pos)
            start = pos + 1
        return self._buscar_melhor_ocorrencia(nome, posicoes) if posicoes else None

    def _estrategia_case_insensitive(self, nome: str) -> ItemMagicoExtraido | None:
        texto_lower = self.todas_paginas.lower()
        nome_lower = nome.lower()
        posicoes = []
        start = 0
        while True:
            pos = texto_lower.find(nome_lower, start)
            if pos == -1:
                break
            posicoes.append(pos)
            start = pos + 1
        return self._buscar_melhor_ocorrencia(nome, posicoes) if posicoes else None

    def _estrategia_sem_acentos(self, nome: str) -> ItemMagicoExtraido | None:
        def remover_acentos(s: str) -> str:
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )
        nome_sem = remover_acentos(nome)
        texto_sem = remover_acentos(self.todas_paginas)
        posicoes = []
        start = 0
        while True:
            pos = texto_sem.lower().find(nome_sem.lower(), start)
            if pos == -1:
                break
            posicoes.append(pos)
            start = pos + 1
        return self._buscar_melhor_ocorrencia(nome, posicoes) if posicoes else None

    def _estrategia_primeira_palavra(self, nome: str) -> ItemMagicoExtraido | None:
        """Só usa se o bloco contiver o nome completo (evita Anel→Anel Arcano)."""
        partes = nome.split()
        if not partes:
            return None
        primeira = partes[0]
        if len(primeira) <= 2:
            return None
        nome_norm = unicodedata.normalize("NFD", nome.lower())
        nome_norm = "".join(c for c in nome_norm if unicodedata.category(c) != "Mn")
        for match in re.finditer(
            rf"\b{re.escape(primeira)}\b", self.todas_paginas, re.IGNORECASE
        ):
            bloco = self.todas_paginas[match.start() : match.start() + 600]
            if not self._tem_indicador_item(bloco):
                continue
            bloco_norm = unicodedata.normalize("NFD", bloco.lower())
            bloco_norm = "".join(c for c in bloco_norm if unicodedata.category(c) != "Mn")
            if nome_norm[: max(15, len(nome_norm) - 2)] not in bloco_norm:
                continue
            return self._extrair_contexto(nome, match.start())
        return None

    def _extrair_contexto(
        self, nome: str, posicao: int, nome_real: str | None = None
    ) -> ItemMagicoExtraido:
        """Extrai campos a partir da posição do nome. Descrição completa até o próximo item."""
        nome_usado = nome_real or nome

        # Janela ampla para capturar descrições completas (até ~6000 chars)
        inicio = max(0, posicao - 80)
        fim = min(len(self.todas_paginas), posicao + 6000)
        bloco = self.todas_paginas[inicio:fim]

        pagina = 1
        chars_acumulados = 0
        for num, texto in self.texto_por_pagina.items():
            if chars_acumulados + len(texto) > posicao:
                pagina = num + 1
                break
            chars_acumulados += len(texto)

        tipo = self._extrair_campo_flexivel(
            bloco,
            [r"Tipo:\s*([^.\n]+)", r"tipo\s+([^.\n]+)", r"arma\s+([^.\n]+)", r"armadura\s+([^.\n]+)"],
        )

        bonus = self._extrair_campo_flexivel(
            bloco,
            [
                r"B[oô]nus:\s*([^.\n]+)",
                r"(?:Força|F)\s*\+\s*(\d+)",
                r"(?:Armadura|A)\s*\+\s*(\d+)",
                r"(?:Habilidade|H)\s*\+\s*(\d+)",
            ],
        )
        if not bonus:
            m = re.search(r"[FARH]\+\d+|\+\d+", bloco)
            bonus = m.group(0) if m else None
        if bonus and not re.search(r"[FARH]?\+\d+|\d+", str(bonus)):
            bonus = None

        # Descrição completa: do nome até o próximo item (inclui Preço)
        efeito = ""
        texto_restante = ""
        offset_no_bloco = posicao - inicio
        if offset_no_bloco >= 0:
            # Pular o nome: até o próximo \n (fim da linha do título)
            idx_nl = bloco.find("\n", offset_no_bloco)
            inicio_efeito = (idx_nl + 1) if idx_nl != -1 else offset_no_bloco
            # Se nome e descrição na mesma linha, buscar "Este"/"Esta"
            if idx_nl == -1 or idx_nl == offset_no_bloco:
                m = re.search(r"\s+(Este|Esta|O |A |Um |Uma)\s+", bloco[offset_no_bloco:], re.IGNORECASE)
                if m:
                    inicio_efeito = offset_no_bloco + m.start() + 1
            texto_restante = bloco[inicio_efeito:]

        if texto_restante:
            # Próximo item: linha que começa com título de item (Anel X, Poção X, etc.)
            prox_item = re.search(
                r"\n\s*(Anel\s|Poção\s|Pergaminho\s|Elixir\s|Óleo\s|Pomada\s|Cajado\s|"
                r"Espada\s|Luvas\s|Mão\s|Escama\s|Brachyura\s|Arma\s|Armadura\s|"
                r"Afiada\s|Vorpal\s|Profana\s|Sagrada\s|Contramágica\s|Estátua\s|"
                r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{4,35}\s*\(\d+\s*PEs?\)\s*:|\n\s*\d+\.\s+[A-Z])",
                texto_restante,
                re.IGNORECASE,
            )
            if prox_item:
                efeito = texto_restante[: prox_item.start()].strip()
            else:
                efeito = texto_restante.strip()

            # Limite de segurança 4000 chars (evita vazamento para próximo item em livros mal formatados)
            if len(efeito) > 4000:
                efeito = efeito[:4000].rstrip()

        # Custo: extrair do EFEITO (texto do item), não do bloco inteiro
        # Evita capturar "80 PEs" de "Força +5: 80 PEs" quando o item é Poção da Genialidade
        texto_para_custo = efeito if efeito else texto_restante if texto_restante else bloco
        custo = self._extrair_campo_flexivel(
            texto_para_custo,
            [
                r"Pre[cç]o:\s*([^\n]+)",
                r"Custo:\s*([^.\n]+)",
                rf"{re.escape(nome_usado[:40])}\s*:\s*(\d+)\s*PEs?\s*\.?",  # "Poção da Genialidade: 10 PEs."
                r"\((\d+)\s*PEs?\)",
                r":\s*(\d+)\s*PEs?\s*\.",  # "Nome: 50 PEs." no fim do bloco
                r"(\d+)\s*PEs?\s*[;.]",
            ],
        )
        if custo:
            custo = custo.strip()
            if custo.isdigit():
                if "T$" in texto_para_custo and "Preço" in texto_para_custo:
                    custo = f"T$ {custo}"
                elif "PE" not in custo.upper():
                    custo = f"{custo} PEs"

        campos = sum([bool(tipo), bool(bonus), bool(custo), bool(efeito)])
        confianca = campos / 4.0 if campos > 0 else 0.1

        # Rejeitar blocos com OCR ruim (ex.: Pena de Grifo do manual-revisado-ampliado)
        texto_avaliar = f"{tipo or ''} {efeito or ''}".strip()
        if texto_avaliar and self._qualidade_ocr_ruim(texto_avaliar):
            confianca = 0.0

        return ItemMagicoExtraido(
            nome=nome_usado,
            tipo=tipo,
            bonus=bonus,
            custo=custo,
            efeito=efeito,
            pagina=pagina,
            confianca=confianca,
            fonte="busca_agressiva",
            livro=self.nome_livro,
            texto_bruto=bloco[:600],
        )

    def extrair_por_descoberta(self) -> list[ItemMagicoExtraido]:
        """
        Descobre itens varrendo o PDF por estrutura (Manual da Magia).
        Encontra blocos que parecem itens: "Nome (X PEs):", "Nome:" + Preço, etc.
        """
        resultados: list[ItemMagicoExtraido] = []
        texto = self.todas_paginas
        vistos: set[str] = set()

        # Padrões de início de item (nome seguido de indicador)
        padroes = [
            # "Nome (X PEs):" ou "Nome (X PEs)."
            re.compile(
                r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,50}?)\s*\((\d+)\s*PEs?\)\s*[.:]",
                re.IGNORECASE,
            ),
            # "Força +1: 8 PEs" / "Resistência +2: 2 PMs"
            re.compile(
                r"((?:Força|Habilidade|Resistência|Armadura|PdF)\s*\+\s*\d+)\s*:\s*(\d+)\s*(?:PEs?|PMs?)",
                re.IGNORECASE,
            ),
            # "Poção do Amor: 50 PEs." / "Anel Arcano: ..."
            re.compile(
                r"((?:Poção|Pergaminho|Elixir|Óleo|Pomada|Anel|Cajado|Bastão|Escudo)\s+"
                r"(?:de\s+)?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']*?)\s*:\s*(\d+)\s*PEs?\s*\.?",
                re.IGNORECASE,
            ),
            # "Nome\n" seguido de Preço: ou Tipo: (linha anterior é título)
            re.compile(
                r"\n([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{4,45}?)\s*\n\s*(?:Preço|Tipo|Bônus|Custo):",
                re.IGNORECASE,
            ),
        ]

        for padrao in padroes:
            for m in padrao.finditer(texto):
                nome = m.group(1).strip()
                if "\n" in nome:
                    nome = nome.split("\n")[-1].strip()
                if len(nome) < 4 or len(nome) > 55:
                    continue
                if any(x in nome.lower() for x in ["página", "capítulo", "objetos", "mágicos"]):
                    continue
                if any(f in nome.lower() for f in INDICE_FRAGMENTOS):
                    continue
                chave = nome.lower()
                if chave in vistos:
                    continue
                vistos.add(chave)

                item = self._extrair_contexto(nome, m.start())
                if item.confianca > 0.15 and not self._qualidade_ocr_ruim(
                    (item.efeito or "")[:500]
                ):
                    item.fonte = "descoberta"
                    resultados.append(item)

        return resultados


# Fragmentos que indicam linha inválida no índice (não é nome de item)
INDICE_FRAGMENTOS = {
    "anel tem", "anel aos", "anel parece", "anel saia", "anel estiver", "anel se parece",
    "anel é capaz", "anel nem", "anel são", "anel cujo", "anel e uma", "anel magico toma",
    "anel mágico torna", "anel capaz de", "anel é uma", "anel arcano um mago",
    "anel com três pedras oferecerá", "anel com uma", "anel consome", "anel da revelação da loucura oferece",
    "anel de anula", "anel de força se aplicam", "anel de força sempre é ornamentado",
    "anel de ouro usa energia mágica", "anel dos desejos permite", "anel elemental oferece",
    "anel em seus", "anel estiver no dedo", "anel ganha a capacidade de", "anel mágico era visto",
    "anel mágico é colocado", "anel mágicona mesma mão", "anel nunca pode armazenar",
    "anel não", "anel oferece ao seu usuário", "anel parece um belo", "anel pode usar o poder da",
    "anel poderá", "anel prateado tem uma ou mais", "anel sempre leva o nome", "anel são itens",
    "anel são os pri", "anel torna o usuário imune", "anel torna-se cin", "anel torna-se mais ágil",
    "anel é colocado no dedo", "anel é conjurado", "anel é considerado", "anel é encontrado o mestre",
    "anel é um item raro", "anel é uma versão", "poção acaba", "poção não veja", "poção tem uma",
    "poção ela é", "poção ele é", "poção adquire", "poção conseguirá", "poção torna", "poção teria",
    "poção permite", "poção perdura", "poção de Explosão deve se", "poção de forma errada",
    "poção vai levar", "poção faz", "poção é usada", "pergaminho mágico", "pergaminho a magia",
    "pergaminho contém", "pergaminho consigo", "pergaminho com", "pergaminho mágico é relativa",
    "pergaminho se", "não veja", "sando o machado", "tador conjure", "da Força Infinita",
    "tornável", "remessável", "benefícios", "chado de batalha", "habilidades Arremessável",
    "mas tem a habilidade", "custo em PMs", "ção pela metade", "nenosa", "com as habilidades",
    "tência dos alvos", "contra fogo", "com seus PVs", "elixir é muito", "que confere Ataque Múltiplo",
    "da Força Infinita encontra-se", "só vai fazer efeito quando", "deve ser arremessada", "não adianta esfregar",
}


def _indice_valido(nome: str) -> bool:
    """Retorna True se a linha do índice parece um nome de item válido."""
    n = nome.strip()
    if len(n) < 4 or len(n) > 70:
        return False
    if n.endswith("-") or "..." in n:
        return False
    if not n[0].isupper() and n[0] not in "0123456789":
        return False
    n_lower = n.lower()
    if any(f in n_lower for f in INDICE_FRAGMENTOS):
        return False
    return True


# Lista fallback: poderes de armas + itens do Manual da Magia (anéis, poções, pergaminhos, etc.)
INDICE_FALLBACK = [
    # Poderes de armas
    "Afiada", "Agonizante", "Absoluta", "Absorvedora", "Adaptável", "Alcance Longo", "Arcana",
    "Arena", "Carga Extra", "Vorpal", "Profana", "Sagrada", "Espiritual", "Vampírica",
    # Anéis
    "Anel Arcano",
    # Poções
    "Poção de Cura", "Poção de Força", "Poção de Velocidade", "Poção de Saltar",
    "Poção do Amor", "Poção do Ar Molhado", "Poção do Carisma", "Poção da Grande Força",
    "Poção da Genialidade", "Poção dos Heróis", "Poção Ladina", "Poção da Verdade",
    # Itens diversos
    "Óleo Escorregadio", "Pergaminho", "Força +1", "Força +2", "Força +3",
    "Armadura +1", "Armadura +2", "Armadura +3",
]


def main() -> None:
    caminho_indice = Path("data/processed/indice_itens_magicos_3dt.txt")
    raw_count = 0
    if not caminho_indice.exists():
        print("Criando índice fallback (execute scripts para extrair do PDF)...")
        indice = [(i, n) for i, n in enumerate(INDICE_FALLBACK, 1)]
    else:
        indice = []
        raw_count = 0
        with caminho_indice.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if ". " in line:
                    raw_count += 1
                    _, nome = line.strip().split(". ", 1)
                    nome = nome.strip()
                    if _indice_valido(nome):
                        indice.append((i, nome))

    pdfs = _encontrar_pdfs()
    print(f"Livros encontrados: {len(pdfs)}")
    for p in pdfs:
        print(f"  - {p.name}")

    total = len(indice)
    if caminho_indice.exists() and raw_count > total:
        print(f"Índice: {total} itens válidos (filtrados {raw_count - total} fragmentos)")
    print(f"\nProcurando {total} itens em {len(pdfs)} livros (coletando de TODOS os livros)...")

    # Coleta itens de TODOS os livros: (nome, livro) -> item (evita duplicata no mesmo livro)
    resultados_por_livro: dict[tuple[str, str], ItemMagicoExtraido] = {}
    # Rastreia quais itens do índice foram encontrados em pelo menos um livro
    encontrados_no_indice: set[int] = set()

    for pdf_path in pdfs:
        print(f"\n--- {pdf_path.name} ---")
        try:
            extrator = ExtratorItensMagicosAgressivo(pdf_path)
        except Exception as e:
            print(f"  Erro ao abrir: {e}")
            continue

        achadas = 0
        for num, nome in indice:
            item = extrator.extrair_por_nome(nome)
            if item and item.confianca > 0.2:
                chave = (nome.strip().lower(), extrator.nome_livro)
                if chave not in resultados_por_livro:
                    resultados_por_livro[chave] = item
                    achadas += 1
                    encontrados_no_indice.add(num)

        # Descoberta: varre o PDF por estrutura (Manual da Magia sem alpha)
        is_manual_magia = (
            "manual" in pdf_path.name.lower()
            and "magia" in pdf_path.name.lower()
            and "alpha" not in pdf_path.name.lower()
        )
        if is_manual_magia:
            descobertos = extrator.extrair_por_descoberta()
            disc_novos = 0
            for item in descobertos:
                chave = (item.nome.strip().lower(), extrator.nome_livro)
                if chave not in resultados_por_livro:
                    resultados_por_livro[chave] = item
                    disc_novos += 1
            if disc_novos:
                print(f"  Descoberta (estrutura): +{disc_novos} itens novos")

        extrator.close()
        print(f"  Encontrados: {achadas} (total único nome+livro: {len(resultados_por_livro)})")

    encontradas = [asdict(item) for item in resultados_por_livro.values()]
    # Ordenar por livro, depois nome (origem sempre explícita)
    encontradas.sort(key=lambda i: (i.get("livro", ""), i.get("nome", "").lower()))
    nao_encontradas = [(num, nome) for num, nome in indice if num not in encontrados_no_indice]

    output_dir = Path("data/processed/itens_magicos")
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "itens_magicos_extraidos_agressivo.json").open("w", encoding="utf-8") as f:
        json.dump(encontradas, f, ensure_ascii=False, indent=2)

    with (output_dir / "itens_nao_encontrados.txt").open("w", encoding="utf-8") as f:
        for num, nome in nao_encontradas:
            f.write(f"{num:03d}. {nome}\n")

    print(f"\n{'='*60}")
    print("RESULTADO")
    print(f"{'='*60}")
    print(f"Itens extraídos (nome+livro): {len(encontradas)}")
    print(f"Itens do índice únicos encontrados: {len(encontrados_no_indice)}/{total}")
    print(f"Não encontrados em nenhum livro: {len(nao_encontradas)}")
    # Resumo por livro
    por_livro: dict[str, int] = {}
    for item in encontradas:
        livro = item.get("livro", "?")
        por_livro[livro] = por_livro.get(livro, 0) + 1
    print("\nPor livro:")
    for livro, qtd in sorted(por_livro.items(), key=lambda x: -x[1]):
        print(f"  {livro}: {qtd}")
    print(f"\nArquivos salvos em {output_dir}/")


if __name__ == "__main__":
    main()
