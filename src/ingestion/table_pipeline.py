"""
Pipeline integrado de extração, normalização e ingestão de tabelas 3D&T.
Orquestra todo o fluxo desde PDF até chunks vetorizáveis.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from src.ingestion.table_extractor import TableExtractor
from src.ingestion.table_normalizer import (
    TableNormalizer,
    TableEnricher,
    NormalizedStats,
    NormalizedMagia,
    NormalizedEquipamento,
    _dataclass_from_dict,
)
from src.ingestion.layout_aware_chunking import LayoutAwareChunker


@dataclass
class PipelineConfig:
    """Configuração do pipeline de tabelas."""
    pdf_dir: str = "data/raw"
    output_dir: str = "data/processed"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_workers: int = 4
    save_intermediates: bool = True
    validate_strict: bool = False

    min_rows_per_table: int = 2
    accepted_table_types: Optional[List[str]] = None


class TablePipeline:
    """
    Pipeline completo: PDF -> Tabelas -> Normalização -> Chunks.
    """

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()
        self.logger = logging.getLogger(__name__)

        self.extractor = TableExtractor()
        self.normalizer = TableNormalizer()
        self.enricher = TableEnricher()
        self.chunker = LayoutAwareChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            table_extractor=self.extractor,
        )

        self.stats: Dict[str, Any] = {
            "extracted": 0,
            "normalized": 0,
            "chunked": 0,
            "errors": [],
        }

    def run(self, pdf_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Executa pipeline completo."""
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print("FASE 1: EXTRAÇÃO DE TABELAS")
        print("=" * 60)
        extracted = self._extract_phase(pdf_files)
        if self.config.save_intermediates:
            self._save_json(extracted, "01_extracted_tables.json")

        print("\n" + "=" * 60)
        print("FASE 2: NORMALIZAÇÃO")
        print("=" * 60)
        normalized = self._normalize_phase(extracted)
        if self.config.save_intermediates:
            self._save_json(normalized, "02_normalized_tables.json")

        print("\n" + "=" * 60)
        print("FASE 3: GERAÇÃO DE CHUNKS")
        print("=" * 60)
        chunks = self._chunking_phase(normalized)
        self._save_json(chunks, "03_table_chunks.json")

        print("\n" + "=" * 60)
        print("FASE 4: GERAÇÃO DE ÍNDICE")
        print("=" * 60)
        index = self._generate_index(chunks, normalized)
        self._save_json(index, "table_index.json")

        print("\n" + "=" * 60)
        print("PIPELINE CONCLUÍDO")
        print("=" * 60)
        print(f"Total extraído: {self.stats['extracted']}")
        print(f"Total normalizado: {self.stats['normalized']}")
        print(f"Total chunks: {self.stats['chunked']}")
        print(f"Erros: {len(self.stats['errors'])}")

        return {
            "stats": self.stats,
            "output_files": {
                "extracted": "01_extracted_tables.json",
                "normalized": "02_normalized_tables.json",
                "chunks": "03_table_chunks.json",
                "index": "table_index.json",
            },
            "index": index,
        }

    def _extract_phase(self, pdf_files: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Fase de extração de tabelas dos PDFs."""
        all_tables: List[Dict[str, Any]] = []

        if pdf_files:
            files_to_process = [Path(f) for f in pdf_files]
        else:
            files_to_process = list(Path(self.config.pdf_dir).glob("*.pdf"))

        print(f"Processando {len(files_to_process)} arquivos...")

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._extract_single_pdf, p): p
                for p in files_to_process
            }
            for future in as_completed(futures):
                pdf_path = futures[future]
                try:
                    tables = future.result()
                    all_tables.extend(tables)
                    self.stats["extracted"] += len(tables)
                    print(f"  [OK] {pdf_path.name}: {len(tables)} tabelas")
                except Exception as e:
                    error_msg = f"Erro em {pdf_path.name}: {e}"
                    self.stats["errors"].append(error_msg)
                    print(f"  [X] {error_msg}")

        return all_tables

    def _extract_single_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extrai tabelas de um único PDF."""
        tables = self.extractor.extract_from_pdf(str(pdf_path))
        return [t.to_dict() for t in tables]

    def _normalize_phase(self, extracted_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fase de normalização das tabelas extraídas."""
        normalized: List[Dict[str, Any]] = []

        for table in extracted_tables:
            try:
                if self.config.accepted_table_types:
                    if table.get("table_type") not in self.config.accepted_table_types:
                        continue

                rows = table.get("rows", [])
                if len(rows) < self.config.min_rows_per_table:
                    continue

                norm_table = self.normalizer.normalize_table(table)
                if not norm_table:
                    continue

                enriched_rows = []
                for row in norm_table.get("rows", []):
                    enriched = self._enrich_row(row, norm_table["table_type"])
                    enriched_rows.append(enriched)

                norm_table["rows"] = enriched_rows
                norm_table["id"] = self._generate_table_id(norm_table)
                normalized.append(norm_table)
                self.stats["normalized"] += 1

            except Exception as e:
                self.logger.error("Erro na normalização: %s", e)
                if self.config.validate_strict:
                    continue

        print(f"Normalizadas: {len(normalized)}/{len(extracted_tables)} tabelas")
        return normalized

    def _enrich_row(self, row: Dict[str, Any], table_type: str) -> Dict[str, Any]:
        """Enriquece uma linha baseado no tipo (usa apenas campos válidos do dataclass)."""
        try:
            if table_type == "stats":
                stats = _dataclass_from_dict(NormalizedStats, row)
                return self.enricher.enrich_stats(stats)
            if table_type == "magias":
                magia = _dataclass_from_dict(NormalizedMagia, row)
                return self.enricher.enrich_magia(magia)
            if table_type == "equipamentos":
                equip = _dataclass_from_dict(NormalizedEquipamento, row)
                return self.enricher.enrich_equipamento(equip)
        except Exception as e:
            self.logger.warning("Erro no enriquecimento: %s", e)
        return row

    def _chunking_phase(self, normalized_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Gera chunks a partir das tabelas normalizadas."""
        chunks: List[Dict[str, Any]] = []

        for table in normalized_tables:
            table_text = self._table_to_rich_text(table)

            for idx, row in enumerate(table.get("rows", [])):
                row_chunk = self._create_row_chunk(table, row, idx)
                if row_chunk:
                    chunks.append(row_chunk)
                    self.stats["chunked"] += 1

            full_table_chunk: Dict[str, Any] = {
                "id": f"{table['id']}_full",
                "content": table_text,
                "metadata": {
                    "type": "table_full",
                    "table_id": table["id"],
                    "table_type": table["table_type"],
                    "title": table.get("title"),
                    "source": table.get("source"),
                    "page": table.get("page"),
                    "row_count": table.get("row_count", 0),
                    "is_structured": True,
                },
            }
            chunks.append(full_table_chunk)
            self.stats["chunked"] += 1

        print(f"Gerados: {len(chunks)} chunks")
        return chunks

    def _table_to_rich_text(self, table: Dict[str, Any]) -> str:
        """Converte tabela para texto rico e legível."""
        lines = []
        title = table.get("title") or "Tabela"
        lines.append(f"## {title}")
        lines.append(f"Fonte: {table.get('source')}, página {table.get('page')}")
        lines.append("")
        type_descriptions = {
            "stats": "Tabela de Atributos (F, H, R, A, PV, PM)",
            "magias": "Tabela de Magias",
            "equipamentos": "Tabela de Equipamentos",
            "monstros": "Tabela de Monstros",
            "pericias": "Tabela de Perícias",
        }
        lines.append(f"Tipo: {type_descriptions.get(table['table_type'], table['table_type'])}")
        lines.append("")
        for row in table.get("rows", []):
            if isinstance(row, dict) and row.get("nome"):
                lines.append(self._row_to_text(row, table["table_type"]))
                lines.append("")
        return "\n".join(lines)

    def _row_to_text(self, row: Dict[str, Any], table_type: str) -> str:
        """Converte uma linha para texto descritivo."""
        nome = row.get("nome", "Desconhecido")
        if table_type == "stats":
            return (
                f"**{nome}**: Força {row.get('forca', '-')}, "
                f"Habilidade {row.get('habilidade', '-')}, "
                f"Resistência {row.get('resistencia', '-')}, "
                f"Armadura {row.get('armadura', '-')}, "
                f"PV {row.get('pv', '-')}, PM {row.get('pm', '-')}. "
                f"Categoria: {row.get('categoria_poder', 'Desconhecida')}"
            )
        if table_type == "magias":
            return (
                f"**{nome}** (Círculo {row.get('circulo', '-')}, "
                f"{row.get('custo_pm', '-')} PM): "
                f"Alcance {row.get('alcance', '-')}, "
                f"Duração {row.get('duracao', '-')}. "
                f"{(row.get('descricao') or '')[:200]}"
            )
        if table_type == "equipamentos":
            if row.get("dano"):
                return (
                    f"**{nome}** (Arma): Dano {row.get('dano', '-')}, "
                    f"Bônus {row.get('bonus', 0)}, "
                    f"PE {row.get('pe', '-')}. "
                    f"{(row.get('descricao') or '')[:150]}"
                )
            return (
                f"**{nome}** ({row.get('tipo', 'Item')}): "
                f"Defesa {row.get('defesa', '-')}, "
                f"PE {row.get('pe', '-')}. "
                f"{(row.get('descricao') or '')[:150]}"
            )
        return f"**{nome}**: {json.dumps(row, ensure_ascii=False)[:300]}"

    def _create_row_chunk(
        self,
        table: Dict[str, Any],
        row: Dict[str, Any],
        row_idx: int,
    ) -> Optional[Dict[str, Any]]:
        """Cria um chunk para uma linha individual."""
        if not isinstance(row, dict) or "nome" not in row:
            return None
        content = self._row_to_text(row, table["table_type"])
        return {
            "id": f"{table['id']}_row_{row_idx}",
            "content": content,
            "metadata": {
                "type": "table_row",
                "table_id": table["id"],
                "table_type": table["table_type"],
                "table_title": table.get("title"),
                "row_index": row_idx,
                "entity_name": row.get("nome"),
                "source": table.get("source"),
                "page": table.get("page"),
                "structured_data": row,
                "is_structured": True,
            },
        }

    def _generate_table_id(self, table: Dict[str, Any]) -> str:
        """Gera ID único para tabela."""
        content = f"{table.get('source')}_{table.get('page')}_{table.get('title', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_index(
        self,
        chunks: List[Dict[str, Any]],
        tables: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Gera índice de busca otimizado."""
        index: Dict[str, Any] = {
            "by_type": {},
            "by_source": {},
            "by_name": {},
            "stats": {
                "total_chunks": len(chunks),
                "total_tables": len(tables),
                "types": {},
            },
        }
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            t_type = meta.get("table_type", "unknown")
            if t_type not in index["by_type"]:
                index["by_type"][t_type] = []
            index["by_type"][t_type].append(chunk["id"])

            source = meta.get("source", "unknown")
            if source not in index["by_source"]:
                index["by_source"][source] = []
            index["by_source"][source].append(chunk["id"])

            name = meta.get("entity_name")
            if name:
                name_lower = name.lower()
                if name_lower not in index["by_name"]:
                    index["by_name"][name_lower] = []
                index["by_name"][name_lower].append({
                    "chunk_id": chunk["id"],
                    "table_id": meta.get("table_id"),
                    "type": t_type,
                })

            index["stats"]["types"][t_type] = index["stats"]["types"].get(t_type, 0) + 1
        return index

    def _save_json(self, data: Any, filename: str) -> None:
        """Salva dados em JSON."""
        path = Path(self.config.output_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"  Salvo: {path}")


class TableQueryEngine:
    """Motor de consulta para dados de tabelas processados."""

    def __init__(self, index_path: str = "data/processed/table_index.json") -> None:
        self.index_path = Path(index_path)
        self.index: Optional[Dict[str, Any]] = None
        self.chunks: Optional[Dict[str, Any]] = None
        self._load_data()

    def _load_data(self) -> None:
        """Carrega índice e chunks."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Índice não encontrado: {self.index_path}")
        with open(self.index_path, "r", encoding="utf-8") as f:
            self.index = json.load(f)
        chunks_path = self.index_path.parent / "03_table_chunks.json"
        if chunks_path.exists():
            with open(chunks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chunks = {c["id"]: c for c in data} if isinstance(data, list) else data

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Busca entidade por nome exato ou parcial."""
        name_lower = name.lower()
        results = []
        by_name = self.index.get("by_name", {}) if self.index else {}
        if name_lower in by_name and self.chunks:
            for ref in by_name[name_lower]:
                cid = ref.get("chunk_id")
                if cid and cid in self.chunks:
                    results.append(self.chunks[cid])
        if not results and self.chunks:
            for indexed_name, refs in by_name.items():
                if name_lower in indexed_name or indexed_name in name_lower:
                    for ref in refs:
                        cid = ref.get("chunk_id")
                        if cid and cid in self.chunks:
                            results.append(self.chunks[cid])
        return results

    def find_by_type(self, table_type: str) -> List[Dict[str, Any]]:
        """Retorna todos os chunks de um tipo."""
        if not self.index or not self.chunks:
            return []
        chunk_ids = self.index.get("by_type", {}).get(table_type, [])
        return [self.chunks[cid] for cid in chunk_ids if cid in self.chunks]

    def find_by_stats_range(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Busca entidades por range de stats (forca_min, forca_max, pv_min, pv_max, etc.)."""
        results = []
        stat_chunks = self.find_by_type("stats")
        for chunk in stat_chunks:
            data = chunk.get("metadata", {}).get("structured_data", {})
            match = True
            for key, value in kwargs.items():
                if key.endswith("_min"):
                    stat = key[:-4]
                    if data.get(stat, 0) < value:
                        match = False
                        break
                elif key.endswith("_max"):
                    stat = key[:-4]
                    if data.get(stat, 999) > value:
                        match = False
                        break
            if match:
                results.append(chunk)
        return results

    def get_stats_comparison(self, name1: str, name2: str) -> Optional[Dict[str, Any]]:
        """Compara stats de duas criaturas/personagens."""
        entity1 = self.find_by_name(name1)
        entity2 = self.find_by_name(name2)
        if not entity1 or not entity2:
            return None
        data1 = entity1[0].get("metadata", {}).get("structured_data", {})
        data2 = entity2[0].get("metadata", {}).get("structured_data", {})
        comparison: Dict[str, Any] = {
            "entidade_1": data1.get("nome"),
            "entidade_2": data2.get("nome"),
            "diferencas": {},
            "vencedor": None,
        }
        stats = ["forca", "habilidade", "resistencia", "armadura", "pv", "pm"]
        pontos1 = pontos2 = 0
        for stat in stats:
            v1 = data1.get(stat, 0)
            v2 = data2.get(stat, 0)
            diff = v1 - v2
            comparison["diferencas"][stat] = {
                "valor_1": v1,
                "valor_2": v2,
                "diferenca": diff,
                "vantagem": 1 if diff > 0 else (2 if diff < 0 else 0),
            }
            if diff > 0:
                pontos1 += 1
            elif diff < 0:
                pontos2 += 1
        if pontos1 > pontos2:
            comparison["vencedor"] = data1.get("nome")
        elif pontos2 > pontos1:
            comparison["vencedor"] = data2.get("nome")
        else:
            comparison["vencedor"] = "Empate"
        return comparison


def run_full_pipeline(config: Optional[PipelineConfig] = None) -> Dict[str, Any]:
    """Executa pipeline completo com configurações padrão."""
    if config is None:
        config = PipelineConfig(
            pdf_dir="data/raw",
            output_dir="data/processed",
            save_intermediates=True,
            accepted_table_types=["stats", "magias", "equipamentos"],
        )
    pipeline = TablePipeline(config)
    return pipeline.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    result = run_full_pipeline()
    print("\nTestando consultas...")
    try:
        query = TableQueryEngine()
        goblins = query.find_by_name("goblin")
        print(f"Encontrados {len(goblins)} resultados para 'goblin'")
        magias = query.find_by_type("magias")
        magias_fogo = [m for m in magias if "fogo" in (m.get("content") or "").lower()]
        print(f"Encontradas {len(magias_fogo)} magias de fogo")
    except FileNotFoundError as e:
        print("Pular testes de consulta (índice não gerado):", e)
