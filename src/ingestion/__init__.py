"""
Módulo de ingestão dos livros 3D&T.

- PDFs: `paths.source_pdf_dir` em `src/config.py`.
- Limpeza/chunking: `text_cleaning.py`, `chunking.py`.
- Tabelas: `table_extractor.py` -> extracted_tables.json;
  `table_normalizer.py` -> normalized_tables.json;
  `layout_aware_chunking.py` para chunks; `table_pipeline.py` orquestra o fluxo completo.
"""

from src.ingestion.table_extractor import (
    TableExtractor,
    ExtractedTable,
    TableRow,
    extract_all_tables_from_corpus,
)
from src.ingestion.layout_aware_chunking import (
    LayoutAwareChunker,
    TableChunk,
)
from src.ingestion.table_normalizer import (
    TableType,
    TableNormalizer,
    TableEnricher,
    NormalizedStats,
    NormalizedMagia,
    NormalizedEquipamento,
    normalize_all_tables,
)
from src.ingestion.table_pipeline import (
    PipelineConfig,
    TablePipeline,
    TableQueryEngine,
    run_full_pipeline,
)

__all__ = [
    "TableExtractor",
    "ExtractedTable",
    "TableRow",
    "extract_all_tables_from_corpus",
    "LayoutAwareChunker",
    "TableChunk",
    "TableType",
    "TableNormalizer",
    "TableEnricher",
    "NormalizedStats",
    "NormalizedMagia",
    "NormalizedEquipamento",
    "normalize_all_tables",
    "PipelineConfig",
    "TablePipeline",
    "TableQueryEngine",
    "run_full_pipeline",
]
