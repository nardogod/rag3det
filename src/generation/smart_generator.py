"""
Nivel 5: Geracao de Conteudo Inteligente.
Cria NPCs, encontros e aventuras baseados em analise de contexto.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.generation.content_generator import ContentGenerator, GeneratedNPC
from src.rag.smart_reasoning import AnaliseContexto, SmartReasoning, TipoConsulta


@dataclass
class EncontroGerado:
    """Encontro completo gerado."""
    nome: str
    descricao: str
    dificuldade: str
    inimigos: List[Dict[str, Any]]
    total_xp: int
    tesouro: List[str]
    taticas: str
    mapa_sugestao: str
    variacoes: List[str]


@dataclass
class AventuraGerada:
    """Aventura completa gerada (estrutura para expansao)."""
    titulo: str
    sinopse: str
    atos: List[Dict[str, Any]]
    npcs_chave: List[GeneratedNPC]
    encontros_principais: List[EncontroGerado]
    recompensas: Dict[str, Any]
    ganchos: List[str]


class SmartGenerator:
    """
    Gerador inteligente que usa analise de contexto para criar conteudo
    adequado à necessidade do usuario.
    """

    def __init__(
        self,
        entity_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> None:
        self.entity_cache = entity_cache or {}
        self.reasoning = SmartReasoning(self.entity_cache)
        self.base_generator = ContentGenerator()

    def gerar(
        self,
        query: str,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gera conteudo baseado na analise inteligente da query.
        """
        analise = self.reasoning.analisar(query)

        if analise.tipo == TipoConsulta.GERACAO_NPC:
            return self._gerar_npc_inteligente(analise, contexto)

        if analise.tipo == TipoConsulta.GERACAO_ENCONTRO:
            return self._gerar_encontro_inteligente(analise, contexto)

        if "aventura" in query.lower() or "missao" in query.lower():
            return self._gerar_aventura_inteligente(analise, contexto)

        return self._gerar_conteudo_generico(analise)

    def _gerar_npc_inteligente(
        self,
        analise: AnaliseContexto,
        contexto: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Gera NPC adequado ao contexto da party/sessao."""
        params = analise.parametros
        nivel = params.get("nivel", 1)
        if contexto and "party_level" in contexto:
            variacao = random.choice([-1, 0, 0, 1, 2])
            nivel = max(1, contexto["party_level"] + variacao)

        arquetipo = params.get("arquetipo", "generalista")
        if analise.entidades:
            if any(self._is_magia(e) for e in analise.entidades):
                arquetipo = "mago"
            elif any(self._is_arma(e) for e in analise.entidades):
                arquetipo = "guerreiro"

        raca = params.get(
            "raca",
            random.choice(["Humano", "Elfo", "Anao"]),
        )
        npc = self.base_generator.generate_npc(
            nivel=nivel,
            arquetipo=arquetipo,
            raca=raca,
        )

        personalizacao = self._personalizar_npc(npc, analise, contexto)
        ctx = contexto or {}
        return {
            "tipo": "npc",
            "analise": {
                "nivel_ajustado": nivel,
                "arquetipo_escolhido": arquetipo,
                "contexto_detectado": ctx.get("tema", "Geral"),
            },
            "npc": npc.to_dict(),
            "personalizacao": personalizacao,
            "sugestoes_uso": [
                f"Use {npc.nome} como {personalizacao['papel_sugerido']}",
                f"Conexao com party: {personalizacao['conexao_sugerida']}",
                f"Gancho: {personalizacao['gancho_imediato']}",
            ],
        }

    def _gerar_encontro_inteligente(
        self,
        analise: AnaliseContexto,
        contexto: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Gera encontro balanceado."""
        params = analise.parametros
        ctx = contexto or {}
        party_size = params.get("party_size", ctx.get("party_size", 4))
        party_level = params.get("nivel", ctx.get("party_level", 1))
        dificuldade = params.get("dificuldade", "medio")

        xp_base = party_level * 100 * party_size
        multiplicador = self.reasoning.REGRAS["encontro_xp"][dificuldade]
        xp_alvo = int(xp_base * multiplicador)

        monstros_disponiveis = self._buscar_monstros_adequados(party_level)
        composicao = self._otimizar_composicao(
            monstros_disponiveis,
            xp_alvo,
            dificuldade,
            party_size,
        )

        inimigos_list = composicao["inimigos"]
        primeiro_nome = (
            inimigos_list[0].get("nome", "Inimigos")
            if inimigos_list
            else "Inimigos"
        )

        encontro = EncontroGerado(
            nome=self._gerar_nome_encontro(dificuldade, composicao),
            descricao=self._gerar_descricao(composicao, contexto),
            dificuldade=dificuldade,
            inimigos=inimigos_list,
            total_xp=composicao["xp_total"],
            tesouro=self._gerar_tesouro(composicao["xp_total"], party_level),
            taticas=self._gerar_taticas(composicao, dificuldade),
            mapa_sugestao=self._sugerir_mapa(composicao, contexto),
            variacoes=self._gerar_variacoes(composicao, dificuldade),
        )

        razao_pct = (
            (encontro.total_xp / xp_alvo * 100) if xp_alvo > 0 else 100.0
        )
        return {
            "tipo": "encontro",
            "analise": {
                "xp_alvo": xp_alvo,
                "xp_atingido": encontro.total_xp,
                "balanceamento": f"{razao_pct:.1f}% do alvo",
                "dificuldade_real": self._calcular_dificuldade_real(
                    composicao, party_size, party_level
                ),
            },
            "encontro": {
                "nome": encontro.nome,
                "descricao": encontro.descricao,
                "dificuldade": encontro.dificuldade,
                "inimigos": encontro.inimigos,
                "xp_total": encontro.total_xp,
                "xp_por_jogador": (
                    encontro.total_xp // party_size if party_size else 0
                ),
                "tesouro": encontro.tesouro,
                "taticas": encontro.taticas,
                "mapa": encontro.mapa_sugestao,
                "variacoes": encontro.variacoes,
            },
            "timeline": self._gerar_timeline_encontro(encontro),
            "ajustes_rapidos": {
                "mais_facil": "Remover 1 inimigo comum",
                "mais_dificil": (
                    f"Adicionar 1 {primeiro_nome} ou aumentar PV em 50%"
                ),
                "recompensa_maior": (
                    "Dobrar PE ou adicionar item magico menor"
                ),
            },
        }

    def _buscar_monstros_adequados(
        self, party_level: int
    ) -> List[Dict[str, Any]]:
        """Busca monstros adequados ao nivel da party."""
        adequados: List[Dict[str, Any]] = []

        for entity_name, chunks in self.entity_cache.items():
            for chunk in chunks:
                meta = chunk.get("metadata", {}) or {}
                data = meta.get("structured_data", {}) or {}
                if not data:
                    continue
                if meta.get("table_type") != "stats":
                    continue
                poder = data.get("poder_combate", 0)
                nivel_monstro = poder // 3
                if abs(nivel_monstro - party_level) <= 2:
                    adequados.append({
                        "nome": data.get("nome", entity_name),
                        "poder": poder,
                        "xp": data.get("xp_sugerido", poder * 10),
                        "stats": data,
                        "categoria": data.get("categoria_poder", "Medio"),
                    })

        adequados.sort(key=lambda x: x["poder"])
        return adequados[:10]

    def _otimizar_composicao(
        self,
        monstros: List[Dict[str, Any]],
        xp_alvo: int,
        dificuldade: str,
        party_size: int,
    ) -> Dict[str, Any]:
        """Otimiza composicao do encontro para atingir XP alvo."""
        if not monstros:
            return self._composicao_fallback(xp_alvo, dificuldade)

        inimigos: List[Dict[str, Any]] = []
        xp_total = 0
        lider_adicionado = False

        if dificuldade == "facil":
            fracos = [m for m in monstros if m.get("categoria") == "Fraco"]
            if fracos:
                monstro_base = fracos[0]
                qtd = min(
                    party_size + 1,
                    max(1, int(xp_alvo / (monstro_base["xp"] or 1))),
                )
                for _ in range(qtd):
                    inimigos.append({
                        "nome": monstro_base["nome"],
                        "stats": monstro_base["stats"],
                        "xp": monstro_base["xp"],
                        "variante": "comum",
                    })
                    xp_total += monstro_base["xp"]

        elif dificuldade == "medio":
            comuns = [
                m
                for m in monstros
                if m.get("categoria") in ["Fraco", "Medio"]
            ]
            if comuns:
                idx = len(comuns) // 2
                monstro_base = comuns[idx]
                qtd = max(2, party_size - 1)
                for _ in range(qtd):
                    inimigos.append({
                        "nome": monstro_base["nome"],
                        "stats": monstro_base["stats"],
                        "xp": monstro_base["xp"],
                        "variante": "comum",
                    })
                    xp_total += monstro_base["xp"]
                if xp_total < xp_alvo * 0.8:
                    lider = comuns[-1] if len(comuns) > 1 else comuns[0]
                    inimigos.append({
                        "nome": f"{lider['nome']} Lider",
                        "stats": self._buffar_stats(
                            lider.get("stats", {}), 1.3
                        ),
                        "xp": int((lider.get("xp") or 0) * 1.5),
                        "variante": "lider",
                        "habilidades_especiais": ["Comandar", "Moral +2"],
                    })
                    xp_total += int((lider.get("xp") or 0) * 1.5)
                    lider_adicionado = True

        elif dificuldade in ["dificil", "mortal"]:
            fortes = [
                m
                for m in monstros
                if m.get("categoria") in ["Forte", "Epico"]
            ]
            if fortes:
                boss = fortes[-1]
                inimigos.append({
                    "nome": boss["nome"],
                    "stats": boss["stats"],
                    "xp": boss["xp"],
                    "variante": (
                        "boss" if dificuldade == "mortal" else "elite"
                    ),
                })
                xp_total += boss["xp"]
                if dificuldade == "dificil" and len(monstros) > 1:
                    outros = [m for m in monstros if m != boss][:2]
                    for lac in outros:
                        inimigos.append({
                            "nome": lac["nome"],
                            "stats": lac["stats"],
                            "xp": lac["xp"],
                            "variante": "lacaio",
                        })
                        xp_total += lac["xp"]

        if not inimigos:
            return self._composicao_fallback(xp_alvo, dificuldade)

        return {
            "inimigos": inimigos,
            "xp_total": xp_total,
            "lider_presente": lider_adicionado,
            "estrategia": dificuldade,
        }

    def _composicao_fallback(
        self, xp_alvo: int, dificuldade: str
    ) -> Dict[str, Any]:
        """Composicao quando nao ha dados no cache."""
        inimigos: List[Dict[str, Any]] = []
        xp_total = 0

        if dificuldade == "facil":
            qtd = min(6, max(1, xp_alvo // 90))
            for _ in range(qtd):
                inimigos.append({
                    "nome": "Goblin",
                    "xp": 90,
                    "variante": "comum",
                    "stats": {"forca": 3, "habilidade": 4, "pv": 8},
                })
                xp_total += 90
        elif dificuldade == "medio":
            for _ in range(3):
                inimigos.append({
                    "nome": "Orc",
                    "xp": 120,
                    "variante": "comum",
                    "stats": {"forca": 5, "habilidade": 3, "pv": 15},
                })
                xp_total += 120
        else:
            inimigos.append({
                "nome": "Troll",
                "xp": 400,
                "variante": "boss",
                "stats": {"forca": 8, "habilidade": 4, "pv": 40},
            })
            xp_total = 400

        return {
            "inimigos": inimigos,
            "xp_total": xp_total,
            "lider_presente": False,
            "estrategia": f"{dificuldade}_fallback",
        }

    def _buffar_stats(
        self, stats: Dict[str, Any], fator: float
    ) -> Dict[str, Any]:
        """Aumenta stats para versao elite/lider."""
        buffed: Dict[str, Any] = {}
        for key, val in (stats or {}).items():
            if (
                isinstance(val, (int, float))
                and key not in ("nivel", "circulo")
            ):
                buffed[key] = int(val * fator)
            else:
                buffed[key] = val
        return buffed

    def _gerar_nome_encontro(
        self, dificuldade: str, composicao: Dict[str, Any]
    ) -> str:
        """Gera nome atmosferico para o encontro."""
        nomes: Dict[str, List[str]] = {
            "facil": [
                "Emboscada Goblin",
                "Patrulha Perdida",
                "Bando de Saques",
            ],
            "medio": [
                "Guarnicao Orc",
                "Emboscada na Estrada",
                "Guardas do Cla",
            ],
            "dificil": [
                "Elite Sombria",
                "Guardioes do Covil",
                "Tropa de Choque",
            ],
            "mortal": [
                "Avante do Exercito",
                "Champion da Horda",
                "Ameaca Imortal",
            ],
        }
        base = random.choice(
            nomes.get(dificuldade, nomes["medio"])
        )
        if composicao.get("lider_presente"):
            base += " (Com Lider)"
        return base

    def _gerar_descricao(
        self,
        composicao: Dict[str, Any],
        contexto: Optional[Dict[str, Any]],
    ) -> str:
        """Gera descricao atmosferica."""
        ctx = contexto or {}
        local = ctx.get("local", "terreno selvagem")
        inimigos = composicao.get("inimigos") or []
        primeiro = inimigos[0].get("nome", "inimigos") if inimigos else "inimigos"
        descricoes = [
            f"Os inimigos estao emboscados em {local}, "
            "esperando o momento certo para atacar.",
            f"Um grupo de {primeiro}s patrulha {local} de forma desorganizada.",
            f"Voceis encontram {local} sendo guardado por forcas inimigas.",
            f"O som de {primeiro}s precede a visao - eles estao em {local}.",
        ]
        return random.choice(descricoes)

    def _gerar_tesouro(self, xp_total: int, party_level: int) -> List[str]:
        """Gera tesouro proporcional."""
        pe_base = max(0, xp_total // 2)
        tesouro = [f"{pe_base} PE em moedas e objetos de valor"]
        if party_level >= 3 and random.random() < 0.3:
            tesouro.append("Pocao de Cura Menor (2d8 PV)")
        if party_level >= 5 and random.random() < 0.2:
            tesouro.append("Pergaminho de Magia (1o circulo)")
        if random.random() < 0.5:
            tesouro.append("Equipamento padrao (valor 20% do normal)")
        return tesouro

    def _gerar_taticas(
        self, composicao: Dict[str, Any], dificuldade: str
    ) -> str:
        """Gera taticas baseadas na composicao."""
        inimigos = composicao.get("inimigos") or []
        base = (
            inimigos[0].get("nome", "Inimigos")
            if inimigos
            else "Inimigos"
        )
        taticas = {
            "facil": (
                f"Os {base}s atacam diretamente sem estrategia. "
                "Fugem se perderem metade."
            ),
            "medio": (
                "Formam linha de combate. Se houver lider, "
                "ele coordena flanqueamento."
            ),
            "dificil": (
                "Usam terreno para vantagem. Focam em alvos fracos. "
                "Retirada tactica se necessario."
            ),
            "mortal": (
                "Comportamento predatorio inteligente. "
                "Exploram fraquezas da party. Nao fogem."
            ),
        }
        return taticas.get(dificuldade, taticas["medio"])

    def _sugerir_mapa(
        self,
        composicao: Dict[str, Any],
        contexto: Optional[Dict[str, Any]],
    ) -> str:
        """Sugere configuracao de mapa."""
        return (
            "Sugestao: 20x20m, cobertura natural 30%, "
            "ponto alto no centro para lider (se presente), "
            "rotas de fuga em 2 lados."
        )

    def _gerar_variacoes(
        self, composicao: Dict[str, Any], dificuldade: str
    ) -> List[str]:
        """Gera variacoes do encontro."""
        return [
            "Versao Noturna: Inimigos +2 em Furtividade, -2 em Percepcao",
            "Versao Ferida: Todos com 50% PV, mas +1 de moral",
            "Versao Reforcada: +2 inimigos comuns chegam em 1d4 rodadas",
        ]

    def _calcular_dificuldade_real(
        self,
        composicao: Dict[str, Any],
        party_size: int,
        party_level: int,
    ) -> str:
        """Calcula dificuldade real baseada nos numeros."""
        xp_total = composicao.get("xp_total", 0)
        xp_esperado = party_level * 100 * party_size
        razao = xp_total / xp_esperado if xp_esperado > 0 else 1
        if razao < 0.7:
            return "Facil (abaixo do esperado)"
        if razao < 1.3:
            return "Medio (balanceado)"
        if razao < 2.0:
            return "Dificil (desafiador)"
        return "Mortal (perigoso)"

    def _gerar_timeline_encontro(
        self, encontro: EncontroGerado
    ) -> List[Dict[str, str]]:
        """Gera timeline provavel do encontro."""
        return [
            {
                "rodada": 1,
                "evento": "Surpresa ou deteccao",
                "acao_sugerida": "Teste de Furtividade vs Percepcao",
            },
            {
                "rodada": 2,
                "evento": "Posicionamento inicial",
                "acao_sugerida": "Aproveitar terreno",
            },
            {
                "rodada": "2-3",
                "evento": "Combate principal",
                "acao_sugerida": "Focar lider ou eliminar lacaios",
            },
            {
                "rodada": "4+",
                "evento": "Resolucao",
                "acao_sugerida": "Perseguicao ou aceitar rendicao",
            },
        ]

    def _personalizar_npc(
        self,
        npc: GeneratedNPC,
        analise: AnaliseContexto,
        contexto: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Personaliza NPC baseado no contexto."""
        entidade_ref = (
            random.choice(analise.entidades)
            if analise.entidades
            else "o objetivo atual"
        )
        return {
            "papel_sugerido": random.choice([
                "aliado temporario",
                "informante",
                "comerciante",
                "antagonista secundario",
                "mentor",
                "rival",
            ]),
            "conexao_sugerida": (
                f"Tem informacoes sobre {entidade_ref}"
            ),
            "gancho_imediato": random.choice([
                "Precisa de ajuda com uma divida, um segredo ou protecao",
                "Sabe algo sobre o vilao, o tesouro ou a dungeon",
                "Esta sendo perseguido, chantageado ou ignorado",
            ]),
            "motivacao_oculta": random.choice([
                "Dinheiro para familia",
                "Vinganca silenciosa",
                "Proteger um segredo",
                "Achar um herdeiro",
            ]),
        }

    def _is_magia(self, nome: str) -> bool:
        """Verifica se nome e magia."""
        return any(
            kw in nome.lower()
            for kw in ["fogo", "gelo", "cura", "bola", "raio", "magia"]
        )

    def _is_arma(self, nome: str) -> bool:
        """Verifica se nome e arma."""
        return any(
            kw in nome.lower()
            for kw in [
                "espada", "machado", "arco", "adaga",
                "martelo", "lanca",
            ]
        )

    def _gerar_aventura_inteligente(
        self,
        analise: AnaliseContexto,
        contexto: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Gera aventura completa (placeholder para expansao)."""
        return {
            "tipo": "aventura",
            "status": "Funcionalidade em desenvolvimento",
            "sugestao": (
                "Use geracao de encontros multiplos para criar uma aventura"
            ),
        }

    def _gerar_conteudo_generico(
        self, analise: AnaliseContexto
    ) -> Dict[str, Any]:
        """Geracao generica quando tipo nao identificado."""
        return {
            "tipo": "generico",
            "analise": {
                "tipo": analise.tipo.value,
                "entidades": analise.entidades,
                "parametros": analise.parametros,
                "intencao_principal": analise.intencao_principal,
                "sugestao_acao": analise.sugestao_acao,
            },
            "sugestao": (
                "Tente ser mais especifico: 'crie NPC nivel 3' ou "
                "'gere encontro medio para 4 jogadores'"
            ),
        }


def gerar_inteligente(
    query: str,
    entity_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    contexto: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Funcao simples para gerar conteudo inteligente."""
    generator = SmartGenerator(entity_cache or {})
    return generator.gerar(query, contexto)
