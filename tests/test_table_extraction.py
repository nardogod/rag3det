"""
Testes para o pipeline de extração de tabelas.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ingestion.table_extractor import TableExtractor, ExtractedTable, TableRow
from src.ingestion.table_normalizer import (
    TableNormalizer,
    TableEnricher,
    NormalizedStats,
    NormalizedMagia,
    TableType,
)
from src.ingestion.table_pipeline import TablePipeline, PipelineConfig


class TestTableExtractor:
    """Testes para o extrator de tabelas."""

    def setup_method(self) -> None:
        self.extractor = TableExtractor()

    def test_detect_table_type_stats(self) -> None:
        """Detecta corretamente tabela de stats."""
        headers = ["NOME", "F", "H", "R", "A", "PV", "PM"]
        result = self.extractor._detect_table_type(headers)
        assert result == "stats"

    def test_detect_table_type_magias(self) -> None:
        """Detecta corretamente tabela de magias."""
        headers = ["NOME", "CUSTO", "DURAÇÃO", "ALCANCE", "ESCOLA"]
        result = self.extractor._detect_table_type(headers)
        assert result == "magias"

    def test_detect_table_type_equipamentos(self) -> None:
        """Detecta corretamente tabela de equipamentos."""
        headers = ["NOME", "PE", "DANO", "BÔNUS"]
        result = self.extractor._detect_table_type(headers)
        assert result == "equipamentos"

    def test_normalize_header(self) -> None:
        """Normaliza variações de nomes de colunas."""
        assert self.extractor._normalize_header("FORÇA") == "F"
        assert self.extractor._normalize_header("habilidade") == "H"
        assert self.extractor._normalize_header("PVS") == "PV"
        assert self.extractor._normalize_header("CUSTO PM") == "CUSTO"

    def test_parse_cell_value_numeric(self) -> None:
        """Parseia valores numéricos corretamente."""
        assert self.extractor._parse_cell_value("15", "F") == 15
        assert self.extractor._parse_cell_value("3-5", "PV") == 3
        assert self.extractor._parse_cell_value("1d6", "DANO") == "1d6"

    def test_process_table_data(self) -> None:
        """Processa dados brutos em estrutura tipada."""
        table_data = [
            ["NOME", "F", "H", "R", "A", "PV"],
            ["Goblin", "3", "4", "2", "1", "10"],
        ]
        result = self.extractor._process_table_data(
            table_data=table_data,
            source="test.pdf",
            page=1,
            title="Monstros",
        )
        assert result is not None
        assert result.table_type == "stats"
        assert len(result.rows) == 1
        assert result.rows[0].cells["NOME"] == "Goblin"
        assert result.rows[0].cells["F"] == 3


class TestTableNormalizer:
    """Testes para o normalizador."""

    def setup_method(self) -> None:
        self.normalizer = TableNormalizer()

    def test_normalize_stats_row(self) -> None:
        """Normaliza linha de stats corretamente."""
        mapped = {
            "nome": "Orc",
            "forca": 4,
            "habilidade": 2,
            "resistencia": 3,
            "armadura": 2,
            "pv": 15,
            "pm": 0,
        }
        result = self.normalizer._normalize_stats_row(mapped)
        assert isinstance(result, NormalizedStats)
        assert result.nome == "Orc"
        assert result.forca == 4
        assert result.poder_combate == 4 + 2 + 3 + 1  # F + H + R + PV//10

    def test_normalize_stats_invalid_range(self) -> None:
        """Corrige valores fora do range permitido."""
        mapped = {
            "nome": "Dragão",
            "forca": 200,
            "habilidade": 5,
            "resistencia": 100,
            "armadura": 60,
            "pv": 5000,
            "pm": 10,
        }
        result = self.normalizer._normalize_stats_row(mapped)
        assert result is not None
        assert result.forca == 100
        assert result.armadura == 50
        assert result.pv == 1000

    def test_detect_table_type_enum(self) -> None:
        """Detecta tipos usando enum."""
        assert TableType.detect_from_headers(["F", "H", "PV"]) == TableType.STATS
        assert TableType.detect_from_headers(["CUSTO", "DURAÇÃO"]) == TableType.MAGIAS
        assert TableType.detect_from_headers(["PE", "DANO"]) == TableType.EQUIPAMENTOS


class TestTableEnricher:
    """Testes para o enriquecedor."""

    def setup_method(self) -> None:
        self.enricher = TableEnricher()

    def test_enrich_stats(self) -> None:
        """Adiciona atributos derivados."""
        stats = NormalizedStats(
            nome="Guerreiro",
            forca=5,
            habilidade=4,
            resistencia=4,
            armadura=3,
            pv=25,
            pm=5,
        )
        result = self.enricher.enrich_stats(stats)
        assert result["iniciativa"] == 4
        assert result["ataque_fisico"] == 9
        assert result["dano_bonus"] == 2
        assert "categoria_poder" in result
        assert "xp_sugerido" in result

    def test_calcular_dano_medio(self) -> None:
        """Calcula dano médio corretamente."""
        assert self.enricher._calcular_dano_medio("1d6") == 3.5
        assert self.enricher._calcular_dano_medio("2d6") == 7.0
        assert self.enricher._calcular_dano_medio("1d6+2") == 5.5
        assert self.enricher._calcular_dano_medio("1d8") == 4.5


class TestTablePipeline:
    """Testes de integração do pipeline."""

    def test_pipeline_config(self) -> None:
        """Configuração é aplicada corretamente."""
        config = PipelineConfig(
            chunk_size=500,
            min_rows_per_table=3,
            accepted_table_types=["stats"],
        )
        pipeline = TablePipeline(config)
        assert pipeline.config.chunk_size == 500
        assert pipeline.chunker.chunk_size == 500

    def test_generate_table_id(self) -> None:
        """Gera IDs consistentes."""
        pipeline = TablePipeline()
        table = {
            "source": "manual.pdf",
            "page": 42,
            "title": "Monstros",
        }
        id1 = pipeline._generate_table_id(table)
        id2 = pipeline._generate_table_id(table)
        assert id1 == id2
        assert len(id1) == 12

    def test_table_to_rich_text(self) -> None:
        """Converte tabela para texto rico."""
        pipeline = TablePipeline()
        table = {
            "title": "Monstros Básicos",
            "source": "manual.pdf",
            "page": 10,
            "table_type": "stats",
            "rows": [
                {
                    "nome": "Goblin",
                    "forca": 3,
                    "habilidade": 4,
                    "resistencia": 2,
                    "armadura": 1,
                    "pv": 8,
                    "pm": 0,
                    "categoria_poder": "Fraco",
                },
            ],
        }
        text = pipeline._table_to_rich_text(table)
        assert "## Monstros Básicos" in text
        assert "Goblin" in text
        assert "Força 3" in text
        assert "Categoria: Fraco" in text


# Fixtures


@pytest.fixture
def sample_stats_table() -> dict:
    """Retorna tabela de stats de exemplo."""
    return {
        "source": "test.pdf",
        "page": 1,
        "table_type": "stats",
        "title": "Monstros",
        "headers": ["NOME", "F", "H", "R", "A", "PV", "PM"],
        "rows": [
            {
                "cells": {
                    "NOME": "Goblin",
                    "F": "3",
                    "H": "4",
                    "R": "2",
                    "A": "1",
                    "PV": "8",
                    "PM": "0",
                },
                "raw_text": "Goblin | 3 | 4 | 2 | 1 | 8 | 0",
                "row_index": 1,
            },
        ],
        "raw_data": [
            ["NOME", "F", "H", "R", "A", "PV", "PM"],
            ["Goblin", "3", "4", "2", "1", "8", "0"],
        ],
    }


@pytest.fixture
def sample_magia_table() -> dict:
    """Retorna tabela de magias de exemplo."""
    return {
        "source": "test.pdf",
        "page": 2,
        "table_type": "magias",
        "title": "Magias de Fogo",
        "headers": ["NOME", "CUSTO", "CÍRCULO", "ALCANCE", "DURAÇÃO"],
        "rows": [
            {
                "cells": {
                    "NOME": "Bola de Fogo",
                    "CUSTO": "10",
                    "CÍRCULO": "2",
                    "ALCANCE": "10m",
                    "DURAÇÃO": "Instantânea",
                },
                "raw_text": "Bola de Fogo | 10 | 2 | 10m | Instantânea",
                "row_index": 1,
            },
        ],
        "raw_data": [
            ["NOME", "CUSTO", "CÍRCULO", "ALCANCE", "DURAÇÃO"],
            ["Bola de Fogo", "10", "2", "10m", "Instantânea"],
        ],
    }


def test_end_to_end_normalization(sample_stats_table: dict) -> None:
    """Testa fluxo completo de normalização (sem enricher; categoria_poder vem do enricher)."""
    normalizer = TableNormalizer()
    result = normalizer.normalize_table(sample_stats_table)
    assert result is not None
    assert result["table_type"] == "stats"
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row["nome"] == "Goblin"
    assert row["forca"] == 3
    assert "poder_combate" in row
