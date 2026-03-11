"""
Normalização e validação de tabelas extraídas do 3D&T.
Padroniza formatos, valida consistência e enriquece dados.
Alinhado com table_extractor (table_type: stats, magias, equipamentos, unknown).
"""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, asdict, fields
from datetime import datetime
from enum import Enum
import logging


class TableType(Enum):
    """Tipos de tabela do sistema 3D&T (valores alinhados com table_extractor)."""
    STATS = "stats"
    MAGIAS = "magias"
    EQUIPAMENTOS = "equipamentos"
    MONSTROS = "monstros"
    PERICIAS = "pericias"
    RACAS = "racas"
    DESCONHECIDO = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "TableType":
        """Converte string do extrator para enum."""
        try:
            return cls(value) if value else cls.DESCONHECIDO
        except ValueError:
            return cls.DESCONHECIDO

    @classmethod
    def detect_from_headers(cls, headers: List[str]) -> "TableType":
        """Detecta tipo baseado nos headers."""
        header_set = set(h.upper() for h in headers if h)

        stats_cols = {"F", "H", "R", "A", "PV", "PM", "FOR", "HAB", "RES", "ARM"}
        if len(stats_cols & header_set) >= 3:
            return cls.STATS

        magia_cols = {"CUSTO", "PM", "DURAÇÃO", "ALCANCE", "ESCOLA", "ELEMENTO", "CÍRCULO", "CIRCULO"}
        if len(magia_cols & header_set) >= 2:
            return cls.MAGIAS

        equip_cols = {"PE", "PREÇO", "BÔNUS", "BONUS", "DANO", "DEFESA", "ALCANCE"}
        if len(equip_cols & header_set) >= 2:
            return cls.EQUIPAMENTOS

        pericia_cols = {"CUSTO", "PERÍCIA", "PERICIA", "HABILIDADE", "REQUISITO"}
        if len(pericia_cols & header_set) >= 2:
            return cls.PERICIAS

        return cls.DESCONHECIDO


@dataclass
class NormalizedStats:
    """Stats normalizados de criatura/personagem."""
    nome: str
    forca: int
    habilidade: int
    resistencia: int
    armadura: int
    pv: int
    pm: int
    nivel: Optional[int] = None
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    habilidades_especiais: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.habilidades_especiais is None:
            self.habilidades_especiais = []

    @property
    def poder_combate(self) -> int:
        """Calcula poder de combate aproximado."""
        return self.forca + self.habilidade + self.resistencia + (self.pv // 10)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "poder_combate": self.poder_combate,
        }


@dataclass
class NormalizedMagia:
    """Magia normalizada."""
    nome: str
    custo_pm: int
    circulo: Optional[int]
    duracao: str
    alcance: str
    escola: Optional[str]
    elemento: Optional[str]
    descricao: str
    efeito_mecanico: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedEquipamento:
    """Equipamento normalizado."""
    nome: str
    tipo: str
    pe: Optional[int]
    preco: Optional[int]
    bonus: Optional[int]
    dano: Optional[str]
    defesa: Optional[int]
    alcance: Optional[str]
    descricao: Optional[str]
    requisitos: Optional[str] = None

    @property
    def is_arma(self) -> bool:
        return self.tipo.lower() in ("arma", "armas") or self.dano is not None

    @property
    def is_armadura(self) -> bool:
        return self.tipo.lower() in ("armadura", "armaduras", "escudo", "escudos") or self.defesa is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "categoria": "arma" if self.is_arma else ("armadura" if self.is_armadura else "item"),
        }


def _dataclass_from_dict(klass: type, data: Dict[str, Any]) -> Any:
    """Cria instância de dataclass a partir de dict, apenas com campos válidos."""
    valid = {f.name for f in fields(klass)}
    return klass(**{k: v for k, v in data.items() if k in valid})


