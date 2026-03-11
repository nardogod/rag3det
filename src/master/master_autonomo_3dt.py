"""
NIVEL 8: MESTRE AUTONOMO
Sistema que cria, prepara e conduz campanhas de 3D&T automaticamente.
Integra todos os niveis anteriores em um agente narrativo completo.
"""

from __future__ import annotations

import json
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.integration.sistema_multimodal_3dt import (
    RespostaMultimodal,
    SistemaMultimodal3DT,
)
from src.master.regras_3dt import (
    Dificuldade3DT,
    atributo_interno,
    atributo_para_teste,
    cd_por_dificuldade,
    descricao_teste_3dt,
    nome_atributo_completo,
    resolver_teste,
)
from src.master.schemas_mestre import AcaoResolvida, MudancaEstado
from src.multimedia.visual_system_3dt import MapaProcessado, TipoVisual

logger = logging.getLogger(__name__)

# Prompt obrigatorio - violar resulta em resposta invalida
PROMPT_MESTRE_OBRIGATORIO = """
Voce e o Mestre Autonomo de 3D&T. Sua funcao e RESOLVER ACOES, nao descrever cenarios.

ESTADO ATUAL DO JOGO:
{estado_json}

ACAO DO JOGADOR: "{acao}"

REGRAS OBRIGATORIAS - VIOLAR RESULTA EM RESPOSTA INVALIDA:
1. TODA acao que envolva incerteza DEVE usar tipo_acao="teste_atributo" com atributo_usado e dificuldade
2. CD: Facil=3, Normal=4, Dificil=5, Muito Dificil=6
3. Atributos: Forca, Habilidade, Resistencia, Armadura
4. resultado_narrativo DEVE descrever o RESULTADO CONCRETO, nao a intencao
5. PROIBIDO: "parece que", "talvez", "ainda nao esta claro", "voce tenta"
6. PROIBIDO repetir a descricao inicial da cena
7. mudanca_estado DEVE incluir descobertas/inimigos/objetivos quando algo mudou
8. proximas_opcoes: 2 a 4 acoes especificas baseadas no resultado

FORMATO OBRIGATORIO (retorne JSON valido):
{{
  "tipo_acao": "teste_atributo" ou "ataque" ou "social" ou "exploracao" ou "movimento" ou "narracao",
  "atributo_usado": "Forca" ou "Habilidade" ou "Resistencia" ou "Armadura" (se teste),
  "dificuldade": "Facil" ou "Normal" ou "Dificil" ou "Muito Dificil" (se teste),
  "descricao_teste": "O que esta sendo testado",
  "resultado_narrativo": "O QUE ACONTECEU. Concreto. Sem 'parece que'.",
  "mudanca_estado": {{
    "descobertas_add": ["item1", "item2"],
    "inimigos_add": [],
    "objetivos_add": [],
    "em_combate": true ou false ou null
  }},
  "proximas_opcoes": ["opcao 1", "opcao 2", "opcao 3"]
}}
"""

# Frases que indicam narracao vaga (rejeitar)
FRASES_PROIBIDAS = [
    "parece que",
    "talvez",
    "ainda nao esta claro",
    "voce tenta",
    "voce considera",
    "sol ilumina um vale",
]


class FaseCampanha(Enum):
    """Fases de uma campanha autonoma."""
    CRIACAO_MUNDO = auto()
    PREPARACAO = auto()
    SESSAO_ATIVA = auto()
    ENTRE_SESSOES = auto()
    EPILOGO = auto()


class EstiloNarrativo(Enum):
    """Estilos de conducao do mestre."""
    EPICO = "epico"
    SOMBRIO = "sombrio"
    HEROICO = "heroico"
    INTRIGA = "intriga"
    EXPLORACAO = "exploracao"


@dataclass
class ArcoNarrativo:
    """Estrutura de arco para campanha autonoma."""
    titulo: str
    sinopse: str
    atos: List[Dict[str, Any]]
    npcs_centrais: List[str]
    locais_chave: List[str]
    tema_central: str
    tom: EstiloNarrativo

    def proximo_atual(self, sessao_atual: int) -> Optional[Dict[str, Any]]:
        """Retorna o ato correspondente a sessao atual."""
        if not self.atos:
            return None
        for i, ato in enumerate(self.atos):
            inicio = ato.get("sessao_inicio", i + 1)
            fim = ato.get("sessao_fim", i + 1)
            if inicio <= sessao_atual <= fim:
                return ato
        return self.atos[-1] if self.atos else None

    def to_dict(self) -> Dict[str, Any]:
        """Serializacao para persistencia."""
        return {
            "titulo": self.titulo,
            "sinopse": self.sinopse,
            "atos": self.atos,
            "npcs_centrais": self.npcs_centrais,
            "locais_chave": self.locais_chave,
            "tema_central": self.tema_central,
            "tom": self.tom.value,
        }


@dataclass
class DecisaoMestre:
    """Decisao tomada pelo mestre autonomo."""
    tipo: str
    conteudo: str  # texto completo usado hoje na UI
    mecanica_envolvida: Optional[str]
    testes_solicitados: List[Dict[str, Any]]
    consequencias_possiveis: List[str]
    proximos_passos: List[str]
    opcoes_jogador: List[str] = field(default_factory=list)  # 4-5 opcoes para multipla escolha

    # Campos estruturados novos (passo 2)
    teste_necessario: Optional["TesteRPG"] = None
    resultado_acao: str = ""  # foco no QUE aconteceu
    mudanca_estado: Dict[str, Any] = field(default_factory=dict)
    narracao: str = ""  # narracao focada no resultado (pode ser igual a conteudo)


@dataclass
class TesteRPG:
    """Teste de RPG (ex.: Percepcao, Ataque, Carisma)."""

    atributo: str
    cd: int
    resultado: Optional[int] = None
    sucesso: Optional[bool] = None
    descricao: str = ""


@dataclass
class EstadoCena:
    """
    Estado estruturado da cena atual.

    Este objeto deve refletir o que esta acontecendo *agora* em jogo:
    - descricao base do local
    - descobertas que os jogadores ja fizeram
    - inimigos visiveis
    - objetivos em andamento
    - ultimo teste relevante realizado
    """

    nome: str
    descricao: str
    descobertas: List[str] = field(default_factory=list)
    inimigos_visiveis: List[str] = field(default_factory=list)
    objetivos: List[str] = field(default_factory=list)
    ultimo_teste: Optional[TesteRPG] = None
    em_combate: bool = False


def _mapa_para_dict(mapa: MapaProcessado) -> Dict[str, Any]:
    """Converte MapaProcessado para dict serializavel."""
    return {
        "id": mapa.id,
        "nome": mapa.nome,
        "tipo": mapa.tipo.value,
        "pontos_interesse": mapa.pontos_interesse,
        "imagem_path": str(mapa.imagem_path),
    }


