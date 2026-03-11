"""
SISTEMA 3D&T COMPLETO - Integracao Niveis 4-6
Query unica -> Analise -> Busca -> Geracao -> Memoria
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.generation.smart_generator import SmartGenerator
from src.rag.smart_reasoning import SmartReasoning, TipoConsulta
from src.session.campaign_memory import (
    CampaignMemory,
    criar_ou_carregar_campanha,
)
from src.vectorstore.chroma_store import get_vectorstore


@dataclass
class Resposta3DT:
    """Resposta completa do sistema 3D&T."""
    query_original: str
    intencao: str
    dados_recuperados: List[Dict[str, Any]]
    analise_inteligente: Dict[str, Any]
    conteudo_gerado: Optional[Dict[str, Any]]
    contexto_campanha: Optional[Dict[str, Any]]
    sugestoes: List[str]
    proximos_passos: List[str]


class Sistema3DT:
    """
    Sistema 3D&T unificado e completo.
    Integra busca, raciocinio, geracao e memoria.
    """

    def __init__(
        self,
        campaign_id: Optional[str] = None,
        campaign_name: str = "Aventura 3D&T",
    ) -> None:
        print("Inicializando Sistema 3D&T...")

        self.campanha = criar_ou_carregar_campanha(
            campaign_id, campaign_name
        )
        print(f"   Campanha: {self.campanha.nome}")

        cache = self._carregar_entity_cache()
        self.reasoning = SmartReasoning(entity_cache=cache)
        print("   Raciocinio: OK")

        self.generator = SmartGenerator(entity_cache=cache)
        print("   Geracao: OK")

        self.vector_db = get_vectorstore(use_baseline=False)
        print("   Busca semantica: OK")

        print("Sistema pronto.\n")

    def _carregar_entity_cache(self) -> Dict[str, List[Dict[str, Any]]]:
        """Carrega entidades do demo (tabelas)."""
        cache: Dict[str, List[Dict[str, Any]]] = {}
        try:
            from src.config import paths
            chunks_path = paths.project_root / "data/demo_processed/demo_chunks.json"
        except Exception:
            chunks_path = Path("data/demo_processed/demo_chunks.json")

        if chunks_path.exists():
            with chunks_path.open("r", encoding="utf-8") as f:
                chunks = json.load(f)
            for chunk in chunks:
                meta = (chunk.get("metadata") or {})
                entity = meta.get("entity_name")
                if entity:
                    key = str(entity).lower()
                    cache.setdefault(key, []).append(chunk)
        return cache

    def consultar(
        self,
        query: str,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Resposta3DT:
        """
        Consulta completa ao sistema.
        Fluxo: Analise -> Busca -> Geracao (se necessario) -> Memoria -> Resposta.
        """
        print(f"Query: '{query}'")

        analise = self.reasoning.analisar(query)
        print(f"   Intencao: {analise.tipo.value}")

        dados = self._buscar_dados(query, analise)
        print(f"   Dados: {len(dados)} resultados")

        analise_inteligente = self._analisar_dados(dados, analise)

        conteudo_gerado: Optional[Dict[str, Any]] = None
        if analise.tipo in (
            TipoConsulta.GERACAO_NPC,
            TipoConsulta.GERACAO_ENCONTRO,
        ):
            print("   Gerando conteudo...")
            contexto_geracao = {
                **(contexto or {}),
                "party_size": len(self.campanha.party_xp),
                "party_level": self._calcular_nivel_medio_party(),
                "ultimo_encontro": self._get_ultimo_encontro(),
                "tema_campanha": self.campanha.nome,
            }
            conteudo_gerado = self.generator.gerar(query, contexto_geracao)

            if conteudo_gerado.get("tipo") == "encontro":
                enc = conteudo_gerado.get("encontro", {})
                self.campanha.registrar_evento(
                    f"Encontro gerado: {enc.get('nome', '?')}",
                    tipo="preparacao",
                    envolvidos=list(self.campanha.party_xp.keys()),
                    importancia=2,
                )

        self.campanha.registrar_evento(
            f"Consulta: {query[:50]}...",
            tipo="consulta",
            envolvidos=[],
            importancia=1,
        )

        sessao = self.campanha.sessao_atual
        resposta = Resposta3DT(
            query_original=query,
            intencao=analise.intencao_principal,
            dados_recuperados=dados,
            analise_inteligente=analise_inteligente,
            conteudo_gerado=conteudo_gerado,
            contexto_campanha={
                "campanha": self.campanha.nome,
                "sessao_atual": sessao.numero if sessao else None,
                "personagens": list(self.campanha.personagens.keys()),
                "xp_party": self.campanha.party_xp,
            },
            sugestoes=self._gerar_sugestoes(
                analise, dados, conteudo_gerado
            ),
            proximos_passos=self._gerar_proximos_passos(analise),
        )
        return resposta

    def _buscar_dados(
        self, query: str, analise: Any
    ) -> List[Dict[str, Any]]:
        """Busca em vectorstore e personagens da campanha."""
        resultados: List[Dict[str, Any]] = []

        try:
            docs = self.vector_db.similarity_search(query, k=3)
            for doc in docs:
                resultados.append({
                    "fonte": "vector_db",
                    "tipo": "lore",
                    "conteudo": (doc.page_content or "")[:300],
                    "metadata": getattr(doc, "metadata", {}),
                })
        except Exception:
            pass

        for entity_name in analise.entidades:
            if entity_name in self.campanha.personagens:
                pc = self.campanha.personagens[entity_name]
                resultados.append({
                    "fonte": "campaign_memory",
                    "tipo": "personagem",
                    "conteudo": {
                        "nome": pc.nome,
                        "raca": pc.raca,
                        "nivel": pc.nivel,
                        "aparicoes": pc.aparicoes,
                        "destino": pc.destino_atual,
                    },
                    "score": 1.0,
                })

        return resultados

    def _analisar_dados(
        self, dados: List[Dict[str, Any]], analise: Any
    ) -> Dict[str, Any]:
        """Analise inteligente dos dados."""
        por_tipo: Dict[str, int] = {}
        for d in dados:
            t = d.get("tipo", "outro")
            por_tipo[t] = por_tipo.get(t, 0) + 1
        return {
            "total_resultados": len(dados),
            "distribuicao": por_tipo,
            "entidades_principais": analise.entidades,
            "parametros_detectados": analise.parametros,
            "recomendacao_geral": analise.sugestao_acao,
        }

    def _gerar_sugestoes(
        self,
        analise: Any,
        dados: List[Dict[str, Any]],
        gerado: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Gera sugestoes contextuais."""
        sugestoes: List[str] = []

        if analise.tipo == TipoConsulta.BUSCA_ENTIDADE and analise.entidades:
            e0 = analise.entidades[0]
            sugestoes.append(f"Compare {e0} com outros monstros")
            sugestoes.append(f"Gere encontro com {e0}")

        elif analise.tipo == TipoConsulta.COMPARACAO:
            sugestoes.append("Simule combate entre eles")
            sugestoes.append("Gere encontro com ambos")

        elif gerado and gerado.get("tipo") == "encontro":
            enc = gerado.get("encontro", {})
            sugestoes.append(f"Inicie combate: {enc.get('nome', '?')}")
            ajustes = gerado.get("ajustes_rapidos") or {}
            if "mais_dificil" in ajustes:
                sugestoes.append(
                    f"Ajuste dificuldade: {ajustes['mais_dificil']}"
                )

        if self.campanha.sessao_atual:
            sugestoes.append("Finalizar sessao atual")
        else:
            sugestoes.append("Iniciar nova sessao")

        return sugestoes[:4]

    def _gerar_proximos_passos(self, analise: Any) -> List[str]:
        """Proximas acoes recomendadas."""
        return [
            "Fazer nova consulta",
            "Gerar conteudo para sessao",
            "Ver resumo da campanha",
            "Consultar memoria ('Thorin', 'combate', etc.)",
        ]

    def _calcular_nivel_medio_party(self) -> int:
        """Calcula nivel medio da party."""
        if not self.campanha.party_xp:
            return 1
        niveis = [
            self._nivel_por_xp(xp)
            for xp in self.campanha.party_xp.values()
        ]
        return sum(niveis) // len(niveis)

    def _nivel_por_xp(self, xp: int) -> int:
        """Converte XP para nivel."""
        tabela = [
            0, 1000, 3000, 6000, 10000,
            15000, 21000, 28000, 36000, 45000,
        ]
        nivel = 1
        for i, xp_nivel in enumerate(tabela[1:], 2):
            if xp >= xp_nivel:
                nivel = i
        return min(nivel, 10)

    def _get_ultimo_encontro(self) -> str:
        """Recupera dificuldade do ultimo encontro."""
        for evento in reversed(list(self.campanha.eventos.values())):
            if evento.tipo == "combate":
                return "medio"
        return "medio"

    def iniciar_sessao(self, numero: Optional[int] = None) -> Any:
        """Inicia sessao na campanha."""
        return self.campanha.iniciar_sessao(numero)

    def finalizar_sessao(self, resumo: str = "") -> None:
        """Finaliza sessao."""
        self.campanha.finalizar_sessao(resumo)

    def memoria(self, query: str, limite: int = 5) -> List[Dict[str, Any]]:
        """Consulta memoria da campanha."""
        return self.campanha.lembrar(query, limite)

    def resumo_campanha(self, sessoes: int = 3) -> str:
        """Gera resumo da campanha."""
        return self.campanha.gerar_resumo(sessoes)


