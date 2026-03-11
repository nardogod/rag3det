"""
Nivel 4: Raciocinio Inteligente sobre Regras 3D&T.
Analisa contexto, detecta necessidades e sugere acoes relevantes.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TipoConsulta(Enum):
    """Tipos de consulta que o sistema pode identificar."""
    BUSCA_ENTIDADE = "busca_entidade"
    BUSCAR_MAGIA = "buscar_magia"
    COMPARACAO = "comparacao"
    OTIMIZACAO_BUILD = "otimizacao_build"
    CALCULO_ENCONTRO = "calculo_encontro"
    CONSULTA_REGRA = "consulta_regra"
    GERACAO_NPC = "geracao_npc"
    GERACAO_ENCONTRO = "geracao_encontro"
    AJUDA_COMBATE = "ajuda_combate"
    DESCONHECIDO = "desconhecido"


@dataclass
class AnaliseContexto:
    """Resultado da analise de contexto."""
    tipo: TipoConsulta
    entidades: List[str]
    parametros: Dict[str, Any]
    intencao_principal: str
    dados_necessarios: List[str]
    sugestao_acao: str


@dataclass
class RecomendacaoInteligente:
    """Recomendacao gerada pelo sistema."""
    titulo: str
    descricao: str
    dados_base: Dict[str, Any]
    calculos: Dict[str, Any]
    alternativas: List[Dict[str, Any]]
    proximo_passo: str


class SmartReasoning:
    """
    Motor de raciocinio inteligente para 3D&T.
    Transforma dados brutos em insights acionaveis.
    """

    REGRAS = {
        "xp_por_nivel": {
            1: 0, 2: 1000, 3: 3000, 4: 6000, 5: 10000,
            6: 15000, 7: 21000, 8: 28000, 9: 36000, 10: 45000,
        },
        "pe_por_nivel": {
            1: 100, 2: 200, 3: 400, 4: 800, 5: 1500,
            6: 2500, 7: 4000, 8: 6000, 9: 8500, 10: 12000,
        },
        "encontro_xp": {
            "facil": 0.5,
            "medio": 1.0,
            "dificil": 1.5,
            "mortal": 2.0,
        },
        "dano_medio_dado": {
            "d4": 2.5, "d6": 3.5, "d8": 4.5, "d10": 5.5, "d12": 6.5,
        },
    }

    def __init__(self, entity_cache: Optional[Dict[str, List[Dict]]] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.entity_cache = entity_cache or {}
        self.historico_consultas: List[Dict[str, Any]] = []

    def analisar(
        self, query: str, contexto_atual: Optional[Dict[str, Any]] = None
    ) -> AnaliseContexto:
        """
        Analisa profundamente a consulta do usuario.
        """
        query_lower = query.lower()
        tipo = self._detectar_tipo(query_lower)
        entidades = self._extrair_entidades(query_lower)
        parametros = self._extrair_parametros(query_lower)
        intencao = self._determinar_intencao(tipo, entidades, parametros)
        dados_necessarios = self._identificar_dados_necessarios(
            tipo, entidades, parametros
        )
        sugestao = self._gerar_sugestao_acao(tipo, intencao, parametros)

        return AnaliseContexto(
            tipo=tipo,
            entidades=entidades,
            parametros=parametros,
            intencao_principal=intencao,
            dados_necessarios=dados_necessarios,
            sugestao_acao=sugestao,
        )

    def _detectar_tipo(self, query: str) -> TipoConsulta:
        """Detecta o tipo de consulta."""
        if any(
            kw in query
            for kw in [
                " vs ",
                " versus ",
                " contra ",
                " ou ",
                " qual melhor ",
                " comparar ",
            ]
        ):
            return TipoConsulta.COMPARACAO

        if any(
            kw in query
            for kw in ["melhor", "otimo", "ideal", "mais eficiente", "custo-beneficio"]
        ):
            if any(kw in query for kw in ["arma", "equipamento", "item", "pe"]):
                return TipoConsulta.OTIMIZACAO_BUILD

        if any(
            kw in query
            for kw in ["quanto xp", "quanto pe", "quanto custa", "calcula", "dano medio"]
        ):
            return TipoConsulta.CALCULO_ENCONTRO

        if any(kw in query for kw in ["crie", "gere", "monte", "preciso de um"]):
            if any(kw in query for kw in ["npc", "personagem", "pj", "pc"]):
                return TipoConsulta.GERACAO_NPC
            if any(
                kw in query
                for kw in ["encontro", "combate", "monstros", "inimigos"]
            ):
                return TipoConsulta.GERACAO_ENCONTRO

        if any(
            kw in query
            for kw in [
                "como funciona",
                "regra",
                "teste",
                "rolagem",
                "iniciativa",
            ]
        ):
            return TipoConsulta.CONSULTA_REGRA

        if any(
            kw in query
            for kw in ["dano", "ataque", "acerto", "critico", "defesa"]
        ):
            return TipoConsulta.AJUDA_COMBATE

        # Busca por magia: "o que é X?", "como funciona X?", "magia X"
        if any(
            kw in query
            for kw in ["magia", "feitico", "pm", "custo", "escola", "circulo"]
        ) or "o que" in query or "como funciona" in query:
            from src.ingestion.entity_extractor import extrair_nome_magia
            if extrair_nome_magia(query):
                return TipoConsulta.BUSCAR_MAGIA

        for entity in self.entity_cache.keys():
            if entity in query:
                return TipoConsulta.BUSCA_ENTIDADE

        return TipoConsulta.DESCONHECIDO

    def _extrair_entidades(self, query: str) -> List[str]:
        """Extrai nomes de entidades da query."""
        entidades: List[str] = []
        for entity_name in self.entity_cache.keys():
            if entity_name in query:
                entidades.append(entity_name)

        padroes = [
            r"(?:stats? de|atributos de|sobre|informações sobre)\s+(\w+)",
            r"(\w+)(?:\s+vs\s+|\s+contra\s+|\s+ou\s+)(\w+)",
        ]
        for padrao in padroes:
            matches = re.findall(padrao, query)
            for match in matches:
                if isinstance(match, tuple):
                    entidades.extend(list(match))
                else:
                    entidades.append(match)

        return list(dict.fromkeys(entidades))

    def _extrair_parametros(self, query: str) -> Dict[str, Any]:
        """Extrai parametros numericos da query."""
        params: Dict[str, Any] = {}

        nivel_match = re.search(r"n[íi]vel\s+(\d+)", query)
        if nivel_match:
            params["nivel"] = int(nivel_match.group(1))

        pe_match = re.search(r"(\d+)\s*(?:pe|po|moedas?)", query)
        if pe_match:
            params["pe"] = int(pe_match.group(1))

        party_match = re.search(
            r"(\d+)\s*(?:jogadores?|pjs?|pcs?|aventureiros?)", query
        )
        if party_match:
            params["party_size"] = int(party_match.group(1))

        if any(kw in query for kw in ["facil", "fácil", "fraco"]):
            params["dificuldade"] = "facil"
        elif any(kw in query for kw in ["dificil", "difícil", "hard", "desafiador"]):
            params["dificuldade"] = "dificil"
        elif any(kw in query for kw in ["mortal", "epico", "épico", "impossivel"]):
            params["dificuldade"] = "mortal"
        else:
            params["dificuldade"] = "medio"

        forca_match = re.search(r"for[çc]a\s+(\d+)", query)
        if forca_match:
            params["forca"] = int(forca_match.group(1))

        dado_match = re.search(r"(\d+)d(\d+)", query)
        if dado_match:
            params["dado_quantidade"] = int(dado_match.group(1))
            params["dado_faces"] = int(dado_match.group(2))

        return params

    def _determinar_intencao(
        self,
        tipo: TipoConsulta,
        entidades: List[str],
        parametros: Dict[str, Any],
    ) -> str:
        """Determina a intencao principal do usuario."""
        intencoes = {
            TipoConsulta.BUSCA_ENTIDADE: (
                f"Conhecer detalhes de {entidades[0] if entidades else 'entidade'}"
            ),
            TipoConsulta.COMPARACAO: (
                f"Comparar {' vs '.join(entidades[:2])}"
            ),
            TipoConsulta.OTIMIZACAO_BUILD: (
                f"Otimizar build com {parametros.get('pe', 'X')} PE"
            ),
            TipoConsulta.CALCULO_ENCONTRO: "Calcular progressao ou recompensa",
            TipoConsulta.CONSULTA_REGRA: "Entender mecanica do sistema",
            TipoConsulta.GERACAO_NPC: (
                f"Criar personagem nivel {parametros.get('nivel', '?')}"
            ),
            TipoConsulta.GERACAO_ENCONTRO: (
                f"Criar encontro {parametros.get('dificuldade', 'medio')}"
            ),
            TipoConsulta.AJUDA_COMBATE: "Resolver situacao de combate",
            TipoConsulta.DESCONHECIDO: "Explorar informacoes disponiveis",
        }
        return intencoes.get(tipo, "Consulta geral")

    def _identificar_dados_necessarios(
        self,
        tipo: TipoConsulta,
        entidades: List[str],
        parametros: Dict[str, Any],
    ) -> List[str]:
        """Identifica quais dados sao necessarios para responder."""
        necessarios: List[str] = []

        if tipo == TipoConsulta.COMPARACAO:
            necessarios.extend(
                ["stats_completos", "poder_combate", "analise_vantagens"]
            )
        elif tipo == TipoConsulta.OTIMIZACAO_BUILD:
            necessarios.extend(
                [
                    "equipamentos_disponiveis",
                    "eficiencia_pe",
                    "requisitos_atributos",
                ]
            )
        elif tipo == TipoConsulta.GERACAO_ENCONTRO:
            necessarios.extend(
                ["xp_alvo", "monstros_adequados", "balanceamento_party"]
            )
        elif tipo == TipoConsulta.CALCULO_ENCONTRO and "nivel" in parametros:
            necessarios.append("tabela_xp")
        elif entidades:
            necessarios.append(f"dados_{entidades[0]}")

        return necessarios

    def _gerar_sugestao_acao(
        self,
        tipo: TipoConsulta,
        intencao: str,
        parametros: Dict[str, Any],
    ) -> str:
        """Gera sugestao de proxima acao contextual."""
        sugestoes = {
            TipoConsulta.COMPARACAO: (
                "Analise comparativa com probabilidade de vitoria"
            ),
            TipoConsulta.OTIMIZACAO_BUILD: (
                "Ranking de opcoes com eficiencia calculada"
            ),
            TipoConsulta.GERACAO_ENCONTRO: (
                "Encontro balanceado com taticas sugeridas"
            ),
            TipoConsulta.GERACAO_NPC: "Ficha completa pronta para uso",
            TipoConsulta.CALCULO_ENCONTRO: (
                "Calculo preciso com explicacao da regra"
            ),
            TipoConsulta.BUSCA_ENTIDADE: (
                "Ficha tecnica + lore + sugestoes de uso"
            ),
        }
        return sugestoes.get(tipo, "Informacoes detalhadas da consulta")

    def gerar_recomendacao(
        self,
        analise: AnaliseContexto,
        dados_recuperados: List[Dict[str, Any]],
    ) -> RecomendacaoInteligente:
        """
        Gera recomendacao inteligente baseada na analise.
        """
        if (
            analise.tipo == TipoConsulta.COMPARACAO
            and len(analise.entidades) >= 2
        ):
            return self._recomendar_comparacao(analise, dados_recuperados)
        elif analise.tipo == TipoConsulta.OTIMIZACAO_BUILD:
            return self._recomendar_build(analise, dados_recuperados)
        elif analise.tipo == TipoConsulta.GERACAO_ENCONTRO:
            return self._recomendar_encontro(analise)
        elif analise.tipo == TipoConsulta.CALCULO_ENCONTRO:
            return self._recomendar_calculo(analise)
        else:
            return self._recomendar_default(analise, dados_recuperados)

    def _recomendar_comparacao(
        self,
        analise: AnaliseContexto,
        dados: List[Dict[str, Any]],
    ) -> RecomendacaoInteligente:
        """Gera recomendacao de comparacao entre entidades."""
        entidade1 = (
            analise.entidades[0]
            if len(analise.entidades) > 0
            else "Desconhecido"
        )
        entidade2 = (
            analise.entidades[1]
            if len(analise.entidades) > 1
            else "Desconhecido"
        )

        data1 = self._get_entity_data(entidade1)
        data2 = self._get_entity_data(entidade2)

        if not data1 or not data2:
            return RecomendacaoInteligente(
                titulo=f"Comparacao: {entidade1} vs {entidade2}",
                descricao="Dados insuficientes para comparacao completa.",
                dados_base={},
                calculos={},
                alternativas=[],
                proximo_passo="Buscar dados completos das entidades",
            )

        stats = ["forca", "habilidade", "resistencia", "armadura", "pv"]
        vantagens1 = vantagens2 = 0
        analise_stats: Dict[str, Dict[str, Any]] = {}

        for stat in stats:
            v1 = data1.get(stat, 0)
            v2 = data2.get(stat, 0)
            if v1 > v2:
                vantagens1 += 1
                analise_stats[stat] = {
                    "vantagem": entidade1,
                    "diff": v1 - v2,
                }
            elif v2 > v1:
                vantagens2 += 1
                analise_stats[stat] = {
                    "vantagem": entidade2,
                    "diff": v2 - v1,
                }
            else:
                analise_stats[stat] = {"vantagem": "Empate", "diff": 0}

        poder1 = data1.get(
            "poder_combate",
            data1.get("forca", 0)
            + data1.get("habilidade", 0)
            + data1.get("resistencia", 0),
        )
        poder2 = data2.get(
            "poder_combate",
            data2.get("forca", 0)
            + data2.get("habilidade", 0)
            + data2.get("resistencia", 0),
        )
        prob1 = (
            round(poder1 / (poder1 + poder2) * 100, 1)
            if (poder1 + poder2) > 0
            else 50.0
        )

        vencedor = (
            entidade1
            if vantagens1 > vantagens2
            else (entidade2 if vantagens2 > vantagens1 else "Empate")
        )

        stats_extras = stats + ["poder_combate", "xp_sugerido"]
        return RecomendacaoInteligente(
            titulo=f"Analise: {entidade1} vs {entidade2}",
            descricao=(
                f"{vencedor} tem vantagem geral. "
                f"{entidade1} vence {prob1}% dos combates simulados."
            ),
            dados_base={
                entidade1: {k: data1.get(k) for k in stats_extras},
                entidade2: {k: data2.get(k) for k in stats_extras},
            },
            calculos={
                "probabilidade_vitoria": {
                    entidade1: prob1,
                    entidade2: round(100 - prob1, 1),
                },
                "vantagens_atributos": {
                    entidade1: vantagens1,
                    entidade2: vantagens2,
                },
                "analise_detalhada": analise_stats,
            },
            alternativas=[
                {
                    "cenario": f"{entidade1} com vantagem de terreno",
                    "resultado": (
                        f"Probabilidade aumenta para {min(95, int(prob1) + 15)}%"
                    ),
                },
                {
                    "cenario": f"{entidade2} em emboscada",
                    "resultado": (
                        f"Probabilidade inverte para "
                        f"{max(5, int(100 - prob1 - 20))}%"
                    ),
                },
            ],
            proximo_passo=(
                f"Simular combate completo ou gerar encontro com "
                f"{vencedor} como lider"
            ),
        )

    def _recomendar_build(
        self,
        analise: AnaliseContexto,
        dados: List[Dict[str, Any]],
    ) -> RecomendacaoInteligente:
        """Recomenda otimizacao de build."""
        pe = analise.parametros.get("pe", 100)
        forca = analise.parametros.get("forca")

        equipamentos = [
            d for d in dados
            if d.get("tipo") == "equipamento"
        ]
        equipamentos.sort(
            key=lambda x: x.get("eficiencia", 0) or 0,
            reverse=True,
        )

        validos: List[Dict[str, Any]] = []
        for eq in equipamentos:
            if forca is not None:
                req_match = re.search(
                    r"for[cç]a\s*(\d+)",
                    (eq.get("descricao") or "").lower(),
                )
                if req_match and int(req_match.group(1)) > forca:
                    continue
            if (eq.get("pe") or 999) <= pe:
                validos.append(eq)

        melhor = validos[0] if validos else None
        nome_melhor = melhor.get("nome", "Nenhuma opcao ideal") if melhor else "Nenhuma opcao ideal"

        return RecomendacaoInteligente(
            titulo=f"Otimizacao: Melhor opcao para {pe} PE",
            descricao=f"{nome_melhor} oferece melhor custo-beneficio.",
            dados_base={
                "orcamento": pe,
                "forca_base": forca,
                "opcoes_disponiveis": len(validos),
            },
            calculos={
                "melhor_eficiencia": melhor.get("eficiencia") if melhor else 0,
                "dano_esperado": (
                    self._calcular_dano_medio(melhor.get("dano"))
                    if melhor
                    else 0
                ),
                "sobra_pe": (
                    pe - (melhor.get("pe") or 0) if melhor else pe
                ),
            },
            alternativas=[
                {
                    "nome": eq.get("nome"),
                    "pe": eq.get("pe"),
                    "eficiencia": eq.get("eficiencia"),
                    "quando_escolher": (
                        "Se priorizar defesa"
                        if eq.get("defesa")
                        else "Se priorizar dano"
                    ),
                }
                for eq in validos[1:3]
            ],
            proximo_passo=(
                "Calcular dano medio por turno ou ver combinacoes com armadura"
            ),
        )

    def _recomendar_encontro(self, analise: AnaliseContexto) -> RecomendacaoInteligente:
        """Recomenda configuracao de encontro."""
        party_size = analise.parametros.get("party_size", 4)
        nivel = analise.parametros.get("nivel", 1)
        dificuldade = analise.parametros.get("dificuldade", "medio")

        xp_base = nivel * 100 * party_size
        xp_alvo = int(xp_base * self.REGRAS["encontro_xp"][dificuldade])

        composicoes: Dict[str, Dict[str, Any]] = {
            "facil": {
                "descricao": f"{party_size} inimigos fracos (Goblins, Kobolds)",
                "exemplo": f"{party_size}x Goblin",
                "xp_por_inimigo": 90,
                "tatica": "Atacam em grupo mas fogem se perderem 50%",
            },
            "medio": {
                "descricao": f"{party_size - 1} inimigos medios + 1 lider",
                "exemplo": f"{party_size - 1}x Orc + 1x Orc Lider",
                "xp_por_inimigo": 120,
                "tatica": "Lider coordena, flanqueiam personagens isolados",
            },
            "dificil": {
                "descricao": f"{party_size} inimigos fortes ou 1 elite",
                "exemplo": f"{party_size}x Orc ou 1x Troll",
                "xp_por_inimigo": 200,
                "tatica": (
                    "Uso inteligente de terreno, retirada tactica se necessario"
                ),
            },
            "mortal": {
                "descricao": "Boss epico ou horda numerosa",
                "exemplo": "1x Dragao Jovem ou 2x Trolls + 4x Goblins",
                "xp_por_inimigo": 400,
                "tatica": (
                    "Comportamento inteligente, foca em alvos fracos, "
                    "usa ambiente"
                ),
            },
        }

        comp = composicoes.get(dificuldade, composicoes["medio"])
        xp_total = comp["xp_por_inimigo"] * (
            party_size if dificuldade != "medio" else party_size
        )

        return RecomendacaoInteligente(
            titulo=f"Encontro {dificuldade.upper()}: Party Nivel {nivel}",
            descricao=(
                f"{comp['descricao']}. XP alvo: {xp_alvo}, "
                f"XP gerado: ~{xp_total}"
            ),
            dados_base={
                "party_size": party_size,
                "nivel_medio": nivel,
                "dificuldade": dificuldade,
                "xp_alvo": xp_alvo,
            },
            calculos={
                "xp_total_estimado": xp_total,
                "xp_por_jogador": xp_total // party_size,
                "progresso_nivel": (
                    f"{(xp_total // party_size) / (nivel * 100) * 100:.1f}% "
                    "para proximo nivel"
                ),
                "duracao_estimada": (
                    "15-30 minutos"
                    if dificuldade in ["facil", "medio"]
                    else "30-60 minutos"
                ),
            },
            alternativas=[
                {
                    "variante": (
                        "Versao mais facil"
                        if dificuldade != "facil"
                        else "Versao mais dificil"
                    ),
                    "ajuste": (
                        "Remover 1 inimigo"
                        if dificuldade != "facil"
                        else "Adicionar 2 inimigos"
                    ),
                    "novo_xp": (
                        int(xp_total * 0.8)
                        if dificuldade != "facil"
                        else int(xp_total * 1.3)
                    ),
                }
            ],
            proximo_passo=(
                "Gerar estatisticas completas dos inimigos ou "
                "iniciar combate simulado"
            ),
        )

    def _recomendar_calculo(
        self, analise: AnaliseContexto
    ) -> RecomendacaoInteligente:
        """Recomenda calculos de progressao ou mecanicas."""
        params = analise.parametros

        if "nivel" in params:
            nivel_atual = params["nivel"]
            xp_atual = self.REGRAS["xp_por_nivel"].get(nivel_atual, 0)
            xp_proximo = self.REGRAS["xp_por_nivel"].get(
                nivel_atual + 1, xp_atual * 2
            )
            xp_faltante = xp_proximo - xp_atual
            xp_medio_encontro = nivel_atual * 100
            encontros_necessarios = xp_faltante / xp_medio_encontro

            return RecomendacaoInteligente(
                titulo=f"Progressao: Nivel {nivel_atual} -> {nivel_atual + 1}",
                descricao=f"Faltam {xp_faltante} XP para o proximo nivel.",
                dados_base={
                    "nivel_atual": nivel_atual,
                    "xp_atual": xp_atual,
                    "xp_proximo_nivel": xp_proximo,
                },
                calculos={
                    "xp_faltante": xp_faltante,
                    "encontros_medios_necessarios": round(
                        encontros_necessarios, 1
                    ),
                    "sessoes_estimadas": round(
                        encontros_necessarios / 3, 1
                    ),
                    "pe_ganhos_no_proximo_nivel": self.REGRAS["pe_por_nivel"].get(
                        nivel_atual + 1, 0
                    ),
                },
                alternativas=[
                    {
                        "caminho": "Encontros faceis (seguros)",
                        "quantidade": round(encontros_necessarios * 2, 0),
                        "tempo": "Mais sessoes, menos risco",
                    },
                    {
                        "caminho": "Encontros dificeis (arriscado)",
                        "quantidade": round(encontros_necessarios * 0.7, 0),
                        "tempo": "Menos sessoes, maior risco de morte",
                    },
                ],
                proximo_passo=(
                    "Planejar encontros da proxima sessao ou gerar missao "
                    "com recompensa adequada"
                ),
            )

        if "dado_quantidade" in params and "dado_faces" in params:
            qtd = params["dado_quantidade"]
            faces = params["dado_faces"]
            dado_str = f"d{faces}"
            media_por_dado = self.REGRAS["dano_medio_dado"].get(
                dado_str, faces / 2 + 0.5
            )
            media_total = qtd * media_por_dado
            maximo = qtd * faces
            minimo = qtd * 1
            prob_maximo = (1 / faces) ** qtd * 100
            prob_minimo = (1 / faces) ** qtd * 100

            return RecomendacaoInteligente(
                titulo=f"Dano: {qtd}d{faces}",
                descricao=(
                    f"Media: {media_total:.1f} por ataque. "
                    f"Varia entre {minimo} e {maximo}."
                ),
                dados_base={
                    "dados": f"{qtd}d{faces}",
                    "media": media_total,
                    "minimo": minimo,
                    "maximo": maximo,
                },
                calculos={
                    "dano_esperado_3_ataques": media_total * 3,
                    "dano_esperado_5_ataques": media_total * 5,
                    "prob_critico_maximo": f"{prob_maximo:.2f}%",
                    "comparacao_arma_padrao": (
                        f"{(media_total / 4.5 - 1) * 100:+.0f}% vs 1d8"
                        if faces == 8
                        else "N/A"
                    ),
                },
                alternativas=[
                    {
                        "dado": f"{qtd + 1}d{faces}",
                        "media": (qtd + 1) * media_por_dado,
                        "impacto": "+1 dado (bonus de forca ou magia)",
                    },
                    {
                        "dado": f"{qtd}d{faces + 2}",
                        "media": qtd * (media_por_dado + 1),
                        "impacto": "Arma maior (ex: d6->d8)",
                    },
                ],
                proximo_passo=(
                    "Calcular DPS (dano por turno) ou comparar com "
                    "armaduras de monstros"
                ),
            )

        return RecomendacaoInteligente(
            titulo="Calculo nao reconhecido",
            descricao=(
                "Nao consegui identificar o que calcular. "
                "Tente especificar nivel ou dados (ex: '2d6')."
            ),
            dados_base={},
            calculos={},
            alternativas=[],
            proximo_passo="Reformular a pergunta com mais detalhes",
        )

    def _recomendar_default(
        self,
        analise: AnaliseContexto,
        dados: List[Dict[str, Any]],
    ) -> RecomendacaoInteligente:
        """Recomendacao padrao quando nao ha caso especifico."""
        entidades = [d.get("nome") for d in dados if d.get("nome")]

        return RecomendacaoInteligente(
            titulo=f"Resultados para '{analise.intencao_principal}'",
            descricao=f"Encontrei {len(dados)} resultados relacionados.",
            dados_base={
                "entidades_encontradas": entidades[:5],
                "tipo_consulta": analise.tipo.value,
            },
            calculos={
                "total_resultados": len(dados),
                "confianca_media": (
                    sum(d.get("confianca", 0) for d in dados) / len(dados)
                    if dados
                    else 0
                ),
            },
            alternativas=[
                {"acao": "Refinar busca", "como": "Adicione mais termos especificos"},
                {"acao": "Comparar entidades", "como": "Use 'vs' entre dois nomes"},
                {"acao": "Gerar conteudo", "como": "Peca 'crie encontro' ou 'NPC'"},
            ],
            proximo_passo=(
                "Especificar melhor a consulta ou explorar resultados "
                "encontrados"
            ),
        )

    def _get_entity_data(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Recupera dados de uma entidade do cache."""
        name_lower = entity_name.lower()

        if name_lower in self.entity_cache:
            for chunk in self.entity_cache[name_lower]:
                data = (
                    chunk.get("metadata", {}) or {}
                ).get("structured_data", {})
                if data:
                    return data

        for name, chunks in self.entity_cache.items():
            if name_lower in name or name in name_lower:
                for chunk in chunks:
                    data = (
                        chunk.get("metadata", {}) or {}
                    ).get("structured_data", {})
                    if data:
                        return data

        return None

    def _calcular_dano_medio(self, dano_str: Optional[str]) -> float:
        """Calcula dano medio de string de dado."""
        if not dano_str:
            return 0.0
        match = re.match(r"(\d+)d(\d+)", str(dano_str))
        if match:
            qtd = int(match.group(1))
            faces = int(match.group(2))
            return qtd * (faces / 2 + 0.5)
        try:
            return float(dano_str)
        except (TypeError, ValueError):
            return 0.0


def analisar_consulta(
    query: str,
    entity_cache: Optional[Dict[str, List[Dict]]] = None,
) -> Dict[str, Any]:
    """Funcao simples para analisar uma consulta."""
    reasoning = SmartReasoning(entity_cache or {})
    analise = reasoning.analisar(query)
    return {
        "tipo": analise.tipo.value,
        "entidades": analise.entidades,
        "parametros": analise.parametros,
        "intencao": analise.intencao_principal,
        "sugestao": analise.sugestao_acao,
    }
