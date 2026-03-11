"""
Extrator de tabelas de PDFs do sistema 3D&T.
Suporta tabelas de stats, magias e equipamentos.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

# Tentar importar bibliotecas de PDF
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logging.warning("pdfplumber não instalado. Usando fallback regex.")

try:
    import camelot
    HAS_CAMELOT = True
except ImportError:
    HAS_CAMELOT = False
    logging.warning("camelot não instalado.")


@dataclass
class TableRow:
    """Representa uma linha de tabela com dados estruturados."""
    cells: Dict[str, Any]
    raw_text: str
    row_index: int


@dataclass
class ExtractedTable:
    """Representa uma tabela extraída de um PDF."""
    source: str
    page: int
    table_type: str  # 'stats', 'magias', 'equipamentos', 'unknown'
    title: Optional[str]
    headers: List[str]
    rows: List[TableRow]
    raw_data: List[List[str]]  # dados brutos para debug

    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        return {
            "source": self.source,
            "page": self.page,
            "table_type": self.table_type,
            "title": self.title,
            "headers": self.headers,
            "rows": [
                {
                    "cells": row.cells,
                    "raw_text": row.raw_text,
                    "row_index": row.row_index
                }
                for row in self.rows
            ]
        }


class TableExtractor:
    """Extrai tabelas de PDFs do sistema 3D&T."""

    # Padrões para detectar tipo de tabela
    STATS_HEADERS = {'F', 'H', 'R', 'A', 'PV', 'PM', 'FOR', 'HAB', 'RES', 'ARM'}
    MAGIA_HEADERS = {'CUSTO', 'PM', 'DURAÇÃO', 'ALCANCE', 'ESCOLA', 'ELEMENTO'}
    EQUIP_HEADERS = {'PE', 'PREÇO', 'BÔNUS', 'DANO', 'DEFESA'}

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_from_pdf(self, pdf_path: str) -> List[ExtractedTable]:
        """
        Extrai todas as tabelas de um PDF.

        Args:
            pdf_path: Caminho para o arquivo PDF

        Returns:
            Lista de tabelas extraídas
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        tables = []

        # Tentar pdfplumber primeiro (mais robusto)
        if HAS_PDFPLUMBER:
            tables = self._extract_with_pdfplumber(pdf_path)

        # Fallback: extração baseada em regex
        if not tables:
            tables = self._extract_with_regex(pdf_path)

        self.logger.info(f"Extraídas {len(tables)} tabelas de {pdf_path.name}")
        return tables

    def _extract_with_pdfplumber(self, pdf_path: Path) -> List[ExtractedTable]:
        """Extrai tabelas usando pdfplumber."""
        tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extrair tabelas da página
                page_tables = page.extract_tables()

                for table_data in page_tables:
                    if not table_data or len(table_data) < 2:
                        continue

                    # Detectar tipo e processar
                    extracted = self._process_table_data(
                        table_data=table_data,
                        source=pdf_path.name,
                        page=page_num,
                        title=self._extract_title(page, table_data)
                    )

                    if extracted:
                        tables.append(extracted)

        return tables

    def _extract_with_regex(self, pdf_path: Path) -> List[ExtractedTable]:
        """Fallback: extrai tabelas usando regex (quando pdfplumber falha)."""
        # Implementação simplificada para PDFs problemáticos
        tables = []

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                # Procurar padrões de tabela de stats
                stats_pattern = r'([A-Za-z\s]+)\s+(\d+)[\s\-]+(\d+)[\s\-]+(\d+)[\s\-]+(\d+)[\s\-]+(\d+)'
                matches = re.finditer(stats_pattern, text, re.MULTILINE)

                for match in matches:
                    # Criar tabela sintética
                    name = match.group(1).strip()
                    f, h, r, a, pv = match.groups()[1:]

                    table_data = [
                        ['Nome', 'F', 'H', 'R', 'A', 'PV'],
                        [name, f, h, r, a, pv]
                    ]

                    extracted = self._process_table_data(
                        table_data=table_data,
                        source=pdf_path.name,
                        page=page_num + 1,
                        title=None
                    )

                    if extracted:
                        tables.append(extracted)

            doc.close()
        except Exception as e:
            self.logger.error(f"Erro no fallback regex: {e}")

        return tables

    def _process_table_data(
        self,
        table_data: List[List[str]],
        source: str,
        page: int,
        title: Optional[str]
    ) -> Optional[ExtractedTable]:
        """Processa dados brutos de tabela em estrutura tipada."""
        if not table_data or len(table_data) < 2:
            return None

        # Limpar headers (primeira linha)
        headers = [str(h).strip().upper() if h else "" for h in table_data[0]]
        headers = [self._normalize_header(h) for h in headers]

        # Detectar tipo de tabela
        table_type = self._detect_table_type(headers)

        # Processar linhas
        rows = []
        for idx, row_data in enumerate(table_data[1:], start=1):
            if not row_data or all(not cell for cell in row_data):
                continue

            # Limpar células
            cells = {}
            raw_text = " | ".join(str(c).strip() if c else "" for c in row_data)

            for i, (header, cell) in enumerate(zip(headers, row_data)):
                if not header:
                    continue

                cell_value = self._parse_cell_value(cell, header)
                cells[header] = cell_value

            rows.append(TableRow(
                cells=cells,
                raw_text=raw_text,
                row_index=idx
            ))

        return ExtractedTable(
            source=source,
            page=page,
            table_type=table_type,
            title=title,
            headers=headers,
            rows=rows,
            raw_data=table_data
        )

    def _normalize_header(self, header: str) -> str:
        """Normaliza nome de coluna."""
        # Mapear variações para padrão
        mapping = {
            'FOR': 'F', 'FORÇA': 'F',
            'HAB': 'H', 'HABILIDADE': 'H',
            'RES': 'R', 'RESISTÊNCIA': 'R',
            'ARM': 'A', 'ARMADURA': 'A',
            'PVS': 'PV', 'VIDA': 'PV',
            'PMS': 'PM', 'MANÁ': 'PM',
            'NOME': 'NOME',
            'CUSTO': 'CUSTO', 'CUSTO PM': 'CUSTO', 'CUSTOPM': 'CUSTO',
            'DURAÇÃO': 'DURAÇÃO', 'DURACAO': 'DURAÇÃO',
            'ALCANCE': 'ALCANCE',
            'ESCOLA': 'ESCOLA',
            'ELEMENTO': 'ELEMENTO',
            'PE': 'PE', 'PREÇO': 'PE', 'PRECO': 'PE',
            'BÔNUS': 'BÔNUS', 'BONUS': 'BÔNUS',
            'DANO': 'DANO',
            'DEFESA': 'DEFESA', 'DEF': 'DEFESA'
        }

        header_clean = re.sub(r'[^\w]', '', header.upper())
        return mapping.get(header_clean, header)

    def _detect_table_type(self, headers: List[str]) -> str:
        """Detecta o tipo de tabela baseado nos headers."""
        header_set = set(h.upper() for h in headers if h)

        # Verificar stats de monstros
        if len(self.STATS_HEADERS & header_set) >= 3:
            return 'stats'

        # Verificar tabela de magias
        if len(self.MAGIA_HEADERS & header_set) >= 2:
            return 'magias'

        # Verificar equipamentos
        if len(self.EQUIP_HEADERS & header_set) >= 2:
            return 'equipamentos'

        # Heurística: se tem coluna NOME e números, provavelmente stats
        if 'NOME' in header_set:
            numeric_cols = sum(1 for h in header_set if h in self.STATS_HEADERS)
            if numeric_cols >= 2:
                return 'stats'

        return 'unknown'

    def _parse_cell_value(self, cell: Any, header: str) -> Any:
        """Parseia valor da célula baseado no tipo de coluna."""
        if cell is None:
            return None

        cell_str = str(cell).strip()

        # Dano: preservar string (ex: 1d6, 2d8+3) para normalização posterior
        if header in {"DANO", "DAN"}:
            return cell_str if cell_str else None

        # Colunas numéricas
        if header in self.STATS_HEADERS | {"CUSTO", "PE", "DEFESA"}:
            numeric_match = re.search(r"(\d+)[\-–]?(?:\d+)?", cell_str)
            if numeric_match:
                return int(numeric_match.group(1))
            return cell_str

        return cell_str

    def _extract_title(self, page, table_data: List[List[str]]) -> Optional[str]:
        """Extrai título da tabela do contexto da página."""
        try:
            # Pegar texto antes da tabela
            text = page.extract_text() or ""

            # Procurar linha em maiúsculas ou negrito antes da tabela
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if any(str(cell) in line for cell in table_data[0] if cell):
                    # Voltar algumas linhas para achar título
                    for j in range(max(0, i - 5), i):
                        candidate = lines[j].strip()
                        if candidate and len(candidate) > 3:
                            if candidate.isupper() or 'Tabela' in candidate:
                                return candidate

            return None
        except Exception:
            return None