def demo_integracao_completa() -> None:
    """Demonstra sistema completo integrado."""
    print("=" * 80)
    print("SISTEMA 3D&T COMPLETO - INTEGRACAO NIVEIS 4-6")
    print("=" * 80)

    sistema = Sistema3DT(campaign_name="Demo Integracao")
    sistema.iniciar_sessao(1)
    sistema.campanha.adicionar_personagem(
        "Thorin", "pc", "Anao", 2, xp_inicial=500
    )
    sistema.campanha.adicionar_personagem(
        "Lyra", "pc", "Elfa", 2, xp_inicial=500
    )

    consultas = [
        "goblin",
        "crie encontro medio para 4 jogadores nivel 2",
        "quanto XP para nivel 3?",
    ]

    for query in consultas:
        print(f"\n{'=' * 80}")
        resposta = sistema.consultar(query)

        print(f"\n[RESPOSTA] '{resposta.query_original}'")
        print(f"   Intencao: {resposta.intencao}")
        print(f"   Dados encontrados: {len(resposta.dados_recuperados)}")
        for d in resposta.dados_recuperados[:2]:
            print(f"      - [{d.get('fonte')}] {d.get('tipo')}")

        if resposta.conteudo_gerado:
            cg = resposta.conteudo_gerado
            print(f"\n   Conteudo gerado: {cg.get('tipo')}")
            if cg.get("tipo") == "encontro":
                enc = cg.get("encontro", {})
                print(f"      Encontro: {enc.get('nome')}")
                print(f"      XP: {enc.get('xp_total')}")

        print("\n   Sugestoes:")
        for s in resposta.sugestoes[:3]:
            print(f"      - {s}")

    print(f"\n{'=' * 80}")
    sistema.finalizar_sessao("Demo de integracao concluida")

    print("\n[OK] Sistema integrado funcionando!")
    print(f"   Campanha salva: {sistema.campanha.campaign_id}")
    print("\nProximo passo: Nivel 7 - Multimodal (imagens)")


if __name__ == "__main__":
    demo_integracao_completa()
