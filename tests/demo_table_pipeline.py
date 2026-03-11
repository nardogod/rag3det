"""
Demonstração do pipeline de tabelas com dados de exemplo 3D&T.
Cria dados simulados equivalentes ao que seria extraído dos PDFs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Garantir que o diretório raiz do projeto esteja no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.table_pipeline import TablePipeline, PipelineConfig
from src.ingestion.table_normalizer import (
    TableNormalizer,
    TableEnricher,
    NormalizedStats,
    NormalizedMagia,
    NormalizedEquipamento,
    _dataclass_from_dict,
)


def create_mock_extracted_data() -> list[dict]:
    """
    Cria dados simulados de extração de PDFs do 3D&T.
    Representa o que seria extraído dos PDFs reais (formato ExtractedTable.to_dict()).
    """

    monstros_table = {
        "source": "3DT_Manual_Basico.pdf",
        "page": 45,
        "table_type": "stats",
        "title": "Monstros Básicos",
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
            {
                "cells": {
                    "NOME": "Orc",
                    "F": "5",
                    "H": "3",
                    "R": "4",
                    "A": "2",
                    "PV": "15",
                    "PM": "0",
                },
                "raw_text": "Orc | 5 | 3 | 4 | 2 | 15 | 0",
                "row_index": 2,
            },
            {
                "cells": {
                    "NOME": "Troll",
                    "F": "8",
                    "H": "4",
                    "R": "8",
                    "A": "3",
                    "PV": "40",
                    "PM": "0",
                },
                "raw_text": "Troll | 8 | 4 | 8 | 3 | 40 | 0",
                "row_index": 3,
            },
            {
                "cells": {
                    "NOME": "Dragão Jovem",
                    "F": "12",
                    "H": "8",
                    "R": "10",
                    "A": "5",
                    "PV": "80",
                    "PM": "20",
                },
                "raw_text": "Dragão Jovem | 12 | 8 | 10 | 5 | 80 | 20",
                "row_index": 4,
            },
        ],
        "raw_data": [
            ["NOME", "F", "H", "R", "A", "PV", "PM"],
            ["Goblin", "3", "4", "2", "1", "8", "0"],
            ["Orc", "5", "3", "4", "2", "15", "0"],
            ["Troll", "8", "4", "8", "3", "40", "0"],
            ["Dragão Jovem", "12", "8", "10", "5", "80", "20"],
        ],
    }

    magias_table = {
        "source": "3DT_Manual_Basico.pdf",
        "page": 78,
        "table_type": "magias",
        "title": "Magias de Fogo",
        "headers": ["NOME", "CUSTO", "CÍRCULO", "ALCANCE", "DURAÇÃO", "DESCRIÇÃO"],
        "rows": [
            {
                "cells": {
                    "NOME": "Bola de Fogo",
                    "CUSTO": "10",
                    "CÍRCULO": "2",
                    "ALCANCE": "10m",
                    "DURAÇÃO": "Instantânea",
                    "DESCRIÇÃO": "Explosão de fogo que causa 2d6 de dano em área",
                },
                "raw_text": "Bola de Fogo | 10 | 2 | 10m | Instantânea | Explosão de fogo...",
                "row_index": 1,
            },
            {
                "cells": {
                    "NOME": "Mão Flamejante",
                    "CUSTO": "5",
                    "CÍRCULO": "1",
                    "ALCANCE": "Toque",
                    "DURAÇÃO": "3 turnos",
                    "DESCRIÇÃO": "Mão em chamas que causa 1d6 de dano de fogo por toque",
                },
                "raw_text": "Mão Flamejante | 5 | 1 | Toque | 3 turnos | Mão em chamas...",
                "row_index": 2,
            },
            {
                "cells": {
                    "NOME": "Parede de Fogo",
                    "CUSTO": "15",
                    "CÍRCULO": "3",
                    "ALCANCE": "30m",
                    "DURAÇÃO": "5 turnos",
                    "DESCRIÇÃO": "Cria uma parede de fogo que causa 3d6 de dano",
                },
                "raw_text": "Parede de Fogo | 15 | 3 | 30m | 5 turnos | Cria uma parede...",
                "row_index": 3,
            },
        ],
        "raw_data": [
            ["NOME", "CUSTO", "CÍRCULO", "ALCANCE", "DURAÇÃO", "DESCRIÇÃO"],
            ["Bola de Fogo", "10", "2", "10m", "Instantânea", "Explosão de fogo..."],
            ["Mão Flamejante", "5", "1", "Toque", "3 turnos", "Mão em chamas..."],
            ["Parede de Fogo", "15", "3", "30m", "5 turnos", "Cria uma parede..."],
        ],
    }

    armas_table = {
        "source": "3DT_Equipamentos.pdf",
        "page": 12,
        "table_type": "equipamentos",
        "title": "Armas Corpo a Corpo",
        "headers": ["NOME", "PE", "DANO", "BÔNUS", "DESCRIÇÃO"],
        "rows": [
            {
                "cells": {
                    "NOME": "Adaga",
                    "PE": "5",
                    "DANO": "1d4",
                    "BÔNUS": "1",
                    "DESCRIÇÃO": "Pequena e fácil de ocultar",
                },
                "raw_text": "Adaga | 5 | 1d4 | 1 | Pequena e fácil de ocultar",
                "row_index": 1,
            },
            {
                "cells": {
                    "NOME": "Espada Longa",
                    "PE": "15",
                    "DANO": "1d8",
                    "BÔNUS": "2",
                    "DESCRIÇÃO": "Arma versátil de uma mão",
                },
                "raw_text": "Espada Longa | 15 | 1d8 | 2 | Arma versátil de uma mão",
                "row_index": 2,
            },
            {
                "cells": {
                    "NOME": "Machado de Batalha",
                    "PE": "20",
                    "DANO": "1d10",
                    "BÔNUS": "1",
                    "DESCRIÇÃO": "Arma pesada, requer F 4+",
                },
                "raw_text": "Machado de Batalha | 20 | 1d10 | 1 | Arma pesada...",
                "row_index": 3,
            },
        ],
        "raw_data": [
            ["NOME", "PE", "DANO", "BÔNUS", "DESCRIÇÃO"],
            ["Adaga", "5", "1d4", "1", "Pequena e fácil de ocultar"],
            ["Espada Longa", "15", "1d8", "2", "Arma versátil de uma mão"],
            ["Machado de Batalha", "20", "1d10", "1", "Arma pesada..."],
        ],
    }

    return [monstros_table, magias_table, armas_table]


def _enrich_table_rows(table: dict, normalizer: TableNormalizer, enricher: TableEnricher) -> Optional[dict]:
    """Helper: normaliza e enriquece todas as linhas de uma tabela."""
    normalized = normalizer.normalize_table(table)
    if not normalized:
        return None

    enriched_rows: list[dict] = []
    t_type = normalized["table_type"]

    for row in normalized["rows"]:
        if t_type == "stats":
            obj = _dataclass_from_dict(NormalizedStats, row)
            enriched_rows.append(enricher.enrich_stats(obj))
        elif t_type == "magias":
            obj = _dataclass_from_dict(NormalizedMagia, row)
            enriched_rows.append(enricher.enrich_magia(obj))
        elif t_type == "equipamentos":
            obj = _dataclass_from_dict(NormalizedEquipamento, row)
            enriched_rows.append(enricher.enrich_equipamento(obj))
        else:
            enriched_rows.append(row)

    normalized["rows"] = enriched_rows
    return normalized


def demo_normalization() -> None:
    """Demonstra a normalização de tabelas."""
    print("=" * 60)
    print("DEMO: NORMALIZACAO DE TABELAS 3D&T")
    print("=" * 60)

    data = create_mock_extracted_data()
    normalizer = TableNormalizer()
    enricher = TableEnricher()

    for table in data:
        print(f"\n[TABELA] {table['title']} (pagina {table['page']})")
        print("-" * 50)

        normalized = _enrich_table_rows(table, normalizer, enricher)

        if normalized:
            print(f"[OK] Tipo: {normalized['table_type']}")
            print(f"[OK] Linhas normalizadas: {normalized['row_count']}")

            if normalized["rows"]:
                first_row = normalized["rows"][0]
                nome = first_row.get("nome", "N/A")
                print(f"\nExemplo - {nome}:")

                if normalized["table_type"] == "stats":
                    print(f"   Forca: {first_row.get('forca')}")
                    print(f"   Poder de Combate: {first_row.get('poder_combate')}")
                    print(f"   Categoria: {first_row.get('categoria_poder')}")
                    print(f"   XP Sugerido: {first_row.get('xp_sugerido')}")
                elif normalized["table_type"] == "magias":
                    print(f"   Custo: {first_row.get('custo_pm')} PM")
                    print(f"   Circulo: {first_row.get('circulo')}")
                    print(f"   Magia de combate? {'Sim' if first_row.get('is_combate') else 'Nao'}")
                elif normalized["table_type"] == "equipamentos":
                    print(f"   Dano: {first_row.get('dano')}")
                    print(f"   PE: {first_row.get('pe')}")
                    if first_row.get("eficiencia_dano_pe") is not None:
                        print(f"   Eficiencia Dano/PE: {first_row.get('eficiencia_dano_pe')}")
        else:
            print("[X] Falha na normalizacao")

    print("\n" + "=" * 60)
    print("Estatisticas de Normalizacao:")
    print(f"  Processadas: {normalizer.normalization_stats['processed']}")
    print(f"  Normalizadas: {normalizer.normalization_stats['normalized']}")
    print(f"  Rejeitadas: {normalizer.normalization_stats['rejected']}")
    print("=" * 60)


def demo_pipeline_chunks() -> list[dict]:
    """Demonstra a geração de chunks usando o TablePipeline."""
    print("\n" + "=" * 60)
    print("DEMO: GERACAO DE CHUNKS")
    print("=" * 60)

    config = PipelineConfig(
        output_dir="data/demo_processed",
        save_intermediates=True,
    )
    pipeline = TablePipeline(config)

    extracted_data = create_mock_extracted_data()

    print("\n[*] Fase 2: Normalizacao (mock)...")
    normalized: list[dict] = []
    for table in extracted_data:
        norm = pipeline.normalizer.normalize_table(table)
        if not norm:
            continue
        norm["id"] = pipeline._generate_table_id(norm)

        enriched_rows: list[dict] = []
        for row in norm["rows"]:
            enriched_rows.append(pipeline._enrich_row(row, norm["table_type"]))
        norm["rows"] = enriched_rows
        normalized.append(norm)

    print(f"   {len(normalized)} tabelas normalizadas")

    print("\n[*] Fase 3: Chunking...")
    chunks = pipeline._chunking_phase(normalized)
    print(f"   {len(chunks)} chunks gerados")

    print("\nExemplos de Chunks:")

    monstro_chunks = [c for c in chunks if "Goblin" in c.get("content", "")]
    if monstro_chunks:
        c0 = monstro_chunks[0]
        print("\n1. Monstro (Goblin):")
        print(f"   ID: {c0['id']}")
        print(f"   Tipo: {c0['metadata']['type']}")
        print(f"   Conteudo: {c0['content'][:150]}...")

    magia_chunks = [c for c in chunks if "Bola de Fogo" in c.get("content", "")]
    if magia_chunks:
        c0 = magia_chunks[0]
        print("\n2. Magia (Bola de Fogo):")
        print(f"   ID: {c0['id']}")
        print(f"   Tipo: {c0['metadata']['type']}")
        print(f"   Conteudo: {c0['content'][:150]}...")

    output_dir = Path("data/demo_processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "demo_chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Chunks salvos em: {out_path}")

    return chunks


def demo_queries() -> None:
    """Demonstra consultas básicas usando os chunks produzidos."""
    print("\n" + "=" * 60)
    print("DEMO: CONSULTAS E BUSCAS")
    print("=" * 60)

    config = PipelineConfig(output_dir="data/demo_processed")
    pipeline = TablePipeline(config)

    extracted = create_mock_extracted_data()
    normalized: list[dict] = []
    for table in extracted:
        norm = pipeline.normalizer.normalize_table(table)
        if not norm:
            continue
        norm["id"] = pipeline._generate_table_id(norm)

        enriched_rows: list[dict] = []
        for row in norm["rows"]:
            enriched_rows.append(pipeline._enrich_row(row, norm["table_type"]))
        norm["rows"] = enriched_rows
        normalized.append(norm)

    chunks = pipeline._chunking_phase(normalized)
    index = pipeline._generate_index(chunks, normalized)

    print("\n[BUSCA] Consulta 1: Buscar 'Orc'")
    orc_results = [c for c in chunks if "Orc" in c.get("content", "")]
    print(f"   Encontrados: {len(orc_results)} resultados")
    if orc_results:
        print(f"   Conteudo: {orc_results[0]['content'][:100]}...")

    print("\n[BUSCA] Consulta 2: Magias com 'fogo'")
    fogo_results = [c for c in chunks if "fogo" in c.get("content", "").lower()]
    print(f"   Encontrados: {len(fogo_results)} resultados")
    for r in fogo_results[:2]:
        nome = r["metadata"].get("entity_name", "Desconhecido")
        print(f"   - {nome}")

    print("\n[BUSCA] Consulta 3: Comparar stats (Goblin x Orc)")
    goblin_data = None
    orc_data = None
    for c in chunks:
        meta = c.get("metadata", {})
        if meta.get("entity_name") == "Goblin" and meta.get("type") == "table_row":
            goblin_data = meta.get("structured_data", {})
        if meta.get("entity_name") == "Orc" and meta.get("type") == "table_row":
            orc_data = meta.get("structured_data", {})
    if goblin_data and orc_data:
        print(f"   Goblin: F={goblin_data.get('forca')}, PV={goblin_data.get('pv')}")
        print(f"   Orc:    F={orc_data.get('forca')}, PV={orc_data.get('pv')}")
        print(
            "   Diferenca: "
            f"F +{orc_data.get('forca', 0) - goblin_data.get('forca', 0)}, "
            f"PV +{orc_data.get('pv', 0) - goblin_data.get('pv', 0)}"
        )

    print("\n[BUSCA] Consulta 4: Armas por eficiencia")
    armas = [
        c
        for c in chunks
        if c.get("metadata", {}).get("table_type") == "equipamentos"
        and c.get("metadata", {}).get("type") == "table_row"
    ]
    armas_sorted = sorted(
        armas,
        key=lambda x: x.get("metadata", {})
        .get("structured_data", {})
        .get("eficiencia_dano_pe", 0),
        reverse=True,
    )
    print("   Ranking de eficiencia (Dano/PE):")
    for a in armas_sorted[:3]:
        data = a.get("metadata", {}).get("structured_data", {})
        nome = data.get("nome", "Desconhecido")
        ef = data.get("eficiencia_dano_pe", 0)
        print(f"   - {nome}: {ef}")


def main() -> None:
    """Executa todas as demonstrações."""
    print("\n" + "=" * 60)
    print("SISTEMA 3D&T - PIPELINE DE TABELAS (DEMO)")
    print("=" * 60 + "\n")

    demo_normalization()
    demo_pipeline_chunks()
    demo_queries()

    print("\n" + "=" * 60)
    print("[OK] DEMONSTRACAO CONCLUIDA")
    print("=" * 60)
    print("\nProximos passos:")
    print("1. Coloque seus PDFs do 3D&T em: data/raw/")
    print("2. Execute: python -m src.ingestion.table_pipeline")
    print("3. Ou rode esta demo: python tests/demo_table_pipeline.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

