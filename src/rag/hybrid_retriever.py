"""
Retriever híbrido que combina:
- Busca semântica em textos (ChromaDB existente, com embedding fine-tuned)
- Busca estruturada em tabelas (índice invertido gerado pelo TablePipeline)
- Raciocínio simples sobre entidades e regras 3D&T
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.ingestion.entity_extractor import extrair_nome_magia, indicadores_busca_magia
from src.vectorstore.chroma_store import get_vectorstore


logger = logging.getLogger(__name__)


@dataclass
class RetrievedContext:
    """Contexto recuperado unificado (texto livre + tabelas)."""

    content: str
    source: str  # 'vector_db', 'table_stats', 'table_magias', 'table_equipamentos', etc.
    score: float
    metadata: Dict[str, Any]
    entity_name: Optional[str] = None

    def is_structured(self) -> bool:
        return self.source.startswith("table_")


class HybridRetriever:
    """
    Combina busca vetorial + busca em tabelas + raciocínio simples sobre entidades.
    """

    def __init__(
        self,
        chroma_db_path: str = "data/chroma",  # mantido apenas por compatibilidade; não é usado
        table_index_path: str = "data/processed/table_index.json",
        table_chunks_path: str = "data/processed/03_table_chunks.json",
    ) -> None:
        self.logger = logging.getLogger(__name__)

        # Reutiliza o mesmo vectorstore que o restante do sistema (fine-tuned, collection 3det_rag)
        self.vector_db = get_vectorstore(use_baseline=False)

        # Carregar índice de tabelas produzido por TablePipeline
        self.table_index = self._load_json(table_index_path, {})
        self.table_chunks: List[Dict[str, Any]] = self._load_json(table_chunks_path, [])
        self.chunks_by_id: Dict[str, Dict[str, Any]] = {
            c["id"]: c for c in self.table_chunks if isinstance(c, dict) and "id" in c
        }

        # Cache de entidades (nome → lista de chunks de linha de tabela)
        self._entity_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._build_entity_cache()

    def _load_json(self, path: str, default: Any) -> Any:
        """Carrega JSON com fallback silencioso."""
        try:
            p = Path(path)
            if not p.is_absolute():
                # Assume que o script será executado a partir do root do projeto
                from src.config import paths  # import interno para evitar ciclos

                p = paths.project_root / p
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning("Arquivo não encontrado ou inválido (%s): %s", path, e)
            return default

    def _build_entity_cache(self) -> None:
        """Constrói cache de entidades com base nos chunks de tabela."""
        for chunk in self.table_chunks:
            if not isinstance(chunk, dict):
                continue
            meta = chunk.get("metadata", {}) or {}
            entity = meta.get("entity_name")
            if not entity:
                continue
            entity_lower = str(entity).lower()
            self._entity_cache.setdefault(entity_lower, []).append(chunk)

    # ------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------

    def query(self, query_text: str, top_k: int = 10) -> List[RetrievedContext]:
        """
        Query híbrida: busca em vetores + tabelas + inferência de entidades.
        Prioriza busca por nome exato quando detecta "o que é X?", "como funciona X?".
        """
        results: List[RetrievedContext] = []

        # 0) Busca prioritaria por nome de magia/entidade extraido
        nome_extraido = extrair_nome_magia(query_text)
        if nome_extraido and (
            indicadores_busca_magia(query_text)
            or "o que" in query_text.lower()
            or "como funciona" in query_text.lower()
        ):
            prioridade = self._buscar_por_nome_exato(nome_extraido, top_k=top_k)
            if prioridade:
                results.extend(prioridade)
                logger.info("Busca prioritaria por nome: '%s' -> %d resultados", nome_extraido, len(prioridade))

        # 1) Busca semântica em texto livre (Chroma)
        # Boost: quando temos nome extraido, incluir no query para melhor match
        query_vector = f"{nome_extraido} {query_text}" if nome_extraido else query_text
        vector_results = self._vector_search(query_vector, top_k=max(1, top_k // 2))
        results.extend(vector_results)

        # 2) Busca estruturada em tabelas
        table_results = self._structured_search(query_text, top_k=max(1, top_k // 2))
        results.extend(table_results)

        # 3) Inferência de entidades mencionadas na query (inclui nomes compostos)
        inferred = self._infer_entities(query_text)
        if inferred:
            inference_results = self._get_entity_contexts(inferred)
            results.extend(inference_results)

        # 4) Reranking e deduplicação
        final_results = self._rerank_and_deduplicate(results)
        return final_results[:top_k]

    # ------------------------------------------------------------
    # Busca por nome exato (magias, entidades)
    # ------------------------------------------------------------

    def _buscar_por_nome_exato(self, nome: str, top_k: int = 5) -> List[RetrievedContext]:
        """
        Busca prioritaria por nome de entidade (ex: Portal para o Saber).
        Usa busca semantica com o nome puro e entity_cache (tabelas).
        """
        results: List[RetrievedContext] = []

        # 1) Entity cache (tabelas) - match exato ou parcial
        nome_lower = nome.lower()
        for stored_name, chunks in self._entity_cache.items():
            if nome_lower == stored_name or nome_lower in stored_name or stored_name in nome_lower:
                for chunk in chunks[:2]:
                    meta = chunk.get("metadata", {}) or {}
                    results.append(
                        RetrievedContext(
                            content=chunk.get("content", ""),
                            source=f"table_{meta.get('table_type', 'unknown')}",
                            score=0.98 if nome_lower == stored_name else 0.85,
                            metadata=meta,
                            entity_name=meta.get("entity_name"),
                        )
                    )

        # 2) Busca vetorial com nome puro (encontra chunks de texto que mencionam a magia)
        try:
            docs = self.vector_db.similarity_search_with_score(nome, k=min(20, top_k * 4))
            for doc, distance in docs:
                content_lower = (doc.page_content or "").lower()
                nome_lower = nome.lower()
                # Match exato ou palavras do nome (ex: "portal" e "saber" para "Portal para o Saber")
                palavras_nome = [p for p in nome_lower.split() if len(p) > 2]
                match = nome_lower in content_lower or (
                    len(palavras_nome) >= 2 and sum(1 for p in palavras_nome if p in content_lower) >= 2
                )
                if match:
                    score = 0.95 / (1.0 + float(distance))
                    results.append(
                        RetrievedContext(
                            content=doc.page_content,
                            source="vector_db",
                            score=score,
                            metadata=doc.metadata or {},
                            entity_name=nome,
                        )
                    )
        except Exception as e:
            self.logger.debug("Busca por nome no vectorstore: %s", e)

        return results[:top_k]

    # ------------------------------------------------------------
    # Busca vetorial
    # ------------------------------------------------------------

    def _vector_search(self, query: str, top_k: int) -> List[RetrievedContext]:
        """Busca semântica no ChromaDB (texto livre)."""
        try:
            docs = self.vector_db.similarity_search_with_score(query, k=top_k)
        except Exception as e:
            self.logger.exception("Falha na busca vetorial: %s", e)
            return []

        out: List[RetrievedContext] = []
        for doc, distance in docs:
            score = 1.0 / (1.0 + float(distance))  # converter distância em similaridade
            out.append(
                RetrievedContext(
                    content=doc.page_content,
                    source="vector_db",
                    score=score,
                    metadata=doc.metadata or {},
                    entity_name=self._extract_entity_name(doc.page_content),
                )
            )
        return out

    # ------------------------------------------------------------
    # Busca estruturada em tabelas
    # ------------------------------------------------------------

    def _structured_search(self, query: str, top_k: int) -> List[RetrievedContext]:
        """Busca estruturada em tabelas (stats, magias, equipamentos)."""
        results: List[RetrievedContext] = []
        query_lower = query.lower()

        is_stats_query = any(
            kw in query_lower for kw in ["força", "habilidade", "pv", "pm", "stats", "atributos", "monstro"]
        )
        is_magia_query = any(
            kw in query_lower for kw in ["magia", "círculo", "circulo", "pm", "custo", "feitiço", "feitico"]
        )
        is_equip_query = any(
            kw in query_lower for kw in ["arma", "equipamento", "dano", "defesa", "pe", "preço", "preco"]
        )

        words = re.findall(r"\b\w+\b", query_lower)

        # 1) Match exato por entidade
        for word in words:
            if len(word) <= 3:
                continue
            chunks = self._entity_cache.get(word, [])
            for chunk in chunks[:2]:
                meta = chunk.get("metadata", {}) or {}
                results.append(
                    RetrievedContext(
                        content=chunk.get("content", ""),
                        source=f"table_{meta.get('table_type', 'unknown')}",
                        score=0.95,
                        metadata=meta,
                        entity_name=meta.get("entity_name"),
                    )
                )

        # 2) Filtro por tipo de tabela, se ainda houver espaço
        if len(results) < top_k:
            target_type: Optional[str] = None
            if is_stats_query:
                target_type = "stats"
            elif is_magia_query:
                target_type = "magias"
            elif is_equip_query:
                target_type = "equipamentos"

            if target_type:
                type_chunks = [
                    c
                    for c in self.table_chunks
                    if isinstance(c, dict)
                    and c.get("metadata", {}).get("table_type") == target_type
                    and c.get("metadata", {}).get("type") == "table_row"
                ]
                for chunk in type_chunks[:top_k]:
                    meta = chunk.get("metadata", {}) or {}
                    content = chunk.get("content", "") or ""
                    # score simples baseado em termo da query aparecendo no conteúdo
                    matched = sum(1 for w in words if w in content.lower())
                    frac = matched / max(1, len(words))
                    score = 0.5 + frac * 0.4
                    results.append(
                        RetrievedContext(
                            content=content,
                            source=f"table_{target_type}",
                            score=score,
                            metadata=meta,
                            entity_name=meta.get("entity_name"),
                        )
                    )

        return results

    # ------------------------------------------------------------
    # Inferência de entidades e contexto
    # ------------------------------------------------------------

    def _infer_entities(self, query: str) -> List[str]:
        """Infere quais entidades (nomes) são mencionadas na query. Suporta nomes compostos."""
        query_lower = query.lower()
        entities: List[str] = []

        # Nome composto: "o que é Portal para o Saber?" -> "Portal para o Saber"
        nome_magia = extrair_nome_magia(query)
        if nome_magia:
            entities.append(nome_magia.lower())

        patterns = [
            r"(?:quem [eé]|quem e|o que [eé]|o que e|como|stats? de|atributos de|magia|arma)\s+([^?]+)",
            r"(\w+)\s+(?:vs|versus|contra|ou|mais forte que)",
            r"(?:melhor|pior|mais forte|mais fraco)\s+(?:que|de|entre)?\s*(\w+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, query_lower)
            for m in matches:
                m = m.strip()
                if len(m) >= 3 and m not in ("a", "o", "e", "um", "uma", "de", "para"):
                    entities.append(m)

        words = query_lower.split()
        for word in words:
            if len(word) > 3 and word in self._entity_cache:
                entities.append(word)

        # Remover duplicatas
        return sorted(set(e for e in entities if e))

    def _get_entity_contexts(self, entities: List[str]) -> List[RetrievedContext]:
        """Recupera contextos completos (linha + tabela cheia) para entidades inferidas."""
        results: List[RetrievedContext] = []

        for entity in entities:
            entity_lower = entity.lower()
            chunks = self._entity_cache.get(entity_lower, [])
            for chunk in chunks:
                meta = chunk.get("metadata", {}) or {}
                t_type = meta.get("table_type", "unknown")
                results.append(
                    RetrievedContext(
                        content=chunk.get("content", ""),
                        source=f"table_{t_type}",
                        score=0.9,
                        metadata=meta,
                        entity_name=meta.get("entity_name"),
                    )
                )

                table_id = meta.get("table_id")
                if table_id:
                    full = self.chunks_by_id.get(f"{table_id}_full")
                    if full:
                        results.append(
                            RetrievedContext(
                                content=full.get("content", ""),
                                source=f"table_{t_type}_full",
                                score=0.7,
                                metadata=full.get("metadata", {}) or {},
                                entity_name=None,
                            )
                        )
        return results

    # ------------------------------------------------------------
    # Reranking / deduplicação
    # ------------------------------------------------------------

    def _rerank_and_deduplicate(self, results: List[RetrievedContext]) -> List[RetrievedContext]:
        """Ordena por score e remove duplicatas aproximadas."""
        seen: set[Tuple[Optional[str], str, str]] = set()
        unique: List[RetrievedContext] = []

        for r in sorted(results, key=lambda x: x.score, reverse=True):
            key = (r.entity_name, r.source, r.content[:100])
            if key in seen:
                continue
            seen.add(key)
            unique.append(r)
        return unique

    # ------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------

    def _extract_entity_name(self, text: str) -> Optional[str]:
        """Tenta extrair nome de entidade de texto não estruturado."""
        patterns = [
            r"\*\*(\w+)\*\*",  # **Nome**
            r"^(\w+):",  # Nome:
            r"(\w+)\s*\(",  # Nome (
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(1)
        return None

    # ------------------------------------------------------------
    # Funções de alto nível: comparação e recomendações
    # ------------------------------------------------------------

    def _get_entity_data(self, name: str) -> Optional[Dict[str, Any]]:
        """Recupera dados estruturados (metadata) de uma entidade pelo nome."""
        name_lower = name.lower()
        chunks = self._entity_cache.get(name_lower, [])
        if chunks:
            return chunks[0].get("metadata", {}) or {}
        for stored_name, chs in self._entity_cache.items():
            if name_lower in stored_name or stored_name in name_lower:
                if chs:
                    return chs[0].get("metadata", {}) or {}
        return None

    def compare_entities(self, name1: str, name2: str) -> Optional[Dict[str, Any]]:
        """
        Compara duas entidades (monstros, personagens etc.) usando dados estruturados.
        """
        entity1_data = self._get_entity_data(name1)
        entity2_data = self._get_entity_data(name2)
        if not entity1_data or not entity2_data:
            return None

        stats1 = entity1_data.get("structured_data", {}) or {}
        stats2 = entity2_data.get("structured_data", {}) or {}
        if not stats1 or not stats2:
            return {
                "entidade_1": name1,
                "entidade_2": name2,
                "erro": "Dados estruturados não disponíveis para comparação",
            }

        comparison: Dict[str, Any] = {
            "entidade_1": {
                "nome": stats1.get("nome", name1),
                "tipo": entity1_data.get("table_type", "unknown"),
                "stats": {
                    k: v
                    for k, v in stats1.items()
                    if k in ["forca", "habilidade", "resistencia", "armadura", "pv", "pm"]
                },
            },
            "entidade_2": {
                "nome": stats2.get("nome", name2),
                "tipo": entity2_data.get("table_type", "unknown"),
                "stats": {
                    k: v
                    for k, v in stats2.items()
                    if k in ["forca", "habilidade", "resistencia", "armadura", "pv", "pm"]
                },
            },
            "analise": {},
            "vencedor": None,
        }

        vantagens1 = vantagens2 = 0
        for stat in ["forca", "habilidade", "resistencia", "armadura", "pv", "pm"]:
            v1 = stats1.get(stat, 0)
            v2 = stats2.get(stat, 0)
            if v1 > v2:
                vantagens1 += 1
                comparison["analise"][stat] = {
                    "vantagem": stats1.get("nome", name1),
                    "diferenca": v1 - v2,
                }
            elif v2 > v1:
                vantagens2 += 1
                comparison["analise"][stat] = {
                    "vantagem": stats2.get("nome", name2),
                    "diferenca": v2 - v1,
                }

        if vantagens1 > vantagens2:
            comparison["vencedor"] = comparison["entidade_1"]["nome"]
            comparison["razao"] = f"Vantagem em {vantagens1} atributos"
        elif vantagens2 > vantagens1:
            comparison["vencedor"] = comparison["entidade_2"]["nome"]
            comparison["razao"] = f"Vantagem em {vantagens2} atributos"
        else:
            comparison["vencedor"] = "Empate técnico"
            comparison["razao"] = "Mesmo número de vantagens"

        if "forca" in stats1 and "forca" in stats2:
            poder1 = stats1.get("poder_combate", stats1.get("forca", 0) + stats1.get("habilidade", 0))
            poder2 = stats2.get("poder_combate", stats2.get("forca", 0) + stats2.get("habilidade", 0))
            if poder1 + poder2 > 0:
                comparison["analise_combate"] = {
                    "poder_combate_1": poder1,
                    "poder_combate_2": poder2,
                    "probabilidade_vitoria_1": round(poder1 / (poder1 + poder2) * 100, 1),
                    "probabilidade_vitoria_2": round(poder2 / (poder1 + poder2) * 100, 1),
                }

        return comparison

    def recommend_for_build(
        self,
        pe_budget: Optional[int] = None,
        min_forca: Optional[int] = None,
        tipo: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recomenda equipamentos com base em restrições simples (PE, força mínima, tipo).
        """
        candidates: List[Dict[str, Any]] = []

        for chunk in self.table_chunks:
            meta = chunk.get("metadata", {}) or {}
            if meta.get("table_type") != "equipamentos":
                continue

            data = meta.get("structured_data", {}) or {}
            if not data:
                continue

            if pe_budget is not None:
                pe = data.get("pe", 9999)
                if pe is None or pe > pe_budget:
                    continue

            if min_forca is not None:
                desc = (data.get("descricao") or "").lower()
                req_match = re.search(r"força\s*(\d+)|forca\s*(\d+)", desc)
                if req_match:
                    req_val = req_match.group(1) or req_match.group(2)
                    try:
                        req_forca = int(req_val)
                        if min_forca < req_forca:
                            continue
                    except ValueError:
                        pass

            if tipo is not None:
                item_tipo = (data.get("tipo") or "").lower()
                if tipo.lower() not in item_tipo:
                    continue

            eficiencia = data.get("eficiencia_dano_pe") or data.get("eficiencia_defesa_pe") or 0.0
            pe_val = data.get("pe") or 0
            score = eficiencia * 0.7 + (1.0 / (pe_val + 1)) * 0.3

            candidates.append(
                {
                    "nome": data.get("nome"),
                    "tipo": data.get("tipo"),
                    "pe": data.get("pe"),
                    "dano": data.get("dano"),
                    "defesa": data.get("defesa"),
                    "eficiencia": eficiencia,
                    "score_recomendacao": score,
                    "descricao": (data.get("descricao") or "")[:100],
                }
            )

        return sorted(candidates, key=lambda x: x["score_recomendacao"], reverse=True)


