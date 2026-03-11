"""
Extrator agressivo: busca cada magia do índice no PDF com múltiplas estratégias.
Suporta PyMuPDF e pdfplumber; formato Escola ou Exigências (Manual Revisado Ampliado).
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

# PDFs que extraem melhor com pdfplumber (layout/OCR)
PDFS_PREFERIR_PDFPLUMBER = {"3dt-manual-revisado-ampliado-e-turbinado-biblioteca-elfica.pdf"}


@dataclass
class MagiaExtraida:
    nome: str
    escola: str | None = None
    custo: str | None = None
    alcance: str | None = None
    duracao: str | None = None
    descricao: str | None = None
    pagina: int = 0
    confianca: float = 0.0
    fonte: str = ""
    livro: str = ""  # Nome do PDF de origem
    texto_bruto: str = ""


def _encontrar_pdfs() -> list[Path]:
    """Localiza todos os PDFs no diretório de fontes."""
    from src.config import paths

    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        raise FileNotFoundError(
            f"Diretorio de PDFs nao encontrado: {pdf_dir}. Configure SOURCE_PDF_DIR."
        )
    pdfs = sorted(pdf_dir.rglob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"Nenhum PDF encontrado em {pdf_dir}")
    return pdfs


class ExtratorMagiasAgressivo:
    """
    Extrator que tenta múltiplas estratégias para encontrar magias em um PDF.
    Usa pdfplumber para PDFs com layout complexo (ex: Manual Revisado Ampliado).
    """

    def __init__(self, caminho_pdf: str | Path, nome_livro: str = ""):
        self.caminho = Path(caminho_pdf)
        self.nome_livro = nome_livro or self.caminho.name
        self.doc = None

        preferir_plumber = self.caminho.name in PDFS_PREFERIR_PDFPLUMBER
        try:
            from src.ingestion.pdf_text_extractor import extrair_texto_dual

            self.texto_por_pagina, self.todas_paginas, metodo = extrair_texto_dual(
                self.caminho, preferir_pdfplumber=preferir_plumber
            )
        except Exception:
            if fitz is None:
                raise ImportError("PyMuPDF (pip install pymupdf) necessario.")
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
        """Extrai primeiro grupo do regex ou None."""
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extrair_campo_flexivel(
        self, texto: str, padroes: list[str]
    ) -> str | None:
        """Tenta vários padrões (Escola, Exigências, typos OCR)."""
        for padrao in padroes:
            val = self._extrair_campo(texto, padrao)
            if val:
                return val
        return None

    def extrair_por_nome(self, nome_magia: str) -> MagiaExtraida | None:
        """Dado um nome do índice, tenta encontrar a descrição completa no PDF."""
        estrategias = [
            self._estrategia_exata,
            self._estrategia_case_insensitive,
            self._estrategia_sem_acentos,
            self._estrategia_primeira_palavra,
            self._estrategia_fuzzy,
        ]

        for estrategia in estrategias:
            resultado = estrategia(nome_magia)
            if resultado:
                return resultado

        return None

    def _buscar_melhor_ocorrencia(
        self, nome: str, posicoes: list[int], max_tentativas: int = 15
    ) -> MagiaExtraida | None:
        """Dada lista de posições, retorna a magia com maior confiança."""
        melhor = None
        for pos in posicoes[:max_tentativas]:
            magia = self._extrair_contexto(nome, pos)
            if magia.confianca > 0.3 and (melhor is None or magia.confianca > melhor.confianca):
                melhor = magia
                if magia.confianca >= 0.8:
                    break  # Já temos boa extração
        return melhor

    def _estrategia_exata(self, nome: str) -> MagiaExtraida | None:
        """Busca exata do nome no texto."""
        posicoes = []
        start = 0
        while True:
            pos = self.todas_paginas.find(nome, start)
            if pos == -1:
                break
            posicoes.append(pos)
            start = pos + 1
        return self._buscar_melhor_ocorrencia(nome, posicoes) if posicoes else None

    def _estrategia_case_insensitive(self, nome: str) -> MagiaExtraida | None:
        """Busca sem case sensitive."""
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

    def _estrategia_sem_acentos(self, nome: str) -> MagiaExtraida | None:
        """Remove acentos para comparar."""

        def remover_acentos(s: str) -> str:
            return "".join(
                c
                for c in unicodedata.normalize("NFD", s)
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

    def _tem_indicador_magia(self, contexto: str) -> bool:
        """Verifica se o contexto parece bloco de magia (Escola ou Exigências)."""
        return bool(
            re.search(r"Escola:", contexto, re.IGNORECASE)
            or re.search(r"Exig[eê]n[cç]i[aã]s?:", contexto, re.IGNORECASE)
            or re.search(r"Exlg[eê]nclas?:", contexto, re.IGNORECASE)
            or re.search(r"Custo:", contexto, re.IGNORECASE)
            or re.search(r"Custa:", contexto, re.IGNORECASE)
        )

    def _estrategia_primeira_palavra(self, nome: str) -> MagiaExtraida | None:
        """Busca só pela primeira palavra (para nomes longos)."""
        partes = nome.split()
        if not partes:
            return None
        primeira = partes[0]
        if len(primeira) <= 3:
            return None
        for match in re.finditer(
            rf"\b{re.escape(primeira)}\b", self.todas_paginas, re.IGNORECASE
        ):
            contexto = self.todas_paginas[match.start() : match.start() + 300]
            if self._tem_indicador_magia(contexto):
                return self._extrair_contexto(nome, match.start())
        return None

    def _estrategia_fuzzy(self, nome: str) -> MagiaExtraida | None:
        """Último recurso: busca aproximada."""
        from difflib import get_close_matches

        # Padrões: Nome seguido de Escola ou Exigências
        padroes = [
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,50}?)\s*\n\s*Escola:",
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,50}?)\s*\n\s*Exig[eê]n[cç]i[aã]s?:",
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,50}?)\s*\n\s*Exlg[eê]nclas?:",
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,50}?)\s*\n\s*Custo:",
            r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,50}?)\s*\n\s*Custa:",
        ]
        candidatos = []
        for padrao in padroes:
            candidatos.extend(re.findall(padrao, self.todas_paginas, re.IGNORECASE))
        candidatos = [c.strip() for c in candidatos if len(c.strip()) >= 4]
        matches = get_close_matches(nome, candidatos, n=1, cutoff=0.75)
        if matches:
            nome_encontrado = matches[0].strip()
            pos = self.todas_paginas.find(nome_encontrado)
            if pos != -1:
                return self._extrair_contexto(nome, pos, nome_real=nome_encontrado)
        return None

    def _extrair_contexto(
        self, nome: str, posicao: int, nome_real: str | None = None
    ) -> MagiaExtraida:
        """Extrai campos a partir da posição do nome. Suporta Escola e Exigências."""
        nome_usado = nome_real or nome

        inicio = max(0, posicao - 100)
        fim = min(len(self.todas_paginas), posicao + 2500)
        bloco = self.todas_paginas[inicio:fim]

        pagina = 1
        chars_acumulados = 0
        for num, texto in self.texto_por_pagina.items():
            if chars_acumulados + len(texto) > posicao:
                pagina = num + 1
                break
            chars_acumulados += len(texto)

        # Escola ou Exigências (Manual Revisado Ampliado)
        escola = self._extrair_campo_flexivel(
            bloco,
            [
                r"Escola:\s*([^.\n]+)",
                r"Exig[eê]n[cç]i[aã]s?:\s*([^.\n]+)",
                r"Exlg[eê]nclas?:\s*([^.\n]+)",
                r"Ex[i!1]g[êe6]n[cç]i[aã]s?:\s*([^.\n]+)",
                r"Exlg[eê]nclu:\s*([^.\n]+)",
            ],
        )
        custo = self._extrair_campo_flexivel(
            bloco,
            [
                r"Custo:\s*([^.\n]+)",
                r"Custa:\s*([^.\n]+)",
                r"Cu1to:\s*([^.\n]+)",
                r"Culto:\s*([^.\n]+)",
                r"Custa\.\s*([^.\n]+)",
            ],
        )
        alcance = self._extrair_campo_flexivel(
            bloco,
            [
                r"Alcance:\s*([^;.\n]+)",
                r"A1CanC11:\s*([^;.\n]+)",
                r"Alcanct:\s*([^;.\n]+)",
                r"Alcara:\s*([^;.\n]+)",
            ],
        )
        duracao = self._extrair_campo_flexivel(
            bloco,
            [
                r"Dura[çc][ãa]o:\s*([^.\n]+)",
                r"Our[1l][1l]?[Çc]io:\s*([^.\n]+)",
                r"Dunçio:\s*([^.\n]+)",
                r"Duraçlo:\s*([^.\n]+)",
                r"Our19Ao:\s*([^.\n]+)",
            ],
        )

        descricao = ""
        # Início da descrição: após Duração ou Alcance
        match_dur = re.search(
            r"(?:Dura[çc][ãa]o|Our[1l][1l]?[Çc]io|Dunçio|Duraçlo):[^.\n]+",
            bloco,
            re.IGNORECASE,
        )
        if match_dur:
            inicio_desc = match_dur.end()
            # Fim: próxima magia (Nome + Escola/Exigências)
            fim_desc = re.search(
                r"\n\s*[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{4,50}\s*\n\s*(?:Escola|Exig[eê]n[cç]i[aã]s?|Exlg[eê]nclas?|Custo|Custa):",
                bloco[inicio_desc:],
                re.IGNORECASE,
            )
            if fim_desc:
                descricao = bloco[
                    inicio_desc : inicio_desc + fim_desc.start()
                ].strip()[:1200]
            else:
                descricao = bloco[inicio_desc:].strip()[:1200]

        campos_preenchidos = sum(
            [bool(escola), bool(custo), bool(alcance), bool(duracao), bool(descricao)]
        )
        confianca = campos_preenchidos / 5.0

        return MagiaExtraida(
            nome=nome_usado,
            escola=escola,
            custo=custo,
            alcance=alcance,
            duracao=duracao,
            descricao=descricao,
            pagina=pagina,
            confianca=confianca,
            fonte="busca_agressiva",
            livro=self.nome_livro,
            texto_bruto=bloco[:500],
        )


def main() -> None:
    caminho_indice = Path("data/processed/indice_magias_3dt.txt")
    if not caminho_indice.exists():
        print("Execute primeiro: python scripts/extrair_todas_magias_3dt.py")
        return

    pdfs = _encontrar_pdfs()
    print(f"Livros encontrados: {len(pdfs)}")
    for p in pdfs:
        print(f"  - {p.name}")

    indice: list[tuple[int, str]] = []
    with caminho_indice.open("r", encoding="utf-8") as f:
        for line in f:
            if ". " in line:
                num, nome = line.strip().split(". ", 1)
                indice.append((int(num), nome))

    total = len(indice)
    print(f"\nProcurando {total} magias em {len(pdfs)} livros...")

    # Para cada magia, guarda o melhor resultado encontrado
    resultados: dict[int, MagiaExtraida] = {}

    for pdf_path in pdfs:
        print(f"\n--- {pdf_path.name} ---")
        try:
            extrator = ExtratorMagiasAgressivo(pdf_path)
        except Exception as e:
            print(f"  Erro ao abrir: {e}")
            continue

        achadas_neste = 0
        for num, nome in indice:
            if num in resultados:
                continue
            magia = extrator.extrair_por_nome(nome)
            if magia and magia.confianca > 0.3:
                resultados[num] = magia
                achadas_neste += 1

        extrator.close()
        print(f"  Encontradas: {achadas_neste} (total acumulado: {len(resultados)}/{total})")

    encontradas = [asdict(resultados[num]) for num, _ in indice if num in resultados]
    nao_encontradas = [(num, nome) for num, nome in indice if num not in resultados]

    output_dir = Path("data/processed/magias")
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "magias_extraidas_agressivo.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(encontradas, f, ensure_ascii=False, indent=2)

    with (output_dir / "magias_nao_encontradas.txt").open(
        "w", encoding="utf-8"
    ) as f:
        for num, nome in nao_encontradas:
            f.write(f"{num:03d}. {nome}\n")

    print(f"\n{'='*60}")
    print("RESULTADO")
    print(f"{'='*60}")
    print(f"Encontradas: {len(encontradas)}/{total} ({100*len(encontradas)/total:.1f}%)")
    print(f"Nao encontradas: {len(nao_encontradas)}")
    print(f"\nArquivos salvos em {output_dir}/")


if __name__ == "__main__":
    main()