def extract_all_tables_from_corpus(
    pdf_dir: str = "data/raw",
    output_path: str = "data/tables/extracted_tables.json"
) -> Dict:
    """
    Extrai tabelas de todos os PDFs do corpus.

    Args:
        pdf_dir: Diretório com PDFs
        output_path: Onde salvar o JSON resultante

    Returns:
        Estatísticas da extração
    """
    extractor = TableExtractor()
    all_tables = []
    stats = {
        'total_pdfs': 0,
        'total_tables': 0,
        'by_type': {},
        'by_source': {}
    }

    pdf_path = Path(pdf_dir)
    pdf_files = list(pdf_path.glob("*.pdf"))

    print(f"Processando {len(pdf_files)} PDFs...")

    for pdf_file in pdf_files:
        stats['total_pdfs'] += 1
        print(f"  {pdf_file.name}...", end=" ")

        try:
            tables = extractor.extract_from_pdf(str(pdf_file))
            all_tables.extend([t.to_dict() for t in tables])

            stats['total_tables'] += len(tables)
            stats['by_source'][pdf_file.name] = len(tables)

            for table in tables:
                t_type = table.table_type
                stats['by_type'][t_type] = stats['by_type'].get(t_type, 0) + 1

            print(f"{len(tables)} tabelas")

        except Exception as e:
            print(f"ERRO: {e}")
            stats['by_source'][pdf_file.name] = f"erro: {e}"

    # Salvar resultado
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'tables': all_tables,
            'stats': stats,
            'metadata': {
                'total_tables': len(all_tables),
                'extractor_version': '1.0'
            }
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Extração concluída!")
    print(f"  Total de tabelas: {stats['total_tables']}")
    print(f"  Por tipo: {stats['by_type']}")
    print(f"  Salvo em: {output_path}")

    return stats


if __name__ == "__main__":
    # Teste standalone
    logging.basicConfig(level=logging.INFO)

    # Extrair de um PDF específico
    # tables = TableExtractor().extract_from_pdf("data/raw/manual.pdf")
    # for t in tables:
    #     print(f"{t.table_type}: {t.title} ({len(t.rows)} linhas)")

    # Extrair de todo o corpus
    extract_all_tables_from_corpus()
