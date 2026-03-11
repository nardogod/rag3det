"""
Extrator de Perícias 3D&T.
Busca as 11 Perícias nos PDFs (Manual Turbinado, Manual do Aventureiro).
Campos: nome, custo, descricao, especializacoes, livro, pagina.
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

# As 11 Perícias do 3D&T (ordem típica no livro)
PERICIAS = [
    "Animais", "Arte", "Ciência", "Idiomas", "Investigação",
    "Máquinas", "Medicina", "Sobrevivência", "Crime", "Esporte", "Manipulação",
]


@dataclass
class PericiaExtraida:
    nome: str
    custo: str
    descricao: str
    especializacoes: list[str]
    pagina: int = 0
    livro: str = ""


def _qualidade_ocr_ruim(texto: str) -> bool:
    """Rejeita texto com OCR ruim (manual-revisado-ampliado)."""
    if not texto or len(texto) < 50:
        return False
    if re.search(r"[a-záàâãéêíóôõúç][0-9]{2,}[a-záàâãéêíóôõúç]", texto, re.I):
        return True
    letras = sum(1 for c in texto if c.isalpha() or c in "áàâãéêíóôõúç ")
    if letras / max(len(texto), 1) < 0.65:
        return True
    return False


def _encontrar_pdfs_pericias() -> list[Path]:
    """PDFs que podem ter o capítulo de Perícias (LISTA DE PERÍCIAS).
    Prioriza Manual Turbinado Digital (melhor OCR). Evita Alpha Aventureiro (Kits)."""
    from src.config import paths
    pdf_dir = paths.source_pdf_dir
    if not pdf_dir.exists():
        raise FileNotFoundError(f"Diretório de PDFs não encontrado: {pdf_dir}")
    todos = list(pdf_dir.rglob("*.pdf"))
    # Manual Turbinado Digital primeiro (Cópia de 3D&T...)
    turbinado_digital = [p for p in todos if "turbinado" in p.name.lower() and "digital" in p.name.lower()]
    # manual-revisado-ampliado tem OCR ruim
    revisado = [p for p in todos if "revisado" in p.name.lower() and "ampliado" in p.name.lower()]
    outros = [p for p in todos if p not in turbinado_digital and p not in revisado and "alpha-manual-do-aventureiro" not in p.name.lower()]
    return sorted(turbinado_digital) + sorted(revisado) + sorted(outros)


def _extrair_especializacoes(texto: str) -> list[str]:
    """Extrai nomes de Especializações (padrão: Nome: descrição)."""
    especializacoes = []
    # Padrão: "Doma: você sabe..." ou "Montaria: você sabe..." (nome em início de linha)
    for m in re.finditer(
        r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-/]+?)\s*:\s*(?:você|o personagem|inclui)",
        texto,
        re.MULTILINE | re.IGNORECASE,
    ):
        nome = m.group(1).strip()
        if 3 <= len(nome) <= 40 and nome not in especializacoes:
            especializacoes.append(nome)
    return especializacoes


class ExtratorPericias:
    """Extrai Perícias de um PDF."""

    def __init__(self, caminho_pdf: str | Path):
        self.caminho = Path(caminho_pdf)
        self.nome_livro = self.caminho.name
        self.doc = None
        try:
            from src.ingestion.pdf_text_extractor import extrair_texto_dual
            texto_por_pagina, _, _ = extrair_texto_dual(
                self.caminho, preferir_pdfplumber=False
            )
            self.texto_por_pagina = dict(texto_por_pagina)
            self.todas_paginas = "\n".join(self.texto_por_pagina.values())
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

    def extrair_pericia(self, nome: str) -> PericiaExtraida | None:
        """Busca a Perícia e extrai bloco até a próxima."""
        nome_limpo = nome.strip()
        if not nome_limpo:
            return None

        texto_lower = self.todas_paginas.lower()
        nome_lower = nome_limpo.lower()
        pos = texto_lower.find(nome_lower)
        if pos == -1:
            # Sem acentos
            nome_norm = "".join(
                c for c in unicodedata.normalize("NFD", nome_limpo.lower())
                if unicodedata.category(c) != "Mn"
            )
            texto_norm = "".join(
                c for c in unicodedata.normalize("NFD", self.todas_paginas.lower())
                if unicodedata.category(c) != "Mn"
            )
            pos = texto_norm.find(nome_norm)
            if pos == -1:
                return None

        # Bloco: do nome até a próxima Perícia
        inicio = max(0, pos - 30)
        fim = min(len(self.todas_paginas), pos + 2000)
        bloco = self.todas_paginas[inicio:fim]

        offset = pos - inicio
        idx_nl = bloco.find("\n", offset)
        inicio_desc = (idx_nl + 1) if idx_nl != -1 else offset
        texto_restante = bloco[inicio_desc:]

        # Próxima Perícia (outro nome da lista)
        prox_match = None
        for outro in PERICIAS:
            if outro.lower() == nome_lower:
                continue
            m = re.search(
                rf"\n\s*{re.escape(outro)}\s*\n",
                texto_restante,
                re.IGNORECASE,
            )
            if m and (prox_match is None or m.start() < prox_match.start()):
                prox_match = m

        if prox_match:
            descricao = texto_restante[: prox_match.start()].strip()
        else:
            descricao = texto_restante.strip()

        if len(descricao) > 1500:
            descricao = descricao[:1500].rstrip()

        # Validar: deve parecer Perícia (não Kit de Personagem)
        desc_lower = descricao.lower()
        if "função:" in desc_lower[:250] and "entende" not in desc_lower[:150] and "sabe" not in desc_lower[:150]:
            return None  # Kit, não Perícia
        if not any(
            x in desc_lower
            for x in ["você", "personagem", "perícia", "sabe", "pode", "teste", "entende"]
        ) and len(descricao) < 80:
            return None
        if _qualidade_ocr_ruim(descricao):
            return None  # OCR ruim

        especializacoes = _extrair_especializacoes(descricao)

        # Página
        chars = 0
        pagina = 1
        for num in sorted(self.texto_por_pagina.keys()):
            texto = self.texto_por_pagina[num]
            if chars + len(texto) > pos:
                pagina = num + 1
                break
            chars += len(texto)

        return PericiaExtraida(
            nome=nome_limpo,
            custo="2 pontos",
            descricao=descricao,
            especializacoes=especializacoes,
            pagina=pagina,
            livro=self.nome_livro,
        )


def main() -> None:
    # Usar dados canônicos (descrições corretas do Manual Turbinado)
    base = Path(__file__).resolve().parent.parent
    canonico_path = base / "data/processed/pericias/pericias_canonico.json"
    usar_canonico = canonico_path.exists()

    pdfs = _encontrar_pdfs_pericias()
    if not pdfs and not usar_canonico:
        print("Nenhum PDF encontrado e sem dados canônicos.")
        return

    if usar_canonico:
        print("Usando dados canônicos (pericias_canonico.json) como base.")
    print(f"PDFs disponíveis: {len(pdfs)}")
    for p in pdfs[:5]:
        print(f"  - {p.name}")
    if len(pdfs) > 5:
        print(f"  ... e mais {len(pdfs) - 5}")

    resultados: list[PericiaExtraida] = []

    # Se temos canônico, usar como base
    if usar_canonico:
        canonico = json.loads(canonico_path.read_text(encoding="utf-8"))
        for c in canonico:
            if c.get("nome") in PERICIAS:
                resultados.append(PericiaExtraida(
                    nome=c["nome"],
                    custo=c.get("custo", "2 pontos"),
                    descricao=c.get("descricao", ""),
                    especializacoes=c.get("especializacoes", []),
                    pagina=0,
                    livro=c.get("livro", "Manual 3D&T Turbinado (canônico)"),
                ))
        print(f"Carregadas {len(resultados)} Perícias do canônico.")
    else:
        visto: set[str] = set()
        for pdf_path in pdfs:
            try:
                extrator = ExtratorPericias(pdf_path)
            except Exception as e:
                print(f"Erro ao abrir {pdf_path.name}: {e}")
                continue

            achadas = 0
            for nome in PERICIAS:
                if nome in visto:
                    continue
                item = extrator.extrair_pericia(nome)
                if item and len(item.descricao) >= 50 and not _qualidade_ocr_ruim(item.descricao):
                    resultados.append(item)
                    visto.add(nome)
                    achadas += 1

            extrator.close()
            if achadas > 0:
                print(f"\n{pdf_path.name}: {achadas} Perícias")

            if len(visto) >= len(PERICIAS):
                break

    out_dir = Path("data/processed/pericias")
    out_dir.mkdir(parents=True, exist_ok=True)

    dados = [asdict(r) for r in resultados]
    with (out_dir / "pericias_extraidas.json").open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    # Relatório
    linhas = ["=" * 60, "PERÍCIAS 3D&T", "=" * 60, ""]
    for p in resultados:
        linhas.append(f"--- {p.nome} ---")
        linhas.append(f"  Custo: {p.custo} | Livro: {p.livro} | pg: {p.pagina}")
        linhas.append(f"  Descrição: {(p.descricao or '')[:200]}...")
        if p.especializacoes:
            linhas.append(f"  Especializações: {', '.join(p.especializacoes)}")
        linhas.append("")
    (out_dir / "pericias_por_grupo.txt").write_text("\n".join(linhas), encoding="utf-8")

    print(f"\n{'='*60}")
    print("RESULTADO")
    print(f"{'='*60}")
    print(f"Extraídas: {len(resultados)}/{len(PERICIAS)}")
    print(f"Salvo em {out_dir}/")


if __name__ == "__main__":
    main()
