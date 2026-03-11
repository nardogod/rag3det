"""
Sistema de consulta unificado 3D&T.
Combina busca semantica (ChromaDB) + busca estruturada (tabelas) + geracao.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.generation.content_generator import ContentGenerator
from src.vectorstore.chroma_store import get_vectorstore


@dataclass
class UnifiedResult:
    """Resultado unificado de consulta."""

    tipo: str  # 'lore', 'stats', 'magia', 'equipamento', 'regra', 'gerado'
    titulo: str
    conteudo: Any
    fonte: str
    confianca: float
    acoes_sugeridas: List[str]


class UnifiedQuerySystem:
    """
    Sistema unificado de consulta 3D&T.
    Uma query -> multiplas fontes -> resposta integrada.
    """

    def __init__(
        self,
        chroma_db_path: str = "data/chroma_db",  # mantido apenas por compatibilidade
        table_chunks_path: str = "data/demo_processed/demo_chunks.json",
        use_generation: bool = True,
    ) -> None:
        self.logger = logging.getLogger(__name__)

        # 1. Busca semantica: reutiliza o vectorstore oficial do sistema
        try:
            self.vector_db = get_vectorstore(use_baseline=False)
        except Exception as e:
            self.logger.error("Falha ao carregar vectorstore: %s", e)
            raise

        # 2. Dados estruturados (mundo novo)
        self.table_chunks = self._load_table_chunks(table_chunks_path)
        self.entity_cache = self._build_entity_cache()

        # 3. Geracao (se habilitado)
        self.use_generation = use_generation
        if use_generation:
            self.generator = ContentGenerator()

        self.logger.info("Sistema unificado carregado: %d entidades", len(self.entity_cache))

    def _load_table_chunks(self, path: str) -> List[Dict[str, Any]]:
        """Carrega chunks de tabelas."""
        try:
            p = Path(path)
            if not p.is_absolute():
                from src.config import paths

                p = paths.project_root / p
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Arquivo nao encontrado: %s", path)
            return []
        except json.JSONDecodeError as e:
            self.logger.warning("JSON invalido em %s: %s", path, e)
            return []

    def _build_entity_cache(self) -> Dict[str, List[Dict[str, Any]]]:
        """Constroi cache de entidades."""
        cache: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in self.table_chunks:
            meta = chunk.get("metadata", {}) or {}
            entity = meta.get("entity_name")
            if entity:
                key = str(entity).lower()
                cache.setdefault(key, []).append(chunk)
        return cache

    def query(self, query_text: str, modo: str = "completo") -> Dict[str, Any]:
        """
        Consulta unificada principal.

        Args:
            query_text: Pergunta do usuario.
            modo: 'completo', 'rapido', 'apenas_regras', 'apenas_dados'.
        """
        query_lower = query_text.lower()
        intencao = self._analisar_intencao(query_lower)
        resultados: List[UnifiedResult] = []

        # 1. Busca semantica (sempre, para contexto)
        if modo in ["completo", "rapido", "apenas_regras"]:
            resultados.extend(self._buscar_lore(query_text))

        # 2. Busca estruturada (entidades especificas)
        if modo in ["completo", "apenas_dados"]:
            resultados.extend(self._buscar_entidades(query_lower))

        # 3. Geracao (se solicitado e habilitado)
        if self.use_generation and intencao.get("gerar"):
            resultados.extend(self._gerar_conteudo(intencao, query_text))

        return self._formatar_resposta(query_text, intencao, resultados)

    def _analisar_intencao(self, query: str) -> Dict[str, Any]:
        """Analisa o que o usuario quer."""
        intencao: Dict[str, Any] = {
            "buscar_entidade": False,
            "comparar": False,
            "gerar": False,
            "calcular": False,
            "entidades": [],
            "tipo_geracao": None,
        }

        # Detectar comparacao
        if any(kw in query for kw in [" vs ", " versus ", " contra ", " ou ", " qual melhor "]):
            intencao["comparar"] = True
            parts = re.split(r"\s+(?:vs|versus|contra|ou)\s+", query)
            intencao["entidades"] = [p.strip() for p in parts if len(p.strip()) > 2]

        # Detectar geracao
        gerar_keywords = ["crie", "gere", "genere", "monte", "preciso de", "quero um"]
        if any(kw in query for kw in gerar_keywords):
            intencao["gerar"] = True
            if "npc" in query or "personagem" in query:
                intencao["tipo_geracao"] = "npc"
            elif "encontro" in query or "combate" in query:
                intencao["tipo_geracao"] = "encontro"
            elif "aventura" in query or "historia" in query:
                intencao["tipo_geracao"] = "aventura"

        # Detectar calculo
        calc_keywords = ["quanto", "calcula", "dano medio", "probabilidade"]
        if any(kw in query for kw in calc_keywords):
            intencao["calcular"] = True

        # Detectar busca por entidade
        for palavra in query.split():
            if len(palavra) > 3 and palavra in self.entity_cache:
                intencao["buscar_entidade"] = True
                intencao["entidades"].append(palavra)

        return intencao

    def _buscar_lore(self, query: str) -> List[UnifiedResult]:
        """Busca em textos (ChromaDB)."""
        docs = self.vector_db.similarity_search_with_score(query, k=3)
        results: List[UnifiedResult] = []
        for doc, score in docs:
            confianca = 1.0 / (1.0 + float(score))
            results.append(
                UnifiedResult(
                    tipo="lore",
                    titulo=self._extrair_titulo(doc.page_content or ""),
                    conteudo=(doc.page_content or "")[:500] + "...",
                    fonte=f"{doc.metadata.get('source', 'Desconhecido')} (p. {doc.metadata.get('page', '?')})",
                    confianca=round(confianca, 3),
                    acoes_sugeridas=["Ver fonte original", "Buscar entidades mencionadas"],
                )
            )
        return results

    def _buscar_entidades(self, query: str) -> List[UnifiedResult]:
        """Busca em dados estruturados."""
        results: List[UnifiedResult] = []
        for entity_name, chunks in self.entity_cache.items():
            if entity_name in query or any(word in entity_name for word in query.split()):
                for chunk in chunks[:2]:
                    meta = chunk.get("metadata", {}) or {}
                    data = meta.get("structured_data", {}) or {}
                    if not data:
                        continue
                    tabela_tipo = meta.get("table_type", "unknown")
                    tipo_map = {
                        "stats": "stats",
                        "magias": "magia",
                        "equipamentos": "equipamento",
                    }
                    result_tipo = tipo_map.get(tabela_tipo, "dado_estruturado")
                    if result_tipo == "stats":
                        conteudo = self._formatar_stats(data)
                    elif result_tipo == "magia":
                        conteudo = self._formatar_magia(data)
                    elif result_tipo == "equipamento":
                        conteudo = self._formatar_equipamento(data)
                    else:
                        conteudo = data
                    results.append(
                        UnifiedResult(
                            tipo=result_tipo,
                            titulo=data.get("nome", "Desconhecido"),
                            conteudo=conteudo,
                            fonte=f"{meta.get('source', 'Desconhecido')} (p. {meta.get('page', '?')})",
                            confianca=0.95,
                            acoes_sugeridas=self._sugerir_acoes(data, result_tipo),
                        )
                    )
        return results

    def _formatar_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de stats para exibicao."""
        return {
            "atributos": {
                "Forca": data.get("forca", "-"),
                "Habilidade": data.get("habilidade", "-"),
                "Resistencia": data.get("resistencia", "-"),
                "Armadura": data.get("armadura", "-"),
                "PV": data.get("pv", "-"),
                "PM": data.get("pm", "-"),
            },
            "calculos_derivados": {
                "Poder de Combate": data.get("poder_combate", "-"),
                "Categoria": data.get("categoria_poder", "-"),
                "XP": data.get("xp_sugerido", "-"),
                "Iniciativa": data.get("iniciativa", "-"),
                "Ataque": data.get("ataque_fisico", "-"),
            },
            "descricao": (
                f"{data.get('nome')} - {data.get('categoria_poder', 'Desconhecido')}, "
                f"PV {data.get('pv', '-')}, bom inimigo para niveis iniciais."
            ),
        }

    def _formatar_magia(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de magia."""
        return {
            "nome": data.get("nome"),
            "custo": f"{data.get('custo_pm', '-')} PM",
            "circulo": data.get("circulo", "-"),
            "alcance": data.get("alcance", "-"),
            "duracao": data.get("duracao", "-"),
            "efeito": (data.get("descricao", "") or "")[:200],
            "combate": "Sim" if data.get("is_combate") else "Nao",
        }

    def _formatar_equipamento(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formata dados de equipamento."""
        return {
            "nome": data.get("nome"),
            "tipo": data.get("tipo"),
            "custo_pe": data.get("pe", "-"),
            "dano": data.get("dano", "-"),
            "defesa": data.get("defesa", "-"),
            "bonus": data.get("bonus", "-"),
            "eficiencia": data.get("eficiencia_dano_pe")
            or data.get("eficiencia_defesa_pe", "-"),
        }

    def _sugerir_acoes(self, data: Dict[str, Any], tipo: str) -> List[str]:
        """Sugere acoes baseadas no tipo de dado."""
        acoes: List[str] = []
        nome = data.get("nome", "")
        if tipo == "stats":
            acoes.extend(
                [
                    f"Comparar {nome} com outro monstro",
                    f"Gerar encontro com {nome}",
                    f"Ver ilustracoes de {nome}",
                ]
            )
        elif tipo == "magia":
            acoes.extend(
                [
                    f"Listar magias do mesmo circulo",
                    f"Magias similares a {nome}",
                    "Calcular dano medio",
                ]
            )
        elif tipo == "equipamento":
            acoes.extend(
                [
                    "Comparar com alternativas",
                    "Ver melhor custo-beneficio",
                    "Calcular dano medio por turno",
                ]
            )
        return acoes

    def _gerar_conteudo(self, intencao: Dict[str, Any], query: str) -> List[UnifiedResult]:
        """Gera conteudo novo se solicitado."""
        results: List[UnifiedResult] = []
        if intencao.get("tipo_geracao") == "npc":
            nivel = 1
            nivel_match = re.search(r"nivel\\s+(\\d+)", query)
            if nivel_match:
                try:
                    nivel = int(nivel_match.group(1))
                except ValueError:
                    nivel = 1
            npc = self.generator.generate_npc(nivel=nivel)
            results.append(
                UnifiedResult(
                    tipo="gerado",
                    titulo=f"NPC Gerado: {npc.nome}",
                    conteudo=npc.to_dict(),
                    fonte="Sistema de Geracao 3D&T",
                    confianca=0.9,
                    acoes_sugeridas=[
                        "Adicionar a sessao",
                        "Gerar variacao",
                        "Criar background expandido",
                    ],
                )
            )
        elif intencao.get("tipo_geracao") == "encontro":
            level = 1
            level_match = re.search(r"nivel\\s+(\\d+)", query)
            if level_match:
                try:
                    level = int(level_match.group(1))
                except ValueError:
                    level = 1
            encounter = self.generator.generate_encounter(
                party_size=4,
                party_level=level,
                dificuldade="medio",
            )
            results.append(
                UnifiedResult(
                    tipo="gerado",
                    titulo=f"Encontro para Nivel {level}",
                    conteudo=encounter,
                    fonte="Sistema de Geracao 3D&T",
                    confianca=0.85,
                    acoes_sugeridas=[
                        "Iniciar combate",
                        "Ajustar dificuldade",
                        "Gerar mapa do local",
                    ],
                )
            )
        return results

    def _formatar_resposta(
        self,
        query: str,
        intencao: Dict[str, Any],
        resultados: List[UnifiedResult],
    ) -> Dict[str, Any]:
        """Formata resposta final unificada."""
        por_tipo: Dict[str, List[UnifiedResult]] = {}
        for r in resultados:
            por_tipo.setdefault(r.tipo, []).append(r)
        for tipo, lista in por_tipo.items():
            lista.sort(key=lambda x: x.confianca, reverse=True)
        resposta: Dict[str, Any] = {
            "query_original": query,
            "intencao_detectada": intencao,
            "resumo_executivo": self._gerar_resumo(por_tipo, intencao),
            "resultados": {
                tipo: [
                    {
                        "titulo": r.titulo,
                        "conteudo": r.conteudo,
                        "fonte": r.fonte,
                        "confianca": r.confianca,
                        "acoes": r.acoes_sugeridas,
                    }
                    for r in lista
                ]
                for tipo, lista in por_tipo.items()
            },
            "sugestoes_proxima_acao": self._proximas_acoes(por_tipo, intencao),
            "meta": {
                "total_resultados": len(resultados),
                "fontes_consultadas": sorted({r.fonte for r in resultados}),
                "tem_dados_estruturados": any(
                    t in por_tipo for t in ("stats", "magia", "equipamento")
                ),
            },
        }
        return resposta

    def _gerar_resumo(
        self,
        por_tipo: Dict[str, List[UnifiedResult]],
        intencao: Dict[str, Any],
    ) -> str:
        """Gera resumo executivo da resposta (saida \"bonita\")."""
        partes: List[str] = []
        counts = {k: len(v) for k, v in por_tipo.items()}
        if counts.get("stats", 0) > 0:
            nomes = [r.titulo for r in por_tipo["stats"][:2]]
            partes.append(f"Encontrei dados de **{', '.join(nomes)}**")
        if counts.get("lore", 0) > 0:
            partes.append(f"mais **{counts['lore']} trechos de lore**")
        if counts.get("gerado", 0) > 0:
            partes.append("e gerei conteudo novo conforme solicitado")
        return " ".join(partes) if partes else "Consulta realizada"

    def _proximas_acoes(
        self,
        por_tipo: Dict[str, List[UnifiedResult]],
        intencao: Dict[str, Any],
    ) -> List[str]:
        """Sugere proximas acoes baseadas nos resultados."""
        sugestoes: List[str] = []
        if "stats" in por_tipo and por_tipo["stats"]:
            entidade = por_tipo["stats"][0].titulo
            sugestoes.append(f"Compare {entidade} com outro monstro")
        if "equipamento" in por_tipo:
            sugestoes.append("Calcule dano medio por turno")
        if "magia" in por_tipo:
            sugestoes.append("Liste magias do mesmo circulo")
        sugestoes.extend(
            [
                "Consulte as regras completas",
                "Gere um encontro com esses elementos",
            ]
        )
        return sugestoes[:4]

    def _extrair_titulo(self, texto: str) -> str:
        """Extrai titulo de texto nao estruturado."""
        for linha in texto.split("\n")[:3]:
            linha_limpa = linha.strip()
            if linha_limpa and len(linha_limpa) > 5:
                return linha_limpa[:60]
        return "Trecho do manual"


def main() -> None:
    """Interface de linha de comando simples para o sistema unificado."""
    import sys as _sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    print("======================================================================")
    print("SISTEMA UNIFICADO DE CONSULTA 3D&T")
    print("======================================================================")
    print("Inicializando... (pode levar alguns segundos)")

    sistema = UnifiedQuerySystem()

    print("✅ Sistema pronto!\n")
    queries_demo = [
        "goblin",
        "Orc vs Troll",
        "Bola de Fogo",
        "melhor arma para 20 PE",
        "crie um NPC nivel 3",
    ]
    print("Queries de demonstração disponíveis:")
    for i, q in enumerate(queries_demo, 1):
        print(f"  {i}. {q}")
    print("  0. Sair")
    print("  Ou digite sua própria query\n")

    while True:
        try:
            escolha = input("Query (número ou texto): ").strip()
            if escolha == "0":
                print("Encerrando.")
                break
            if escolha.isdigit() and 1 <= int(escolha) <= len(queries_demo):
                query = queries_demo[int(escolha) - 1]
            else:
                query = escolha

            print(f"\n🔍 Processando: '{query}'")
            print("-" * 70)

            resultado = sistema.query(query)

            print(f"\n📋 RESUMO: {resultado['resumo_executivo']}")

            for tipo, itens in resultado["resultados"].items():
                if not itens:
                    continue
                print("\n" + "─" * 70)
                print(f"📂 {tipo.upper()} ({len(itens)} resultados)")
                print("─" * 70)
                for i, item in enumerate(itens[:2], 1):
                    print(f"\n  {i}. {item['titulo']} [confianca: {item['confianca']}]")
                    conteudo = item["conteudo"]
                    if isinstance(conteudo, dict):
                        for k, v in conteudo.items():
                            if isinstance(v, dict):
                                print(f"     • {k}:")
                                for k2, v2 in v.items():
                                    print(f"       • {k2}: {v2}")
                            else:
                                print(f"     • {k}: {v}")
                    else:
                        print(f"     {str(conteudo)[:150]}...")
                    print(f"     📖 Fonte: {item['fonte']}")
                    if item["acoes"]:
                        print(f"     💡 Ações: {', '.join(item['acoes'][:2])}")

            print("\n" + "======================================================================")
            print("💡 Próximas ações sugeridas:")
            for sug in resultado["sugestoes_proxima_acao"][:3]:
                print(f"   • {sug}")
            print("======================================================================")

        except KeyboardInterrupt:
            print("\nEncerrando.")
            break
        except Exception as e:  # pragma: no cover - caminho de erro de CLI
            print(f"\n[ERRO] {e}")
            import traceback as _tb

            _tb.print_exc()
            break


if __name__ == "__main__":
    main()

