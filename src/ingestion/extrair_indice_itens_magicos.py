"""
Camada 1: Extração do Índice de Itens Mágicos.
Extrai nomes de itens/poderes do capítulo Objetos Mágicos (Parte 8).
Formato típico: "Nome (X PEs):" ou "Nome:" ou lista numerada.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore

# Fragmentos que indicam linha inválida (descrição, não nome de item)
_FRAGMENTOS_INVALIDOS = {
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
    "tornável", "remessável", "benefícios", "chado de batalha", "nenosa",
    "só vai fazer efeito quando", "deve ser arremessada", "não adianta esfregar",
}


def _nome_valido(nome: str) -> bool:
    """Retorna True se o nome parece um item válido (não fragmento)."""
    n = nome.strip()
    if len(n) < 4 or len(n) > 55:
        return False
    if n.endswith("-") or "..." in n or "\n" in n:
        return False
    if not n[0].isupper() and n[0] not in "0123456789":
        return False
    n_lower = n.lower()
    if any(f in n_lower for f in _FRAGMENTOS_INVALIDOS):
        return False
    return True


def _encontrar_pdfs_manuais(pdf_dir: Path) -> List[Path]:
    """Localiza TODOS os PDFs que podem conter itens (manuais, bestiário, etc.)."""
    if not pdf_dir.exists():
        return []
    pdfs = list(pdf_dir.rglob("*.pdf"))
    # Prioriza Manual da Magia
    manual_magia = [p for p in pdfs if "manual" in p.name.lower() and "magia" in p.name.lower()]
    outros = [p for p in pdfs if p not in manual_magia]
    return sorted(manual_magia) + sorted(outros)


def extrair_indice_itens_magicos(
    caminho_pdf: str | Path | None = None,
    paginas: List[int] | None = None,
) -> List[str]:
    """
    Extrai nomes de itens mágicos e poderes do capítulo Objetos Mágicos.
    Padrões: "Nome (X PEs):", "Nome:", "Força +1: 8 PEs", "Poção de X", etc.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (pip install pymupdf) necessário.")

    if caminho_pdf is None:
        from src.config import paths
        pdf_dir = paths.source_pdf_dir
        todos = _encontrar_pdfs_manuais(pdf_dir)
        if not todos:
            raise FileNotFoundError(f"Nenhum PDF encontrado em {pdf_dir}")
        # Processa todos os PDFs
        nomes: List[str] = []
        seen = set()
        for pdf_path in todos:
            try:
                n = _extrair_de_pdf(pdf_path, paginas)
                for nome in n:
                    key = nome.strip().lower()
                    if key and key not in seen:
                        seen.add(key)
                        nomes.append(nome.strip())
            except Exception:
                continue
        print(f"[Camada 1] Extraídos {len(nomes)} itens/poderes dos manuais")
        return nomes

    return _extrair_de_pdf(Path(caminho_pdf), paginas)


def _extrair_de_pdf(pdf_path: Path, paginas: List[int] | None) -> List[str]:
    """Extrai itens de um único PDF. Varre todas as páginas do livro."""
    doc = fitz.open(str(pdf_path))
    nomes: List[str] = []
    seen = set()

    # Varre TODAS as páginas do livro (não apenas 35-150)
    if paginas is None:
        paginas = list(range(len(doc)))

    # Padrões para itens/poderes (Manual da Magia)
    padroes = [
        # "Afiada (20 PEs):" ou "Vorpal (30 PEs):"
        re.compile(r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*\((\d+)\s*PEs?\)\s*:", re.IGNORECASE),
        # "Força +1: 8 PEs" / "Resistência +2: 2 PMs"
        re.compile(r"((?:Força|Habilidade|Resistência|Armadura|PdF)\s*\+\s*\d+)\s*:\s*\d+\s*(?:PEs?|PMs?)", re.IGNORECASE),
        # "Poção de X" / "Anel de X" / "Pergaminho de X"
        re.compile(r"((?:Poção|Pergaminho|Elixir|Óleo|Pomada|Anel|Cajado|Bastão)\s+(?:de\s+|da\s+|do\s+)?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']*?)(?:\s*:\s*\d+\s*PEs?|\s*$|\n)", re.IGNORECASE),
        # "Nome:" no início de linha (poderes curtos)
        re.compile(r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{3,40}?)\s*\(\d+\s*PEs?\)", re.MULTILINE | re.IGNORECASE),
        # "Nome: X PEs." (Poção do Amor: 50 PEs.)
        re.compile(r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']+?)\s*:\s*\d+\s*PEs?\s*\.", re.IGNORECASE),
        # "Escudo de X" / "Armadura de X" / "Botas de X" / "Manto de X"
        re.compile(r"((?:Escudo|Armadura|Cota|Loriga|Peitoral|Botas|Manto|Capa|Chapéu|Elmo|Manoplas|Cinto|Cinturão)\s+(?:de\s+|da\s+|do\s+)?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']*?)(?:\s*\.|\s*$|\n)", re.IGNORECASE),
        # "Adaga de X" / "Espada de X" (armas nomeadas)
        re.compile(r"((?:Adaga|Espada|Arco|Lança|Maça|Flecha|Tridente|Marreta|Sabre|Chicote)\s+(?:de\s+|da\s+|do\s+)?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']*?)(?:\s*\.|\s*$|\n)", re.IGNORECASE),
        # Título em linha isolada seguido de "Preço:" ou "Tipo:"
        re.compile(r"\n([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-']{4,45}?)\s*\n\s*(?:Preço|Tipo|Bônus|Custo)\s*:", re.IGNORECASE),
    ]

    try:
        for num_pag in paginas:
            if num_pag >= len(doc):
                continue
            texto = doc[num_pag].get_text()
            # Em livros sem "Objetos Mágicos", busca por indicadores de itens
            # Manual da Magia: Objetos Mágicos, Preço T$
            # Alpha: mesmo formato
            # Monstros: Tesouro, Equipamento, loot em descrições
            tem_itens = (
                "Objetos Mágicos" in texto or "Objetos\nMágicos" in texto
                or "PEs" in texto or "PE " in texto
                or "Preço:" in texto or "T$" in texto
                or "Poção" in texto or "Anel" in texto or "Pergaminho" in texto
                or "Tesouro" in texto or "Equipamento" in texto or "tesouro" in texto.lower()
            )
            if not tem_itens:
                continue

            for padrao in padroes:
                for match in padrao.finditer(texto):
                    nome = match.group(1).strip()
                    if "\n" in nome:
                        nome = nome.split("\n")[-1].strip()
                    if not _nome_valido(nome):
                        continue
                    if any(x in nome.lower() for x in ["página", "capítulo", "parte", "objetos", "mágicos", "manual"]):
                        continue
                    key = nome.lower()
                    if key not in seen:
                        seen.add(key)
                        nomes.append(nome)
    finally:
        doc.close()

    return nomes


def salvar_indice(
    nomes: List[str],
    arquivo_saida: str | Path = "data/processed/indice_itens_magicos_3dt.txt",
) -> Path:
    """Salva o índice em arquivo."""
    path = Path(arquivo_saida)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i, nome in enumerate(nomes, 1):
            f.write(f"{i:03d}. {nome}\n")
    print(f"[Camada 1] Índice de itens salvo em {path}")
    return path


if __name__ == "__main__":
    try:
        nomes = extrair_indice_itens_magicos()
        if nomes:
            salvar_indice(nomes)
        else:
            print("Nenhum item encontrado. Verifique se os PDFs contêm o capítulo Objetos Mágicos.")
    except (ImportError, FileNotFoundError) as e:
        print(f"Erro: {e}")