class TableNormalizer:
    """
    Normaliza e valida tabelas extraídas do 3D&T.
    Espera dicionários no formato de ExtractedTable.to_dict().
    """

    COLUMN_MAPPINGS = {
        "FOR": "forca", "FORÇA": "forca", "F": "forca", "FORCA": "forca", "STR": "forca",
        "HAB": "habilidade", "HABILIDADE": "habilidade", "H": "habilidade",
        "DES": "habilidade", "DESTREZA": "habilidade", "DEX": "habilidade",
        "RES": "resistencia", "RESISTÊNCIA": "resistencia", "R": "resistencia",
        "RESISTENCIA": "resistencia", "CON": "resistencia", "CONSTITUIÇÃO": "resistencia",
        "ARM": "armadura", "ARMADURA": "armadura", "A": "armadura", "DEF": "armadura", "DEFESA": "armadura",
        "PV": "pv", "PVS": "pv", "VIDA": "pv", "HP": "pv",
        "PM": "pm", "PMS": "pm", "MANA": "pm", "MP": "pm",
        "CUSTO": "custo_pm", "CUSTO PM": "custo_pm", "CUSTOPM": "custo_pm", "CUSTO_PM": "custo_pm",
        "CÍRCULO": "circulo", "CIRCULO": "circulo", "NÍVEL": "circulo", "NIVEL": "circulo",
        "DURAÇÃO": "duracao", "DURACAO": "duracao", "DURAÇAO": "duracao",
        "ALCANCE": "alcance", "ALC": "alcance",
        "ESCOLA": "escola", "ELEMENTO": "elemento", "ELEM": "elemento",
        "PE": "pe", "PREÇO": "preco", "PRECO": "preco", "CUSTO PE": "pe",
        "BÔNUS": "bonus", "BONUS": "bonus", "BÔNUS DE ATAQUE": "bonus",
        "DANO": "dano", "DAN": "dano", "DAMAGE": "dano",
        "NOME": "nome", "NOM": "nome", "NAME": "nome",
        "DESCRIÇÃO": "descricao", "DESCRICAO": "descricao", "DESC": "descricao",
        "TIPO": "tipo", "TIP": "tipo",
        "HABILIDADES": "habilidades_especiais", "HAB. ESPECIAIS": "habilidades_especiais",
        "ESPECIAL": "habilidades_especiais", "REQUISITO": "requisitos",
    }

    VALID_RANGES = {
        "forca": (1, 100),
        "habilidade": (1, 100),
        "resistencia": (1, 100),
        "armadura": (0, 50),
        "pv": (1, 1000),
        "pm": (0, 500),
        "circulo": (1, 5),
        "custo_pm": (0, 100),
    }

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.validation_errors: List[Dict[str, Any]] = []
        self.normalization_stats: Dict[str, Any] = {
            "processed": 0,
            "normalized": 0,
            "rejected": 0,
            "by_type": {},
        }

    def normalize_table(self, table_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normaliza uma tabela extraída (formato ExtractedTable.to_dict()).

        Returns:
            Tabela normalizada ou None se inválida.
        """
        self.normalization_stats["processed"] += 1

        table_type = TableType.from_string(table_data.get("table_type", "unknown"))

        normalized_headers = self._normalize_headers(table_data.get("headers", []))
        normalized_rows: List[Any] = []

        for row in table_data.get("rows", []):
            cells = row.get("cells", row) if isinstance(row, dict) else {}
            try:
                normalized = self._normalize_row(cells, normalized_headers, table_type)
                if normalized is not None:
                    normalized_rows.append(normalized)
            except Exception as e:
                self.logger.warning("Erro ao normalizar linha: %s", e)
                continue

        if not normalized_rows:
            self.normalization_stats["rejected"] += 1
            return None

        self.normalization_stats["normalized"] += 1
        t_val = table_type.value
        self.normalization_stats["by_type"][t_val] = (
            self.normalization_stats["by_type"].get(t_val, 0) + 1
        )

        return {
            "source": table_data.get("source"),
            "page": table_data.get("page"),
            "table_type": table_type.value,
            "title": table_data.get("title"),
            "headers": normalized_headers,
            "rows": [
                r.to_dict() if hasattr(r, "to_dict") else r
                for r in normalized_rows
            ],
            "row_count": len(normalized_rows),
            "normalized_at": datetime.now().isoformat(),
        }

    def _normalize_headers(self, headers: List[str]) -> List[str]:
        """Normaliza nomes de colunas para padrão."""
        normalized = []
        for h in headers:
            raw = (h or "").strip()
            h_clean = re.sub(r"[^\w\s]", "", raw).upper().strip()
            h_compact = h_clean.replace(" ", "")
            norm = (
                self.COLUMN_MAPPINGS.get(h_clean)
                or self.COLUMN_MAPPINGS.get(h_compact)
                or (h_clean.lower() if h_clean else "")
            )
            if norm:
                normalized.append(norm)
        return normalized or [raw.strip().lower() for raw in headers if raw]

    def _normalize_row(
        self,
        cells: Dict[str, Any],
        headers: List[str],
        table_type: TableType,
    ) -> Optional[Any]:
        """Normaliza uma linha conforme o tipo de tabela."""
        mapped: Dict[str, Any] = {}
        for header, value in cells.items():
            h_clean = re.sub(r"[^\w\s]", "", (header or "").strip()).upper().replace(" ", "")
            norm_header = self.COLUMN_MAPPINGS.get(h_clean, (header or "").lower())
            if norm_header:
                mapped[norm_header] = self._parse_value(value, norm_header)

        if table_type == TableType.STATS:
            return self._normalize_stats_row(mapped)
        if table_type == TableType.MAGIAS:
            return self._normalize_magia_row(mapped)
        if table_type == TableType.EQUIPAMENTOS:
            return self._normalize_equipamento_row(mapped)
        return mapped

    def _parse_value(self, value: Any, field: str) -> Any:
        """Parseia valor conforme o campo."""
        if value is None:
            return None
        str_value = str(value).strip()
        numeric_fields = {
            "forca", "habilidade", "resistencia", "armadura",
            "pv", "pm", "circulo", "custo_pm", "pe", "preco", "bonus", "defesa",
        }
        if field in numeric_fields:
            match = re.search(r"(\d+)", str_value.replace(".", "").replace(",", ""))
            return int(match.group(1)) if match else None
        if field == "dano":
            return self._normalize_dano(str_value)
        return str_value

    def _normalize_dano(self, dano_str: str) -> Optional[str]:
        """Normaliza string de dano (ex: 1d6, 2d8+3)."""
        if not dano_str:
            return None
        match = re.search(r"(\d+d\d+(?:[+\-]\d+)?)", dano_str, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        match = re.search(r"(\d+)", dano_str)
        return match.group(1) if match else dano_str

    def _normalize_stats_row(self, mapped: Dict[str, Any]) -> Optional[NormalizedStats]:
        """Normaliza linha de stats."""
        required = ["nome", "forca", "habilidade", "resistencia", "armadura", "pv"]
        for field in required:
            if mapped.get(field) is None and field != "pm":
                if field == "pm":
                    continue
                self.logger.debug("Campo obrigatório ausente: %s", field)
                return None

        for field, (min_val, max_val) in self.VALID_RANGES.items():
            if field in mapped and mapped[field] is not None:
                try:
                    val = int(mapped[field])
                    mapped[field] = max(min(val, max_val), min_val)
                except (TypeError, ValueError):
                    pass

        return NormalizedStats(
            nome=mapped.get("nome") or "Desconhecido",
            forca=mapped.get("forca", 1),
            habilidade=mapped.get("habilidade", 1),
            resistencia=mapped.get("resistencia", 1),
            armadura=mapped.get("armadura", 0),
            pv=mapped.get("pv", 1),
            pm=mapped.get("pm", 0),
            nivel=mapped.get("nivel"),
            tipo=mapped.get("tipo"),
            descricao=mapped.get("descricao"),
            habilidades_especiais=self._parse_list_field(mapped.get("habilidades_especiais")),
        )

    def _normalize_magia_row(self, mapped: Dict[str, Any]) -> Optional[NormalizedMagia]:
        """Normaliza linha de magia."""
        if not mapped.get("nome"):
            return None
        return NormalizedMagia(
            nome=mapped.get("nome"),
            custo_pm=mapped.get("custo_pm", 0),
            circulo=mapped.get("circulo"),
            duracao=mapped.get("duracao") or "Instantânea",
            alcance=mapped.get("alcance") or "Toque",
            escola=mapped.get("escola"),
            elemento=mapped.get("elemento"),
            descricao=mapped.get("descricao") or "",
            efeito_mecanico=mapped.get("efeito_mecanico"),
        )

    def _normalize_equipamento_row(self, mapped: Dict[str, Any]) -> Optional[NormalizedEquipamento]:
        """Normaliza linha de equipamento."""
        if not mapped.get("nome"):
            return None
        tipo = mapped.get("tipo") or "item"
        if tipo == "item":
            tipo = "arma" if mapped.get("dano") else ("armadura" if mapped.get("defesa") else "item")
        return NormalizedEquipamento(
            nome=mapped.get("nome"),
            tipo=tipo,
            pe=mapped.get("pe"),
            preco=mapped.get("preco"),
            bonus=mapped.get("bonus"),
            dano=mapped.get("dano"),
            defesa=mapped.get("defesa"),
            alcance=mapped.get("alcance"),
            descricao=mapped.get("descricao"),
            requisitos=mapped.get("requisitos"),
        )

    def _parse_list_field(self, value: Any) -> List[str]:
        """Parseia campo que pode ser lista."""
        if not value:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        if isinstance(value, str):
            return [v.strip() for v in re.split(r"[,;\n]", value) if v.strip()]
        return []

    def validate_consistency(self, normalized_tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Valida consistência entre tabelas normalizadas."""
        report: Dict[str, Any] = {
            "total_tables": len(normalized_tables),
            "errors": [],
            "warnings": [],
            "stats": {"stats": 0, "magias": 0, "equipamentos": 0},
        }
        names_by_type: Dict[str, Set[str]] = {}

        for table in normalized_tables:
            t_type = table.get("table_type", "unknown")
            names_by_type.setdefault(t_type, set())

            for row in table.get("rows", []):
                if not isinstance(row, dict) or "nome" not in row:
                    continue
                nome = row.get("nome")
                if not nome:
                    continue
                if nome in names_by_type[t_type]:
                    report["warnings"].append({
                        "type": "duplicate_name",
                        "table_type": t_type,
                        "name": nome,
                        "source": table.get("source"),
                    })
                names_by_type[t_type].add(nome)

            if t_type in report["stats"]:
                report["stats"][t_type] += table.get("row_count", 0)

        for table in normalized_tables:
            if table.get("table_type") != "magias":
                continue
            for row in table.get("rows", []):
                if not isinstance(row, dict):
                    continue
                custo = row.get("custo_pm", 0) or 0
                circulo = row.get("circulo", 1) or 1
                if custo > circulo * 10:
                    report["warnings"].append({
                        "type": "high_cost_spell",
                        "spell": row.get("nome"),
                        "custo": custo,
                        "circulo": circulo,
                    })

        return report


class TableEnricher:
    """Enriquece tabelas com dados derivados e metadados."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def enrich_stats(self, stats: NormalizedStats) -> Dict[str, Any]:
        """Adiciona informações derivadas a stats de criatura."""
        data = stats.to_dict()
        data["iniciativa"] = stats.habilidade
        data["ataque_fisico"] = stats.forca + stats.habilidade
        data["dano_bonus"] = stats.forca // 2
        data["resistencia_magia"] = stats.resistencia
        poder = stats.poder_combate
        data["categoria_poder"] = (
            "Fraco" if poder < 10 else "Médio" if poder < 30 else "Forte" if poder < 60 else "Épico"
        )
        data["xp_sugerido"] = poder * 10
        return data

    def enrich_magia(self, magia: NormalizedMagia) -> Dict[str, Any]:
        """Enriquece dados de magia."""
        data = magia.to_dict()
        combat_keywords = ["dano", "ataque", "ferimento", "destruir", "matar"]
        desc_lower = (magia.descricao or "").lower()
        data["is_combate"] = any(kw in desc_lower for kw in combat_keywords)
        if magia.circulo:
            custo_min, custo_max = magia.circulo * 2, magia.circulo * 5
            data["custo_dentro_padrao"] = custo_min <= magia.custo_pm <= custo_max
        return data

    def enrich_equipamento(self, equip: NormalizedEquipamento) -> Dict[str, Any]:
        """Enriquece dados de equipamento."""
        data = equip.to_dict()
        if equip.pe and equip.pe > 0:
            if equip.dano:
                dano_medio = self._calcular_dano_medio(equip.dano)
                if dano_medio is not None:
                    data["eficiencia_dano_pe"] = round(dano_medio / equip.pe, 2)
            if equip.defesa is not None:
                data["eficiencia_defesa_pe"] = round(equip.defesa / equip.pe, 2)
        if equip.is_arma and equip.dano:
            dano_medio = self._calcular_dano_medio(equip.dano) or 0
            data["categoria_poder"] = (
                "Leve" if dano_medio < 4 else "Média" if dano_medio < 7 else "Pesada"
            )
        return data

    def _calcular_dano_medio(self, dano_str: str) -> Optional[float]:
        """Calcula dano médio (ex: 1d6 -> 3.5)."""
        if not dano_str:
            return None
        match = re.match(r"(\d+)d(\d+)(?:([+\-])(\d+))?", dano_str, re.IGNORECASE)
        if match:
            num_dados = int(match.group(1))
            faces = int(match.group(2))
            bonus = 0
            if match.group(3) and match.group(4):
                bonus = int(match.group(4))
                if match.group(3) == "-":
                    bonus = -bonus
            return ((faces + 1) / 2) * num_dados + bonus
        try:
            return float(dano_str)
        except ValueError:
            return None


def normalize_all_tables(
    input_path: str = "data/tables/extracted_tables.json",
    output_path: str = "data/tables/normalized_tables.json",
) -> Dict[str, Any]:
    """
    Pipeline completo: lê extracted_tables.json, normaliza, enriquece e valida.
    Compatível com saída de extract_all_tables_from_corpus().
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables = data.get("tables", [])
    print(f"Carregadas {len(tables)} tabelas para normalização")

    normalizer = TableNormalizer()
    enricher = TableEnricher()
    normalized_tables: List[Dict[str, Any]] = []

    for table in tables:
        try:
            normalized = normalizer.normalize_table(table)
            if not normalized:
                continue

            enriched_rows = []
            for row in normalized["rows"]:
                if not isinstance(row, dict):
                    enriched_rows.append(row)
                    continue
                t_type = normalized["table_type"]
                try:
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
                except Exception as e:
                    normalizer.logger.debug("Enrich skip: %s", e)
                    enriched_rows.append(row)

            normalized["rows"] = enriched_rows
            normalized_tables.append(normalized)

        except Exception as e:
            print(f"Erro ao normalizar tabela: {e}")
            continue

    validation_report = normalizer.validate_consistency(normalized_tables)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "tables": normalized_tables,
                "validation": validation_report,
                "stats": normalizer.normalization_stats,
                "metadata": {
                    "normalized_at": datetime.now().isoformat(),
                    "version": "1.0",
                },
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n[OK] Normalização concluída!")
    print(f"  Tabelas normalizadas: {len(normalized_tables)}")
    print(f"  Estatísticas: {normalizer.normalization_stats}")
    print(f"  Avisos de validação: {len(validation_report['warnings'])}")
    print(f"  Salvo em: {output_path}")

    return {
        "normalized_count": len(normalized_tables),
        "stats": normalizer.normalization_stats,
        "validation": validation_report,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    normalize_all_tables()
