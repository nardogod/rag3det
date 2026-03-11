"""
Extrator agressivo de Vantagens e Desvantagens do Manual da Magia.
Busca cada item do índice no PDF e extrai bloco completo.
Campos: nome, tipo (vantagem/desvantagem), custo, efeito, livro, pagina.
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


@dataclass
class VantagemExtraida:
    nome: str
    tipo: str  # vantagem | desvantagem
    custo: str
    efeito: str
    pagina: int = 0
    confianca: float = 0.0
    livro: str = ""


def _encontrar_pdf_manual_magia() -> Path:
    from src.config import paths
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {pdf_dir}")
    pdfs = list(pdf_dir.rglob("*.pdf"))
    manual = [p for p in pdfs if "manual" in p.name.lower() and "magia" in p.name.lower()]
    sem_alpha = [p for p in manual if "alpha" not in p.name.lower()]
    pdf = sem_alpha[0] if sem_alpha else (manual[0] if manual else None)
    if not pdf:
        raise FileNotFoundError("PDF Manual da Magia não encontrado")
    return pdf


# Páginas do capítulo "NOVAS VANTAGENS E DESVANTAGENS" no Manual da Magia (~95-110)
PAGINAS_VANTAGENS = (90, 125)  # 0-indexed: pg 91-126


class ExtratorVantagensMagia:
    """Extrai blocos de Vantagens/Desvantagens do Manual da Magia."""

    def __init__(self, caminho_pdf: str | Path, paginas: tuple[int, int] = PAGINAS_VANTAGENS):
        self.caminho = Path(caminho_pdf)
        self.nome_livro = self.caminho.name
        self.paginas = paginas
        self.doc = None
        try:
            from src.ingestion.pdf_text_extractor import extrair_texto_dual
            texto_por_pagina, _, _ = extrair_texto_dual(
                self.caminho, preferir_pdfplumber=False
            )
            # Restringe às páginas do capítulo
            p_min, p_max = paginas
            self.texto_por_pagina = {
                i: t for i, t in texto_por_pagina.items()
                if p_min <= i <= p_max
            }
            self.todas_paginas = "\n".join(self.texto_por_pagina.values())
        except Exception:
            if fitz is None:
                raise ImportError("PyMuPDF (pip install pymupdf) necessário.")
            self.doc = fitz.open(str(caminho_pdf))
            all_text = {i: p.get_text() for i, p in enumerate(self.doc)}
            p_min, p_max = paginas
            self.texto_por_pagina = {i: all_text[i] for i in range(p_min, min(p_max + 1, len(all_text)))}
            self.todas_paginas = "\n".join(self.texto_por_pagina.values())

    def close(self) -> None:
        if getattr(self, "doc", None) is not None:
            try:
                self.doc.close()
            except (ValueError, AttributeError):
                pass
            self.doc = None

    def extrair_por_nome(self, nome: str, custo: str) -> VantagemExtraida | None:
        """Busca nome no texto e extrai bloco até o próximo item."""
        nome_limpo = nome.strip()
        if not nome_limpo:
            return None

        # Tipo: desvantagem se custo negativo
        eh_desvantagem = "-" in custo or "–" in custo

        # Estratégias de busca
        posicoes = []
        texto_lower = self.todas_paginas.lower()
        nome_lower = nome_limpo.lower()
        start = 0
        while True:
            pos = texto_lower.find(nome_lower, start)
            if pos == -1:
                break
            posicoes.append(pos)
            start = pos + 1

        if not posicoes:
            # Tentar sem acentos
            nome_norm = "".join(
                c for c in unicodedata.normalize("NFD", nome_limpo.lower())
                if unicodedata.category(c) != "Mn"
            )
            texto_norm = "".join(
                c for c in unicodedata.normalize("NFD", self.todas_paginas.lower())
                if unicodedata.category(c) != "Mn"
            )
            start = 0
            while True:
                pos = texto_norm.find(nome_norm, start)
                if pos == -1:
                    break
                posicoes.append(pos)
                start = pos + 1

        if not posicoes:
            return None

        melhor = None
        for pos in posicoes[:5]:
            item = self._extrair_bloco(nome_limpo, pos, custo, eh_desvantagem)
            if item and item.confianca > 0.2:
                if melhor is None or item.confianca > melhor.confianca:
                    melhor = item
                    if item.confianca >= 0.5:
                        break
        return melhor

    def _extrair_bloco(
        self, nome: str, posicao: int, custo: str, eh_desvantagem: bool
    ) -> VantagemExtraida | None:
        """Extrai bloco do nome até o próximo 'Nome (X pontos)'."""
        inicio = max(0, posicao - 50)
        fim = min(len(self.todas_paginas), posicao + 2500)
        bloco = self.todas_paginas[inicio:fim]

        # Página (1-based)
        chars = 0
        pagina = self.paginas[0] + 1
        for num in sorted(self.texto_por_pagina.keys()):
            texto = self.texto_por_pagina[num]
            if chars + len(texto) > posicao:
                pagina = num + 1
                break
            chars += len(texto)

        # Efeito: do nome até o próximo item
        offset = posicao - inicio
        idx_nl = bloco.find("\n", offset)
        inicio_efeito = (idx_nl + 1) if idx_nl != -1 else offset
        texto_restante = bloco[inicio_efeito:]

        # Próximo item: "Nome (X pontos)" ou "Nome (–X pontos)"
        prox = re.search(
            r"\n\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,40}?)\s*\(\s*(?:especial|\d+(?:\s*a\s*\d+)?\s*pontos?|[\-–]\d+\s*pontos?)\s*\)",
            texto_restante,
            re.IGNORECASE,
        )
        if prox:
            efeito = texto_restante[: prox.start()].strip()
        else:
            efeito = texto_restante.strip()

        if len(efeito) > 2000:
            efeito = efeito[:2000].rstrip()

        # Validar: bloco deve parecer vantagem/desvantagem
        indicadores = (
            "pontos" in efeito.lower()
            or "você" in efeito.lower()
            or "personagem" in efeito.lower()
            or "pode" in efeito.lower()
            or "recebe" in efeito.lower()
            or "gasta" in efeito.lower()
        )
        if not indicadores and len(efeito) < 50:
            return None

        confianca = 0.3 + min(0.4, len(efeito) / 500) if efeito else 0.1

        return VantagemExtraida(
            nome=nome,
            tipo="desvantagem" if eh_desvantagem else "vantagem",
            custo=custo,
            efeito=efeito,
            pagina=pagina,
            confianca=confianca,
            livro=self.nome_livro,
        )


def main() -> None:
    indice_path = Path("data/processed/vantagens_desvantagens/indice_vantagens_magia.txt")
    if not indice_path.exists():
        print("Execute primeiro: python scripts/extrair_indice_vantagens_magia.py")
        return

    indice = []
    with indice_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if ". " in line and " | " in line:
                num_part, rest = line.split(". ", 1)
                nome, custo = rest.split(" | ", 1)
                indice.append((int(num_part), nome.strip(), custo.strip()))

    pdf_path = _encontrar_pdf_manual_magia()
    print(f"Processando: {pdf_path.name}")
    print(f"Índice: {len(indice)} itens\n")

    extrator = ExtratorVantagensMagia(pdf_path)
    resultados = []
    nao_encontradas = []

    for num, nome, custo in indice:
        item = extrator.extrair_por_nome(nome, custo)
        if item and item.confianca > 0.2:
            resultados.append(asdict(item))
        else:
            nao_encontradas.append((num, nome, custo))

    extrator.close()

    out_dir = Path("data/processed/vantagens_desvantagens")
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "vantagens_magia_extraidas.json").open("w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    with (out_dir / "vantagens_nao_encontradas.txt").open("w", encoding="utf-8") as f:
        for num, nome, custo in nao_encontradas:
            f.write(f"{num:03d}. {nome} | {custo}\n")

    print(f"{'='*60}")
    print("RESULTADO")
    print(f"{'='*60}")
    print(f"Extraídas: {len(resultados)}/{len(indice)}")
    print(f"Não encontradas: {len(nao_encontradas)}")
    print(f"\nSalvo em {out_dir}/")


if __name__ == "__main__":
    main()