if __name__ == "__main__":
    import sys as _sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    retriever = HybridRetriever()

    if len(_sys.argv) > 1:
        query = " ".join(_sys.argv[1:])
        print(f"\n[QUERY] {query!r}")
        print("=" * 60)

        results = retriever.query(query, top_k=8)
        print(f"\n[RESULTADOS] {len(results)} encontrados:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r.source}] (score={r.score:.3f})")
            if r.entity_name:
                print(f"   Entidade: {r.entity_name}")
            print(f"   {r.content[:150]}...\n")

        if any(kw in query.lower() for kw in [" vs ", " ou ", " contra "]):
            parts = re.split(r"\s+(?:vs|ou|contra)\s+", query.lower())
            if len(parts) == 2:
                print("=" * 60)
                print("[COMPARACAO]")
                comp = retriever.compare_entities(parts[0].strip(), parts[1].strip())
                if comp:
                    print(f"\n{comp['entidade_1']['nome']} vs {comp['entidade_2']['nome']}")
                    print(f"Vencedor: {comp['vencedor']}")
                    print(f"Razão: {comp['razao']}")
                    if "analise_combate" in comp:
                        prob = comp["analise_combate"]
                        print(
                            f"Probabilidades: {prob['probabilidade_vitoria_1']}% / "
                            f"{prob['probabilidade_vitoria_2']}%"
                        )
    else:
        print('Uso: python -m src.rag.hybrid_retriever "sua pergunta"')

