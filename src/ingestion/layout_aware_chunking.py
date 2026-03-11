"""
Chunking que preserva tabelas e seu contexto.
"""

from __future__ import annotations

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from src.ingestion.table_extractor import TableExtractor, ExtractedTable, TableRow


@dataclass
class TableChunk:
    """Chunk especializado que contém uma tabela."""
    text: str
    metadata: Dict[str, Any]
    table_data: Optional[ExtractedTable] = None
    context_before: str = ""
    context_after: str = ""

    def to_standard_chunk(self) -> Dict[str, Any]:
        """Converte para formato padrão de chunk."""
        return {
            "content": self.text,
            "metadata": {
                **self.metadata,
                "has_table": True,
                "table_type": self.table_data.table_type if self.table_data else "unknown",
                "table_title": self.table_data.title if self.table_data else None,
                "table_page": self.table_data.page if self.table_data else None,
                "context_before": (self.context_before or "")[:200],
                "context_after": (self.context_after or "")[:200],
            },
        }


class LayoutAwareChunker:
    """
    Divide documentos em chunks preservando tabelas intactas.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        table_extractor: Optional[TableExtractor] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.table_extractor = table_extractor or TableExtractor()

    def chunk_document(
        self,
        text: str,
        source: str,
        page: int,
        tables: Optional[List[ExtractedTable]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Divide documento em chunks, preservando tabelas.

        Args:
            text: Texto completo da página/seção
            source: Nome do documento fonte
            page: Número da página
            tables: Tabelas já extraídas desta página (opcional)

        Returns:
            Lista de chunks (dicionários com content e metadata)
        """
        if not tables:
            tables = self._extract_tables_from_text(text, source, page)

        table_positions = self._locate_tables_in_text(text, tables)
        segments = self._segment_text(text, table_positions)

        chunks: List[Dict[str, Any]] = []
        current_chunk_text: List[str] = []
        current_chunk_size = 0

        for segment in segments:
            if segment["type"] == "table":
                if current_chunk_text:
                    chunks.append(
                        self._create_text_chunk(current_chunk_text, source, page)
                    )
                    current_chunk_text = []
                    current_chunk_size = 0

                table_chunk = self._create_table_chunk(
                    segment["table"],
                    segment.get("context_before", ""),
                    segment.get("context_after", ""),
                    source,
                    page,
                )
                chunks.append(table_chunk.to_standard_chunk())

            else:
                segment_text = segment["text"]
                segment_size = len(segment_text)

                if current_chunk_size + segment_size > self.chunk_size:
                    chunks.append(
                        self._create_text_chunk(current_chunk_text, source, page)
                    )
                    overlap_text = self._get_overlap(current_chunk_text)
                    current_chunk_text = [overlap_text, segment_text]
                    current_chunk_size = len(overlap_text) + segment_size
                else:
                    current_chunk_text.append(segment_text)
                    current_chunk_size += segment_size

        if current_chunk_text:
            chunks.append(
                self._create_text_chunk(current_chunk_text, source, page)
            )

        return chunks

    def _extract_tables_from_text(
        self,
        text: str,
        source: str,
        page: int,
    ) -> List[ExtractedTable]:
        """Extrai tabelas de texto (fallback quando não vêm do PDF)."""
        tables: List[ExtractedTable] = []
        lines = text.split("\n")
        current_table: List[str] = []
        in_table = False

        for i, line in enumerate(lines):
            if re.search(r"\b\d+\s+\d+\s+\d+\s+\d+\b", line):
                if not in_table:
                    in_table = True
                    current_table = [
                        lines[i - 1] if i > 0 else "",
                    ]
            if in_table:
                current_table.append(line)
                if not line.strip() or not re.search(r"\d", line):
                    if len(current_table) > 2:
                        parsed = self._parse_text_table(current_table, source, page)
                        if parsed:
                            tables.append(parsed)
                    in_table = False
                    current_table = []

        return tables

    def _parse_text_table(
        self,
        lines: List[str],
        source: str,
        page: int,
    ) -> Optional[ExtractedTable]:
        """Parseia tabela a partir de linhas de texto."""
        if len(lines) < 2:
            return None

        rows: List[List[str]] = []
        for line in lines:
            cells = re.split(r"\s{2,}|\t", line.strip())
            cells = [c.strip() for c in cells if c.strip()]
            if cells:
                rows.append(cells)

        if len(rows) < 2:
            return None

        headers = rows[0]
        table_rows: List[TableRow] = []
        for idx, row_data in enumerate(rows[1:], start=1):
            cells = {}
            for i, h in enumerate(headers):
                if i < len(row_data):
                    cells[h] = row_data[i]
            raw_text = " | ".join(row_data)
            table_rows.append(
                TableRow(cells=cells, raw_text=raw_text, row_index=idx)
            )

        return ExtractedTable(
            source=source,
            page=page,
            table_type="unknown",
            title=None,
            headers=headers,
            rows=table_rows,
            raw_data=rows,
        )

    def _locate_tables_in_text(
        self,
        text: str,
        tables: List[ExtractedTable],
    ) -> List[Dict[str, Any]]:
        """Localiza onde cada tabela aparece no texto."""
        positions: List[Dict[str, Any]] = []

        for table in tables:
            search_terms: List[str] = []
            for row in table.rows[:5]:
                if "NOME" in row.cells and row.cells.get("NOME"):
                    search_terms.append(str(row.cells["NOME"]).strip())
                elif row.raw_text and len(row.raw_text) > 2:
                    first_part = row.raw_text.split("|")[0].strip()[:40]
                    if first_part:
                        search_terms.append(first_part)
            if table.title:
                search_terms.insert(0, table.title.strip())

            start, end = -1, -1
            for term in search_terms:
                if not term or len(term) < 2:
                    continue
                pos = text.find(term)
                if pos >= 0:
                    start = pos
                    end = pos + len(term)
                    break

            if start < 0:
                start = 0
                end = 0

            context_before = text[max(0, start - 300) : start].strip() if start > 0 else ""
            context_after = text[end : end + 300].strip() if end < len(text) else ""

            positions.append({
                "table": table,
                "start": start,
                "end": end,
                "context_before": context_before,
                "context_after": context_after,
            })

        return sorted(positions, key=lambda p: p["start"])

    def _segment_text(
        self,
        text: str,
        table_positions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Divide o texto em segmentos (trechos de texto e tabelas)."""
        if not table_positions:
            return [{"type": "text", "text": text}] if text.strip() else []

        segments: List[Dict[str, Any]] = []
        last_end = 0

        for pos in table_positions:
            start = pos["start"]
            end = pos["end"]
            table = pos["table"]

            if start > last_end:
                segment_text = text[last_end:start].strip()
                if segment_text:
                    segments.append({"type": "text", "text": segment_text})

            table_text = self._table_to_text(table)
            segments.append({
                "type": "table",
                "table": table,
                "text": table_text,
                "context_before": pos.get("context_before", ""),
                "context_after": pos.get("context_after", ""),
            })
            last_end = end

        if last_end < len(text):
            segment_text = text[last_end:].strip()
            if segment_text:
                segments.append({"type": "text", "text": segment_text})

        return segments

    def _table_to_text(self, table: ExtractedTable) -> str:
        """Converte tabela extraída em texto para o chunk."""
        parts: List[str] = []
        if table.title:
            parts.append(table.title)
        parts.append(" | ".join(h for h in table.headers if h))
        for row in table.rows:
            parts.append(row.raw_text)
        return "\n".join(parts)

    def _create_text_chunk(
        self,
        text_parts: List[str],
        source: str,
        page: int,
    ) -> Dict[str, Any]:
        """Cria chunk padrão a partir de uma lista de trechos de texto."""
        content = "\n\n".join(p for p in text_parts if p.strip())
        return {
            "content": content,
            "metadata": {
                "source": source,
                "page": page,
                "has_table": False,
            },
        }

    def _create_table_chunk(
        self,
        table: ExtractedTable,
        context_before: str,
        context_after: str,
        source: str,
        page: int,
    ) -> TableChunk:
        """Cria chunk especializado para uma tabela."""
        text = self._table_to_text(table)
        metadata: Dict[str, Any] = {
            "source": source,
            "page": page,
        }
        return TableChunk(
            text=text,
            metadata=metadata,
            table_data=table,
            context_before=context_before,
            context_after=context_after,
        )

    def _get_overlap(self, text_parts: List[str]) -> str:
        """Retorna o overlap do final do chunk atual (para continuidade)."""
        if not text_parts:
            return ""
        combined = "\n\n".join(text_parts)
        if len(combined) <= self.chunk_overlap:
            return combined
        return combined[-self.chunk_overlap :].lstrip()