class MestreAutonomo3DT:
    """
    Agente Mestre de Campanha Autonomo.
    Cria e conduz aventuras integrado ao sistema 3D&T (niveis 4-7.5).
    """

    def __init__(
        self,
        sistema: Optional[SistemaMultimodal3DT] = None,
        estilo: EstiloNarrativo = EstiloNarrativo.HEROICO,
        duracao_prevista: int = 6,
    ) -> None:
        self.sistema = sistema or SistemaMultimodal3DT()
        self.estilo = estilo
        self.duracao_prevista = duracao_prevista
        self.fase = FaseCampanha.CRIACAO_MUNDO
        self.arco: Optional[ArcoNarrativo] = None
        self.cena_atual: int = 0
        self.preparacao_sessao_atual: Optional[Dict[str, Any]] = None
        self.estado_cena_atual: Optional[EstadoCena] = None
        self.historia_gerada: List[str] = []
        self.pending_decisions: List[DecisaoMestre] = []

        self.on_narrar: Optional[Callable[[str], None]] = None
        self.on_solicitar_teste: Optional[Callable[[Dict], Any]] = None
        self.on_gerar_combate: Optional[Callable[[Dict], None]] = None
        self.use_llm_narracao: bool = False

        print("MESTRE AUTONOMO INICIALIZADO")
        print(f"   Estilo: {estilo.value}")
        print(f"   Duracao prevista: {duracao_prevista} sessoes")

    def criar_campanha_autonoma(
        self,
        tema: Optional[str] = None,
        party_size: int = 4,
        nivel_inicial: int = 1,
    ) -> Dict[str, Any]:
        """
        Cria campanha completa automaticamente.
        Gera: setting, arco narrativo, NPCs, encontros preparados.
        """
        print(f"\n{'='*80}")
        print("FASE 1: CRIACAO DO MUNDO")
        print(f"{'='*80}")

        prompt_criacao = (
            f"Crie uma campanha de 3D&T no estilo {self.estilo.value}. "
            f"Tema: {tema or 'livre'}. "
            f"Duracao: {self.duracao_prevista} sessoes para {party_size} jogadores nivel {nivel_inicial}. "
            "Forneca: Titulo, sinopse breve, tema central, 3 NPCs centrais, 3 locais chave, tom."
        )
        resposta = self.sistema.consultar(prompt_criacao, incluir_visuais=False)
        self.arco = self._parsear_criacao(resposta, tema)
        self._gerar_estrutura_atos(party_size, nivel_inicial)

        self.sistema.campanha.nome = self.arco.titulo

        self.fase = FaseCampanha.PREPARACAO
        print(f"\n[OK] Campanha criada: {self.arco.titulo}")
        print(f"   Sinopse: {(self.arco.sinopse or '')[:100]}...")
        print(f"   Atos planejados: {len(self.arco.atos)}")

        return {
            "titulo": self.arco.titulo,
            "sinopse": self.arco.sinopse,
            "fase": self.fase.name,
            "proximo_passo": "Preparacao de encontros",
        }

    def _parsear_criacao(
        self, resposta: RespostaMultimodal, tema: Optional[str]
    ) -> ArcoNarrativo:
        """Extrai estrutura da resposta de geracao (simplificado)."""
        partes: List[str] = [resposta.intencao or ""]
        if resposta.conteudo_gerado and isinstance(resposta.conteudo_gerado, dict):
            enc = resposta.conteudo_gerado.get("encontro") or resposta.conteudo_gerado
            if isinstance(enc, dict):
                partes.append(enc.get("nome", ""))
                partes.append(enc.get("descricao", ""))
            else:
                partes.append(str(resposta.conteudo_gerado))
        texto = " ".join(p for p in partes if p).strip() or "Aventura sem nome"
        linhas = texto.split("\n")
        titulo = (linhas[0] or "A Aventura Sem Nome").replace("Titulo:", "").strip()[:80]

        return ArcoNarrativo(
            titulo=titulo,
            sinopse=texto[:500],
            atos=[],
            npcs_centrais=["Misterioso", "Aliado", "Neutro"],
            locais_chave=["Lugar 1", "Lugar 2", "Lugar 3"],
            tema_central=tema or "redencao",
            tom=self.estilo,
        )

    def _gerar_estrutura_atos(
        self, party_size: int, nivel_inicial: int
    ) -> None:
        """Gera estrutura de atos dramaticos (3 atos padrao 3D&T)."""
        if not self.arco:
            return
        self.arco.atos = [
            {
                "nome": "O Chamado",
                "objetivo": "Introduzir personagens e conflito central",
                "cenas_chave": ["Encontro inicial", "Incidente incitante", "Primeiro desafio"],
                "reviravolta": "Descoberta da verdadeira ameaca",
                "sessao_inicio": 1,
                "sessao_fim": 2,
                "nivel_recomendado": nivel_inicial,
            },
            {
                "nome": "A Jornada",
                "objetivo": "Desenvolver conflito e personagens",
                "cenas_chave": ["Viagem perigosa", "Revelacao do vilao", "Teste de lealdade"],
                "reviravolta": "Traicao ou sacrificio inesperado",
                "sessao_inicio": 3,
                "sessao_fim": 4,
                "nivel_recomendado": nivel_inicial + 1,
            },
            {
                "nome": "O Confronto",
                "objetivo": "Climax e resolucao",
                "cenas_chave": ["Preparacao final", "Batalha epica", "Consequencias"],
                "reviravolta": "Custo da vitoria",
                "sessao_inicio": 5,
                "sessao_fim": 6,
                "nivel_recomendado": min(nivel_inicial + 2, 10),
            },
        ]

    def preparar_sessao(self, numero_sessao: int) -> Dict[str, Any]:
        """
        Prepara uma sessao especifica automaticamente.
        Gera: encontros, mapas, NPCs necessarios, descricoes.
        """
        print(f"\n{'='*80}")
        print(f"FASE 2: PREPARACAO DA SESSAO {numero_sessao}")
        print(f"{'='*80}")

        ato: Optional[Dict[str, Any]] = None
        if self.arco:
            ato = self.arco.proximo_atual(numero_sessao)
        if not ato and self.arco and self.arco.atos:
            ato = self.arco.atos[0]
        if not ato:
            ato = {
                "nome": "Cena",
                "cenas_chave": ["Cena 1"],
                "nivel_recomendado": 1,
                "sessao_inicio": 1,
                "sessao_fim": 2,
            }

        party_size = len(self.sistema.campanha.party_xp) or 4
        party_level = getattr(
            self.sistema, "_calcular_nivel_medio_party", lambda: 1
        )() or ato.get("nivel_recomendado", 1)
        ultimo_encontro = getattr(
            self.sistema, "_get_ultimo_encontro", lambda: "medio"
        )()
        party_info = {
            "party_size": party_size,
            "party_level": party_level,
            "ultimo_encontro": ultimo_encontro,
        }

        preparacao: Dict[str, Any] = {
            "sessao": numero_sessao,
            "ato": ato.get("nome", "Ato"),
            "cenas": [],
        }
        cenas_chave = ato.get("cenas_chave", ["Cena 1"])

        for cena_nome in cenas_chave:
            print(f"\n   Preparando: {cena_nome}")
            nome_lower = cena_nome.lower()
            if "encontro" in nome_lower or "batalha" in nome_lower:
                cena = self._preparar_cena_combate(cena_nome, party_info, ato)
            elif "viagem" in nome_lower or "exploracao" in nome_lower:
                cena = self._preparar_cena_exploracao(cena_nome, party_info)
            else:
                cena = self._preparar_cena_social(cena_nome, party_info)
            preparacao["cenas"].append(cena)
            print(f"      [OK] {cena['tipo']}: {cena.get('resumo', 'Cena preparada')}")

        self.sistema.campanha.registrar_evento(
            f"Preparacao Sessao {numero_sessao}: {ato.get('nome', '')}",
            tipo="preparacao",
            envolvidos=[],
            importancia=3,
            metadata={"cenas": len(preparacao["cenas"])},
        )
        self.fase = FaseCampanha.SESSAO_ATIVA
        self.preparacao_sessao_atual = preparacao

        # Inicializa estado estruturado da primeira cena da sessao
        if preparacao["cenas"]:
            primeira = preparacao["cenas"][0]
            desc_base = (
                primeira.get("descricao_ambiente")
                or primeira.get("resumo")
                or ato.get("objetivo", "")
                or "Cena inicial"
            )
            objetivos: List[str] = []
            if ato.get("objetivo"):
                objetivos.append(str(ato["objetivo"]))
            if primeira.get("tipo") == "combate":
                objetivos.append("sobreviver")
            self.estado_cena_atual = EstadoCena(
                nome=str(primeira.get("nome", "Cena 1")),
                descricao=str(desc_base),
                objetivos=objetivos,
                em_combate=primeira.get("tipo") == "combate",
            )

        return preparacao

    def _preparar_cena_combate(
        self, nome: str, party_info: Dict[str, Any], ato: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepara cena de combate usando gerador de encontros."""
        query = (
            f"crie encontro {party_info.get('ultimo_encontro', 'medio')} "
            f"para {party_info.get('party_size', 4)} jogadores "
            f"nivel {party_info.get('party_level', 1)}"
        )
        resposta = self.sistema.consultar(query, incluir_visuais=False)
        cg = resposta.conteudo_gerado or {}
        encontro = cg.get("encontro") if isinstance(cg, dict) else None
        return {
            "nome": nome,
            "tipo": "combate",
            "resumo": f"Encontro: {(encontro.get('nome') if encontro else 'A definir')}",
            "encontro_gerado": encontro,
            "dados_regras": (resposta.dados_recuperados or [])[:2],
            "sugestoes_mestre": resposta.sugestoes or [],
        }

    def _preparar_cena_exploracao(
        self, nome: str, party_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepara cena de exploracao/mapa."""
        mapas_elem = self.sistema.visual.listar_por_tipo(TipoVisual.MAPA_DUNGEON)
        mapa_escolhido: Optional[MapaProcessado] = None
        if mapas_elem:
            elem = random.choice(mapas_elem)
            mapa_escolhido = self.sistema.visual.mapas.get(elem.id)
        mapa_dict: Optional[Dict[str, Any]] = None
        if mapa_escolhido:
            mapa_dict = _mapa_para_dict(mapa_escolhido)
        return {
            "nome": nome,
            "tipo": "exploracao",
            "resumo": f"Exploracao: {(mapa_escolhido.nome if mapa_escolhido else 'Area selvagem')}",
            "mapa": mapa_dict,
            "descricao_ambiente": self._gerar_descricao_ambiente(),
            "perigos": ["Armadilha natural", "Monstro errante", "Terreno dificil"],
        }

    def _preparar_cena_social(
        self, nome: str, party_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepara cena de interacao social."""
        npc_query = f"crie NPC nivel {party_info.get('party_level', 1) + 2} para cena: {nome}"
        resposta = self.sistema.consultar(npc_query, incluir_visuais=False)
        analise = resposta.analise_inteligente or {}
        entidades = analise.get("entidades_principais", ["NPC Misterioso"])
        return {
            "nome": nome,
            "tipo": "social",
            "resumo": f"Interacao: {nome}",
            "npcs_envolvidos": entidades if isinstance(entidades, list) else [str(entidades)],
            "objetivo_cena": "Obter informacao ou alianca",
            "possiveis_desfechos": ["Sucesso diplomatico", "Conflito", "Informacao parcial"],
        }

    def _gerar_descricao_ambiente(self) -> str:
        """Gera descricao atmosferica conforme estilo."""
        ambientes = {
            EstiloNarrativo.EPICO: "Ruinas antigas ecoam com magia perdida. Colunas de marmore se elevam.",
            EstiloNarrativo.SOMBRIO: "A nevoa esconde formas indistintas. O silencio e quebrado por gotas d'agua.",
            EstiloNarrativo.HEROICO: "O sol ilumina um vale de possibilidades. Desafios aguardam, mas tambem gloria.",
            EstiloNarrativo.INTRIGA: "Cada sombra esconde olhos atentos. As paredes tem ouvidos.",
            EstiloNarrativo.EXPLORACAO: "Territorio inexplorado se estende a frente. Mapas falham aqui.",
        }
        return ambientes.get(self.estilo, ambientes[EstiloNarrativo.HEROICO])

    def iniciar_sessao_autonoma(self, numero: int) -> Dict[str, Any]:
        """Inicia sessao e comeca conducao autonoma."""
        print(f"\n{'='*80}")
        print(f"FASE 3: SESSAO {numero} INICIADA")
        print(f"{'='*80}")

        self.sistema.iniciar_sessao(numero)
        self.cena_atual = 0
        if self.fase != FaseCampanha.SESSAO_ATIVA:
            self.preparar_sessao(numero)
        introducao = self._narrar_introducao_sessao(numero)
        if self.on_narrar:
            self.on_narrar(introducao)
        return {
            "status": "sessao_ativa",
            "introducao": introducao,
            "proxima_acao": "aguardando_jogadores",
        }

    def _narrar_introducao_sessao(self, numero: int) -> str:
        """Gera introducao dramatica da sessao."""
        ato: Optional[Dict[str, Any]] = None
        if self.arco:
            ato = self.arco.proximo_atual(numero)
        nome_ato = (ato.get("nome", "CONTINUACAO") if ato else "CONTINUACAO").upper()
        contexto = "Inicio da jornada"
        if self.sistema.campanha.sessoes:
            contexto = self.sistema.campanha.gerar_resumo(1)
        return (
            f"\n{'='*60}\n"
            f"SESSAO {numero}: {nome_ato}\n"
            f"{'='*60}\n\n"
            f"{self._gerar_descricao_ambiente()}\n\n"
            f"Resumo do que aconteceu: {(contexto or '')[:200]}...\n\n"
            "A aventura continua...\n"
        )

    def processar_acao_jogadores(
        self, acao_jogadores: List[Dict[str, Any]]
    ) -> DecisaoMestre:
        """Processa acoes dos jogadores e decide reacao do mestre."""
        print(f"\n   Processando {len(acao_jogadores)} acoes...")
        intencoes = [
            a.get("intencao", "explorar") for a in acao_jogadores
        ]
        if any("atacar" in str(i) or "combate" in str(i) for i in intencoes):
            decisao = self._conduzir_combate(acao_jogadores)
        elif any("falar" in str(i) or "persuadir" in str(i) for i in intencoes):
            decisao = self._conduzir_interacao_social(acao_jogadores)
        elif any("investigar" in str(i) or "procurar" in str(i) or "explorar" in str(i) for i in intencoes):
            decisao = self._conduzir_exploracao(acao_jogadores)
        else:
            decisao = self._narrar_continuidade(acao_jogadores)
        if self.use_llm_narracao:
            decisao = self._enriquecer_com_llm(decisao, acao_jogadores)
        return decisao

    def _enriquecer_com_llm(
        self, decisao: DecisaoMestre, acoes: List[Dict[str, Any]]
    ) -> DecisaoMestre:
        """
        Usa LLM com schema Pydantic obrigatorio (AcaoResolvida).
        Executa o teste nos mesmos; valida e retenta se resposta for vaga.
        """
        try:
            from src.generation.llm_provider import get_chat_llm
            llm = get_chat_llm()
            from langchain_core.messages import HumanMessage
        except Exception as e:
            logger.debug("LLM nao disponivel para narracao: %s", e)
            return decisao

        a0 = acoes[0] if acoes else {}
        acao_desc = a0.get("acao_descricao", "agir")
        estado = self.estado_cena_atual

        base_estado = {
            "local": estado.nome if estado else "",
            "descricao": estado.descricao if estado else "",
            "descobertas": list(estado.descobertas) if estado else [],
            "inimigos_visiveis": list(estado.inimigos_visiveis) if estado else [],
            "objetivos": list(estado.objetivos) if estado else [],
            "em_combate": bool(estado.em_combate) if estado else False,
        }
        prompt = PROMPT_MESTRE_OBRIGATORIO.format(
            estado_json=json.dumps(base_estado, ensure_ascii=False),
            acao=acao_desc,
        )

        acao_resolvida: Optional[AcaoResolvida] = None
        erros_validacao: List[str] = []
        max_retries = 2

        for tentativa in range(max_retries + 1):
            try:
                acao_resolvida = self._invocar_llm_estruturado(llm, prompt, erros_validacao)
                if not acao_resolvida:
                    break
                erros = self._validar_resposta_mestre(
                    acao_resolvida.resultado_narrativo, acao_desc, acao_resolvida
                )
                if not erros:
                    break
                erros_validacao = erros
                if tentativa < max_retries:
                    prompt += f"\n\nCORRECAO NECESSARIA: {'; '.join(erros)}. Refaça a resposta."
            except Exception as e:
                logger.warning("Falha LLM estruturado (tentativa %d): %s", tentativa + 1, e)
                from pydantic import ValidationError
                if isinstance(e, ValidationError):
                    erros_validacao = [err.get("msg", str(err)) for err in (e.errors() or [])]
                    if tentativa < max_retries:
                        prompt += f"\n\nERRO NO SCHEMA: {'; '.join(erros_validacao)}. Corrija e retorne JSON valido."
                        continue
                if tentativa == max_retries:
                    return decisao

        if not acao_resolvida:
            return decisao

        # Executar teste nos mesmos se tipo_acao for teste_atributo
        teste_novo: Optional[TesteRPG] = None
        resultado_final = acao_resolvida.resultado_narrativo

        if acao_resolvida.atributo_usado:
            attr = atributo_interno(acao_resolvida.atributo_usado)
            cd = cd_por_dificuldade(acao_resolvida.dificuldade or "Normal")
            modificador = self._modificador_personagem(attr, a0.get("personagem"))
            d6, total, sucesso = resolver_teste(cd, modificador, attr)
            teste_novo = TesteRPG(
                atributo=nome_atributo_completo(attr, acao_resolvida.descricao_teste or ""),
                cd=cd,
                resultado=total,
                sucesso=sucesso,
                descricao=descricao_teste_3dt(attr, cd, d6, total, sucesso, modificador),
            )
            resultado_final += f" (Rolou 1d6+{modificador}={total} vs CD {cd} — {'Sucesso' if sucesso else 'Falha'})"

        # Converter MudancaEstado para dict e aplicar (merge)
        mud_dict = {
            "descobertas_add": list(acao_resolvida.mudanca_estado.descobertas_add),
            "inimigos_add": list(acao_resolvida.mudanca_estado.inimigos_add),
            "objetivos_add": list(acao_resolvida.mudanca_estado.objetivos_add),
        }
        if acao_resolvida.mudanca_estado.em_combate is not None:
            mud_dict["em_combate"] = acao_resolvida.mudanca_estado.em_combate
        self._aplicar_mudanca_estado(mud_dict, teste_novo or decisao.teste_necessario)

        opcoes = [str(o)[:80] for o in acao_resolvida.proximas_opcoes]
        if len(opcoes) < 2:
            opcoes = decisao.opcoes_jogador

        return DecisaoMestre(
            tipo=decisao.tipo,
            conteudo=resultado_final,
            mecanica_envolvida=decisao.mecanica_envolvida,
            testes_solicitados=decisao.testes_solicitados,
            consequencias_possiveis=decisao.consequencias_possiveis,
            proximos_passos=decisao.proximos_passos,
            opcoes_jogador=opcoes[:5] if opcoes else decisao.opcoes_jogador,
            teste_necessario=teste_novo or decisao.teste_necessario,
            resultado_acao=resultado_final,
            mudanca_estado=mud_dict,
            narracao=resultado_final,
        )

    def _invocar_llm_estruturado(
        self, llm: Any, prompt: str, erros_anteriores: List[str]
    ) -> Optional[AcaoResolvida]:
        """Tenta with_structured_output; fallback para JSON + Pydantic."""
        from langchain_core.messages import HumanMessage

        # Tentativa 1: structured output (OpenAI, alguns Ollama)
        try:
            if hasattr(llm, "with_structured_output"):
                structured = llm.with_structured_output(AcaoResolvida)
                result = structured.invoke([HumanMessage(content=prompt)])
                if isinstance(result, AcaoResolvida):
                    logger.info("Schema recebido (structured): %s", result.model_dump_json(indent=2)[:500])
                    return result
        except Exception as e:
            logger.debug("with_structured_output falhou: %s", e)

        # Tentativa 2: JSON parse + Pydantic validate
        try:
            resp = llm.invoke([HumanMessage(content=prompt)])
            text = resp.content if hasattr(resp, "content") else str(resp)
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("JSON nao encontrado")
            dados = json.loads(text[start : end + 1])
            # Normalizar para schema (mudanca_estado pode vir como dict)
            if "mudanca_estado" in dados and isinstance(dados["mudanca_estado"], dict):
                m = dados["mudanca_estado"]
                dados["mudanca_estado"] = {
                    "descobertas_add": m.get("descobertas_add", []),
                    "inimigos_add": m.get("inimigos_add", []),
                    "objetivos_add": m.get("objetivos_add", []),
                    "em_combate": m.get("em_combate"),
                }
            parsed = AcaoResolvida.model_validate(dados)
            logger.info("Schema recebido (JSON parse): %s", parsed.model_dump_json(indent=2)[:500])
            return parsed
        except Exception as e:
            logger.warning("Parse JSON+Pydantic falhou: %s", e)
            raise

    def _validar_resposta_mestre(
        self, texto: str, acao_anterior: str, acao_resolvida: AcaoResolvida
    ) -> List[str]:
        """Rejeita respostas invalidas. Retorna lista de erros (vazia = valida)."""
        erros: List[str] = []
        texto_lower = texto.lower()
        acao_lower = acao_anterior.lower()

        palavras_teste = [
            "atacar", "investigar", "perceber", "convencer", "procurar",
            "ler", "intimidar", "olhar", "buscar", "explorar", "runas",
        ]
        precisa_teste = any(p in acao_lower for p in palavras_teste)
        if precisa_teste and not acao_resolvida.atributo_usado:
            erros.append(
                f"Acao '{acao_anterior[:50]}...' requer teste. Especifique atributo_usado: "
                "Forca, Habilidade, Resistencia ou Armadura."
            )

        for frase in FRASES_PROIBIDAS:
            if frase in texto_lower:
                erros.append(f"Narracao muito vaga: evite '{frase}'")

        if "sol ilumina um vale" in texto_lower or "vale de possibilidades" in texto_lower:
            erros.append("Repetindo introducao em vez de avançar")

        return erros

    def _simular_acoes_jogadores(self) -> List[Dict[str, Any]]:
        """Simula acoes de jogadores para testes/demo (em producao viria da interface)."""
        personagens = [
            p.nome for p in self.sistema.campanha.personagens.values()
            if getattr(p, "tipo", "") == "pc"
        ]
        if not personagens:
            personagens = ["Thorin", "Lyra"]
        personagem = personagens[self.cena_atual % len(personagens)]
        acoes_tipo = [
            {"acao_descricao": "investiga a entrada da masmorra", "intencao": "investigar"},
            {"acao_descricao": "ataca o inimigo mais proximo", "intencao": "atacar"},
            {"acao_descricao": "tenta convencer o NPC a cooperar", "intencao": "falar"},
        ]
        acao = acoes_tipo[self.cena_atual % len(acoes_tipo)]
        return [
            {
                "jogador": "demo",
                "personagem": personagem,
                "acao_descricao": acao["acao_descricao"],
                "intencao": acao["intencao"],
            }
        ]

    def _modificador_personagem(self, atributo: str, nome_personagem: Optional[str] = None) -> int:
        """
        Retorna modificador do atributo (F/H/R/A) para testes 3D&T.
        Usa ficha OCR ou valores padrao por nivel.
        """
        if nome_personagem and hasattr(self.sistema, "campanha"):
            for p in getattr(self.sistema.campanha, "personagens", {}).values():
                if getattr(p, "nome", "") == nome_personagem:
                    attrs = getattr(p, "atributos", None) or {}
                    key = atributo.upper() if len(atributo) == 1 else {"F": "F", "H": "H", "R": "R", "A": "A"}.get(atributo.upper(), "H")
                    if key in attrs:
                        return int(attrs[key])
                    break
            # Fichas OCR no sistema multimodal
            cv = getattr(self.sistema, "componente_visual", None)
            if cv and getattr(cv, "fichas_ocr", []):
                for ficha in cv.fichas_ocr:
                    if ficha.nome_personagem and ficha.nome_personagem.lower() == (nome_personagem or "").lower():
                        attrs = getattr(ficha, "atributos", {}) or {}
                        key = atributo.upper() if len(atributo) == 1 else "H"
                        if key in attrs:
                            return int(attrs[key])
                        break
        # Fallback: nivel medio da party (atributo tipico 2-3 para nivel 1)
        calc = getattr(self.sistema, "_calcular_nivel_medio_party", None)
        nivel = (calc() if callable(calc) else 1) or 1
        return min(2 + (nivel - 1), 5)

    def _cena_atual_preparada(self) -> Optional[Dict[str, Any]]:
        """Retorna a cena preparada para a cena atual, se houver."""
        if not self.preparacao_sessao_atual or not self.preparacao_sessao_atual.get("cenas"):
            return None
        cenas = self.preparacao_sessao_atual["cenas"]
        if self.cena_atual >= len(cenas):
            return None
        return cenas[self.cena_atual]

    def _aplicar_mudanca_estado(
        self, mudanca: Dict[str, Any], teste: Optional[TesteRPG]
    ) -> None:
        """
        Aplica mudancas de estado na cena atual (MERGE, nao replace).
        Persiste eventos na campanha para estado entre turnos.
        """
        if not self.estado_cena_atual:
            return
        estado = self.estado_cena_atual
        if teste:
            estado.ultimo_teste = teste
        # Merge descobertas (nao substituir)
        for item in mudanca.get("descobertas_add", []):
            if item not in estado.descobertas:
                estado.descobertas.append(str(item))
        # Merge inimigos visiveis
        for inimigo in mudanca.get("inimigos_add", []):
            if inimigo not in estado.inimigos_visiveis:
                estado.inimigos_visiveis.append(str(inimigo))
        # Merge objetivos
        for obj in mudanca.get("objetivos_add", []):
            if obj not in estado.objetivos:
                estado.objetivos.append(str(obj))
        if "em_combate" in mudanca:
            estado.em_combate = bool(mudanca["em_combate"])
        # Persistir evento na campanha (estado entre turnos)
        if mudanca and hasattr(self, "sistema") and self.sistema.campanha:
            partes = []
            if mudanca.get("descobertas_add"):
                partes.append(f"Descobertas: {mudanca['descobertas_add']}")
            if mudanca.get("inimigos_add"):
                partes.append(f"Inimigos: {mudanca['inimigos_add']}")
            if "em_combate" in mudanca:
                partes.append(f"Combate: {mudanca['em_combate']}")
            if partes or teste:
                desc = "; ".join(partes) if partes else (teste.descricao if teste else "Mudanca de estado")
                self.sistema.campanha.registrar_evento(desc, tipo="decisao")

    def _gerar_opcoes_jogador(self, tipo: str, cena: Optional[Dict[str, Any]]) -> List[str]:
        """Gera 4-5 opcoes de multipla escolha coerentes com a cena."""
        if tipo == "combate":
            opts = [
                "Atacar o inimigo mais proximo",
                "Tomar posicao defensiva",
                "Tentar intimidar ou negociar",
                "Recuar para cobertura",
                "Usar habilidade ou magia",
            ]
            if cena and cena.get("sugestoes_mestre"):
                extra = cena["sugestoes_mestre"][:2]
                if extra:
                    opts = extra + opts[len(extra) :]
            return opts[:5]
        if tipo == "social":
            opts = [
                "Continuar conversando com calma",
                "Fazer uma proposta ou oferta",
                "Encerrar a conversa",
                "Insistir no ponto",
                "Mudar de assunto",
            ]
            if cena and cena.get("possiveis_desfechos"):
                extra = cena["possiveis_desfechos"][:2]
                if extra:
                    opts = extra + opts[len(extra) :]
            return opts[:5]
        if tipo == "exploracao":
            opts = [
                "Investigar as runas e paredes",
                "Seguir pelo corredor adiante",
                "Procurar armadilhas com cuidado",
                "Voltar e avisar o grupo",
                "Descansar e observar",
            ]
            if cena and cena.get("perigos"):
                p = cena["perigos"][:1]
                if p:
                    opts[2] = f"Procurar armadilhas ({p[0] if isinstance(p[0], str) else 'perigos'})"
            return opts[:5]
        if tipo == "narracao":
            return [
                "Seguir em frente",
                "Olhar em volta com atencao",
                "Falar com o grupo",
                "Aguardar e observar",
                "Investigar algo especifico",
            ][:5]
        return ["Continuar", "Investigar", "Falar com alguem", "Aguardar", "Mudar de plano"][:5]

    def _conduzir_combate(self, acoes: List[Dict[str, Any]]) -> DecisaoMestre:
        """Conduz cena de combate (regras 3D&T: iniciativa, turnos)."""
        a0 = acoes[0] if acoes else {}
        personagem = a0.get("personagem", "O grupo")
        acao_desc = a0.get("acao_descricao", "avanca")
        cena = self._cena_atual_preparada()
        inimigos_texto = "Figuras hostis se movem na penumbra."
        if cena and cena.get("encontro_gerado"):
            enc = cena["encontro_gerado"]
            nome_enc = enc.get("nome", "Inimigos")
            inimigos = enc.get("inimigos") or enc.get("oponentes") or []
            if inimigos:
                nomes = [str(i.get("nome", i.get("tipo", "?"))) for i in inimigos[:3]]
                inimigos_texto = f"{nome_enc}: {', '.join(nomes)}. Eles reagem ao movimento!"
            else:
                inimigos_texto = f"{nome_enc}. A ameaca se revela!"
        # Teste de iniciativa 3D&T: 1d6 + H vs CD por dificuldade
        cd = cd_por_dificuldade(Dificuldade3DT.NORMAL)
        attr = atributo_para_teste("iniciativa")
        modificador = self._modificador_personagem(attr, a0.get("personagem"))
        d6, total, sucesso = resolver_teste(cd, modificador, attr)
        teste = TesteRPG(
            atributo=nome_atributo_completo(attr, "Iniciativa"),
            cd=cd,
            resultado=total,
            sucesso=sucesso,
            descricao=descricao_teste_3dt(attr, cd, d6, total, sucesso, modificador, "Iniciativa"),
        )
        resultado_acao = (
            f"{personagem} se prepara para o combate. "
            f"{'Age rapido e ganha vantagem posicional.' if sucesso else 'Nao consegue reagir a tempo.'}"
        )
        narracao = (
            f"\nCOMBATE!\n\n"
            f"{resultado_acao} {inimigos_texto}\n\n"
            f"{teste.descricao}\n"
        )
        mudanca_estado = {"em_combate": True}
        self._aplicar_mudanca_estado(mudanca_estado, teste)
        return DecisaoMestre(
            tipo="combate",
            conteudo=narracao,
            mecanica_envolvida="Iniciativa (Habilidade)",
            testes_solicitados=[
                {"atributo": "Habilidade", "dificuldade": "normal", "motivo": "Iniciativa"}
            ],
            consequencias_possiveis=["Vantagem posicional", "Ataque surpresa", "Emboscada"],
            proximos_passos=["Resolver iniciativa", "Descrever campo de batalha", "Primeiro turno"],
            opcoes_jogador=self._gerar_opcoes_jogador("combate", cena),
            teste_necessario=teste,
            resultado_acao=resultado_acao,
            mudanca_estado=mudanca_estado,
            narracao=narracao,
        )

    def _conduzir_interacao_social(
        self, acoes: List[Dict[str, Any]]
    ) -> DecisaoMestre:
        """Conduz interacao social (Atitude/roleplay 3D&T)."""
        a0 = acoes[0] if acoes else {}
        personagem = a0.get("personagem", "Alguem")
        acao_desc = a0.get("acao_descricao", "interage")
        cena = self._cena_atual_preparada()
        npc_nome = "Um figura misteriosa"
        if cena and cena.get("npcs_envolvidos"):
            npcs = cena["npcs_envolvidos"]
            npc_nome = npcs[0] if isinstance(npcs[0], str) else str(npcs[0]) if npcs else npc_nome
        reacoes = [
            f"{npc_nome} cruza os bracos, considerando suas palavras.",
            f"{npc_nome} inclina a cabeca, curioso.",
            f"Os olhos de {npc_nome} brilham com interesse ou desconfianca.",
        ]
        reacao = reacoes[self.cena_atual % len(reacoes)]
        cd = cd_por_dificuldade(Dificuldade3DT.NORMAL)
        attr = atributo_para_teste("social")
        modificador = self._modificador_personagem(attr, a0.get("personagem"))
        d6, total, sucesso = resolver_teste(cd, modificador, attr)
        teste = TesteRPG(
            atributo=nome_atributo_completo(attr, "Lábia"),
            cd=cd,
            resultado=total,
            sucesso=sucesso,
            descricao=descricao_teste_3dt(attr, cd, d6, total, sucesso, modificador, "Lábia"),
        )
        resultado_acao = (
            f"{personagem} {acao_desc}. "
            f"{'A atitude parece agradar o NPC.' if sucesso else 'O NPC permanece desconfiado.'}"
        )
        narracao = (
            f"\nINTERACAO\n\n{resultado_acao} {reacao}\n\n{teste.descricao}\n"
        )
        mudanca_estado: Dict[str, Any] = {}
        self._aplicar_mudanca_estado(mudanca_estado, teste)
        return DecisaoMestre(
            tipo="social",
            conteudo=narracao,
            mecanica_envolvida="Teste de Atitude (regra opcional 3D&T)",
            testes_solicitados=[
                {"atributo": "Atitude/Roleplay", "dificuldade": "variavel", "motivo": "Persuasao"}
            ],
            consequencias_possiveis=["Sucesso total", "Informacao parcial", "Suspeita", "Hostilidade"],
            proximos_passos=["Resolver teste", "NPC reage", "Consequencias"],
            opcoes_jogador=self._gerar_opcoes_jogador("social", cena),
            teste_necessario=teste,
            resultado_acao=resultado_acao,
            mudanca_estado=mudanca_estado,
            narracao=narracao,
        )

    def _conduzir_exploracao(self, acoes: List[Dict[str, Any]]) -> DecisaoMestre:
        """Conduz exploracao (Percepcao/Investigacao) com descricao real da cena."""
        a0 = acoes[0] if acoes else {}
        personagem = a0.get("personagem", "Alguem")
        acao_desc = a0.get("acao_descricao", "investiga")
        cena = self._cena_atual_preparada()

        # Texto do ambiente: usar cena preparada ou fallback
        if cena and cena.get("descricao_ambiente"):
            ambiente = cena["descricao_ambiente"]
        else:
            ambiente = self._gerar_descricao_ambiente()

        # Pistas/perigos concretos
        perigos = []
        if cena and cena.get("perigos"):
            perigos = cena["perigos"] if isinstance(cena["perigos"], list) else [str(cena["perigos"])]
        if cena and cena.get("mapa") and cena["mapa"].get("pontos_interesse"):
            pois = cena["mapa"]["pontos_interesse"][:3]
            detalhes = [f"{p.get('label', '?')}: {p.get('descricao', '')[:60]}" for p in pois]
        else:
            detalhes = [
                "Paredes de pedra com runas apagadas.",
                "Um corredor escuro se abre a frente.",
                "Restos de tochas e equipamento abandonado.",
            ]
        idx = self.cena_atual % len(detalhes)
        pista = detalhes[idx]
        aberturas = [
            "Ao olhar com atencao, ",
            "O ambiente revela: ",
            "Voce percebe: ",
        ]
        abertura = aberturas[self.cena_atual % len(aberturas)]
        bloco_ambiente = f"{ambiente}\n\n{abertura}{pista}"
        if perigos:
            bloco_ambiente += f"\n\nCuidado: {', '.join(perigos[:2])}."
        # Teste de percepcao 3D&T: 1d6 + H vs CD
        cd = cd_por_dificuldade(Dificuldade3DT.NORMAL)
        attr = atributo_para_teste("percepcao")
        modificador = self._modificador_personagem(attr, a0.get("personagem"))
        d6, total, sucesso = resolver_teste(cd, modificador, attr)
        teste = TesteRPG(
            atributo=nome_atributo_completo(attr, "Percepção"),
            cd=cd,
            resultado=total,
            sucesso=sucesso,
            descricao=descricao_teste_3dt(attr, cd, d6, total, sucesso, modificador, "Percepção"),
        )
        if sucesso:
            descoberta = pista
            resultado_acao = (
                f"{personagem} {acao_desc} e percebe algo importante: {descoberta}"
            )
            mudanca_estado = {"descobertas_add": [descoberta]}
        else:
            resultado_acao = (
                f"{personagem} {acao_desc}, mas nao encontra nada alem do obvio."
            )
            mudanca_estado = {}
        narracao = (
            f"\n{resultado_acao}\n\n{bloco_ambiente}\n\n{teste.descricao}\n"
        )
        self._aplicar_mudanca_estado(mudanca_estado, teste)
        return DecisaoMestre(
            tipo="exploracao",
            conteudo=narracao,
            mecanica_envolvida="Percepcao/Investigacao",
            testes_solicitados=[
                {"atributo": "Habilidade", "dificuldade": "normal", "motivo": "Percepcao"}
            ],
            consequencias_possiveis=["Descoberta importante", "Armadilha detectada", "Nada encontrado", "Perigo iminente"],
            proximos_passos=["Resultado da busca", "Novas opcoes reveladas"],
            opcoes_jogador=self._gerar_opcoes_jogador("exploracao", cena),
            teste_necessario=teste,
            resultado_acao=resultado_acao,
            mudanca_estado=mudanca_estado,
            narracao=narracao,
        )

    def _narrar_continuidade(
        self, acoes: List[Dict[str, Any]]
    ) -> DecisaoMestre:
        """Narra continuidade quando nao ha mecanica especifica."""
        a0 = acoes[0] if acoes else {}
        personagem = a0.get("personagem", "O grupo")
        acao_desc = a0.get("acao_descricao", "avanca")
        cena = self._cena_atual_preparada()
        nome_cena = cena.get("nome", "A cena") if cena else "A cena"
        frases = [
            f"{personagem} {acao_desc}. {nome_cena} segue seu curso.",
            f"{self._gerar_descricao_ambiente()[:80]}... {personagem} segue.",
            f"O momento e de {nome_cena.lower()}. {personagem} age.",
        ]
        conteudo = frases[self.cena_atual % len(frases)]
        return DecisaoMestre(
            tipo="narracao",
            conteudo=conteudo,
            mecanica_envolvida=None,
            testes_solicitados=[],
            consequencias_possiveis=["Cena continua"],
            proximos_passos=["Aguardar proximas acoes"],
            opcoes_jogador=self._gerar_opcoes_jogador("narracao", cena),
             teste_necessario=None,
             resultado_acao=conteudo,
             mudanca_estado={},
             narracao=conteudo,
        )

    def avancar_cena(
        self, resultado_acoes: Dict[str, Any]
    ) -> Optional[DecisaoMestre]:
        """Avanca narrativa baseado em resultados. Retorna None se sessao terminou."""
        self.cena_atual += 1
        if self.cena_atual >= 3:
            return self._finalizar_sessao_autonoma()
        prep = self.preparacao_sessao_atual
        prox_nome = "Cena"
        if prep and prep.get("cenas") and self.cena_atual < len(prep["cenas"]):
            prox_cena = prep["cenas"][self.cena_atual]
            prox_nome = prox_cena.get("nome", "Cena")
            # Atualiza estado estruturado para a nova cena
            desc_base = (
                prox_cena.get("descricao_ambiente")
                or prox_cena.get("resumo")
                or "Cena em andamento"
            )
            objetivos: List[str] = []
            if isinstance(prep.get("ato"), str):
                objetivos.append(prep["ato"])
            if prox_cena.get("tipo") == "combate":
                objetivos.append("sobreviver")
            self.estado_cena_atual = EstadoCena(
                nome=str(prox_nome),
                descricao=str(desc_base),
                objetivos=objetivos,
                em_combate=prox_cena.get("tipo") == "combate",
            )
        transicoes = [
            f"Apos o que aconteceu, voces seguem para: {prox_nome}.",
            f"A situacao evolui. {prox_nome} se apresenta.",
            f"Novo momento: {prox_nome}. O que fazem?\n",
        ]
        transicao = (
            f"\n--- CENA {self.cena_atual + 1}: {prox_nome} ---\n\n"
            f"{transicoes[self.cena_atual % len(transicoes)]}\n"
        )
        return DecisaoMestre(
            tipo="narracao",
            conteudo=transicao,
            mecanica_envolvida=None,
            testes_solicitados=[],
            consequencias_possiveis=["Nova situacao"],
            proximos_passos=["Descrever nova cena", "Aguardar acoes"],
            opcoes_jogador=self._gerar_opcoes_jogador("narracao", None),
        )

    def _finalizar_sessao_autonoma(self) -> DecisaoMestre:
        """Finaliza sessao automaticamente."""
        resumo_texto = "Sessao conduzida automaticamente."
        self.sistema.finalizar_sessao(resumo_texto)
        self.fase = FaseCampanha.ENTRE_SESSOES
        return DecisaoMestre(
            tipo="pausa",
            conteudo=(
                "\nSESSAO FINALIZADA\n\n"
                f"{resumo_texto}\n\n"
                "Preparando proxima sessao...\n"
            ),
            mecanica_envolvida="XP e Progressao",
            testes_solicitados=[],
            consequencias_possiveis=["Level up", "Novos itens", "Revelacoes"],
            proximos_passos=["Processar XP", "Preparar proxima sessao", "Agendar"],
            opcoes_jogador=["Ver resumo da sessao", "Preparar proxima sessao", "Consultar regras", "Fechar"],
        )

    def executar_sessao_completa(self, numero: int) -> List[DecisaoMestre]:
        """Executa sessao inteira autonoma (para testes/demo)."""
        self.iniciar_sessao_autonoma(numero)
        historico_decisoes: List[DecisaoMestre] = []

        for cena_num in range(3):
            print(f"\n--- CENA {cena_num + 1} ---")
            acoes_simuladas = self._simular_acoes_jogadores()
            decisao = self.processar_acao_jogadores(acoes_simuladas)
            historico_decisoes.append(decisao)
            preview = (decisao.conteudo[:100] + "...") if len(decisao.conteudo) > 100 else decisao.conteudo
            print(f"Mestre: {preview}")
            resultado = self.avancar_cena({"sucesso": True})
            if resultado is not None:
                historico_decisoes.append(resultado)

        return historico_decisoes

    def exportar_estado(self) -> Dict[str, Any]:
        """Exporta estado completo para salvar jogo."""
        arco_data: Optional[Dict[str, Any]] = None
        if self.arco:
            arco_data = self.arco.to_dict()
        estado_cena: Optional[Dict[str, Any]] = None
        if self.estado_cena_atual:
            estado_cena = {
                "nome": self.estado_cena_atual.nome,
                "descricao": self.estado_cena_atual.descricao,
                "descobertas": list(self.estado_cena_atual.descobertas),
                "inimigos_visiveis": list(self.estado_cena_atual.inimigos_visiveis),
                "objetivos": list(self.estado_cena_atual.objetivos),
                "ultimo_teste": (
                    {
                        "atributo": self.estado_cena_atual.ultimo_teste.atributo,
                        "cd": self.estado_cena_atual.ultimo_teste.cd,
                        "resultado": self.estado_cena_atual.ultimo_teste.resultado,
                        "sucesso": self.estado_cena_atual.ultimo_teste.sucesso,
                        "descricao": self.estado_cena_atual.ultimo_teste.descricao,
                    }
                    if self.estado_cena_atual.ultimo_teste
                    else None
                ),
                "em_combate": self.estado_cena_atual.em_combate,
            }
        return {
            "arco": arco_data,
            "fase": self.fase.name,
            "cena_atual": self.cena_atual,
            "estilo": self.estilo.value,
            "campanha": self.sistema.campanha.campaign_id,
            "estado_cena": estado_cena,
            "timestamp": datetime.now().isoformat(),
        }

    def carregar_estado(self, estado: Dict[str, Any]) -> None:
        """Restaura estado de jogo salvo."""
        arco_data = estado.get("arco")
        if arco_data and isinstance(arco_data, dict):
            tom_val = arco_data.get("tom", "heroico")
            tom = (
                EstiloNarrativo(tom_val)
                if isinstance(tom_val, str)
                else tom_val
            )
            self.arco = ArcoNarrativo(
                titulo=arco_data.get("titulo", "Aventura"),
                sinopse=arco_data.get("sinopse", ""),
                atos=arco_data.get("atos", []),
                npcs_centrais=arco_data.get("npcs_centrais", []),
                locais_chave=arco_data.get("locais_chave", []),
                tema_central=arco_data.get("tema_central", ""),
                tom=tom,
            )
        fase_name = estado.get("fase", "CRIACAO_MUNDO")
        try:
            self.fase = FaseCampanha[fase_name]
        except KeyError:
            self.fase = FaseCampanha.CRIACAO_MUNDO
        self.cena_atual = int(estado.get("cena_atual", 0))
        estilo_val = estado.get("estilo", "heroico")
        if isinstance(estilo_val, str):
            self.estilo = EstiloNarrativo(estilo_val)
        else:
            self.estilo = estilo_val


def demo_mestre_autonomo() -> MestreAutonomo3DT:
    """Demonstracao do mestre autonomo completo."""
    print("=" * 80)
    print("DEMONSTRACAO: MESTRE AUTONOMO 3D&T")
    print("=" * 80)

    mestre = MestreAutonomo3DT(
        estilo=EstiloNarrativo.HEROICO,
        duracao_prevista=3,
    )
    print("\nINICIANDO AUTOMACAO COMPLETA\n")

    campanha = mestre.criar_campanha_autonoma(
        tema="Uma antiga masmorra ressurge, trazendo monstros que ameacam a vila",
        party_size=4,
        nivel_inicial=1,
    )

    prep = mestre.preparar_sessao(1)
    print(f"\nCenas preparadas: {len(prep['cenas'])}")
    for i, cena in enumerate(prep["cenas"], 1):
        print(f"   {i}. [{cena['tipo'].upper()}] {cena.get('resumo', '')}")

    sessao = mestre.iniciar_sessao_autonoma(1)
    print(mestre._narrar_introducao_sessao(1))

    acoes_teste = [
        {
            "jogador": "Player1",
            "personagem": "Thorin",
            "acao_descricao": "investiga a entrada da masmorra",
            "intencao": "investigar",
        }
    ]
    decisao = mestre.processar_acao_jogadores(acoes_teste)
    print("\nDECISAO DO MESTRE:")
    print(f"   Tipo: {decisao.tipo}")
    print(f"   Mecanica: {decisao.mecanica_envolvida or 'Nenhuma'}")
    print(f"   Testes: {len(decisao.testes_solicitados)}")

    print(f"\n{'='*80}")
    print("[OK] DEMONSTRACAO CONCLUIDA")
    print(f"{'='*80}")
    sa = mestre.sistema.campanha.sessao_atual
    print(f"Estado final: {mestre.fase.name}")
    print(f"Sessao: {sa.numero if sa else 'Nenhuma'}")

    return mestre


if __name__ == "__main__":
    demo_mestre_autonomo()
