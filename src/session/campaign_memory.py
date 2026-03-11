"""
Nivel 6: Sistema de Memoria e Persistencia de Campanha.
Mantem estado, historico e evolucao ao longo do tempo.
"""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class EventoCampanha:
    """Evento registrado na campanha."""
    id: str
    timestamp: str
    tipo: str
    descricao: str
    envolvidos: List[str]
    consequencias: List[str] = field(default_factory=list)
    xp_ganho: int = 0
    tesouro: List[str] = field(default_factory=list)
    local: str = ""
    importancia: int = 1


@dataclass
class PersonagemRecorrente:
    """NPC ou PC com historico na campanha."""
    id: str
    nome: str
    tipo: str
    raca: str
    nivel: int
    primeira_aparicao: str
    ultima_aparicao: str
    aparicoes: int = 0
    relacoes: Dict[str, str] = field(default_factory=dict)
    destino_atual: str = "vivo"
    notas: str = ""


@dataclass
class ThreadHistoria:
    """Fio de historia ativo na campanha."""
    id: str
    titulo: str
    descricao: str
    status: str
    inicio: str
    envolvidos: List[str]
    eventos_relacionados: List[str] = field(default_factory=list)
    proximo_gancho: str = ""


@dataclass
class SessaoJogo:
    """Uma sessao individual de jogo."""
    id: str
    numero: int
    data: str
    duracao_minutos: int = 0
    eventos: List[str] = field(default_factory=list)
    encontros: List[str] = field(default_factory=list)
    npcs_novos: List[str] = field(default_factory=list)
    resumo_gerado: str = ""


class CampaignMemory:
    """
    Sistema de memoria persistente da campanha.
    Mantem todo o historico e permite consultas inteligentes.
    """

    def __init__(
        self,
        campaign_id: Optional[str] = None,
        nome: str = "Nova Aventura",
    ) -> None:
        self.campaign_id = campaign_id or str(uuid.uuid4())[:8]
        self.nome = nome
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

        self.personagens: Dict[str, PersonagemRecorrente] = {}
        self.eventos: Dict[str, EventoCampanha] = {}
        self.threads: Dict[str, ThreadHistoria] = {}
        self.sessoes: Dict[str, SessaoJogo] = {}

        self.sessao_atual: Optional[SessaoJogo] = None
        self.combate_atual: Optional[Dict[str, Any]] = None
        self.party_xp: Dict[str, int] = {}
        self.inventario_party: List[str] = []

        self._index_por_tipo: Dict[str, Set[str]] = {
            "combate": set(),
            "social": set(),
            "exploracao": set(),
            "decisao": set(),
            "sessao": set(),
        }

        self.save_path = Path("data/campaigns") / f"campaign_{self.campaign_id}.json"
        self._load()

    def _load(self) -> None:
        """Carrega campanha do disco se existir."""
        if not self.save_path.exists():
            return
        try:
            with self.save_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            self.nome = data.get("nome", self.nome)
            self.created_at = data.get("created_at", self.created_at)

            for k, v in data.get("personagens", {}).items():
                self.personagens[k] = PersonagemRecorrente(**v)

            for k, v in data.get("eventos", {}).items():
                self.eventos[k] = EventoCampanha(**v)

            for k, v in data.get("threads", {}).items():
                self.threads[k] = ThreadHistoria(**v)

            for k, v in data.get("sessoes", {}).items():
                self.sessoes[k] = SessaoJogo(**v)

            self.party_xp = data.get("party_xp", {})
            self.inventario_party = data.get("inventario_party", [])

            for eid, evt in self.eventos.items():
                self._index_por_tipo.setdefault(evt.tipo, set()).add(eid)

            print(
                f"[OK] Campanha '{self.nome}' carregada "
                f"({len(self.eventos)} eventos)"
            )
        except Exception as e:
            print(f"[AVISO] Erro ao carregar campanha: {e}")

    def save(self) -> None:
        """Salva campanha no disco."""
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now().isoformat()

        data = {
            "campaign_id": self.campaign_id,
            "nome": self.nome,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "personagens": {k: asdict(v) for k, v in self.personagens.items()},
            "eventos": {k: asdict(v) for k, v in self.eventos.items()},
            "threads": {k: asdict(v) for k, v in self.threads.items()},
            "sessoes": {k: asdict(v) for k, v in self.sessoes.items()},
            "party_xp": self.party_xp,
            "inventario_party": self.inventario_party,
        }

        with self.save_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def iniciar_sessao(self, numero: Optional[int] = None) -> SessaoJogo:
        """Inicia nova sessao de jogo."""
        if numero is None:
            numero = len(self.sessoes) + 1

        sessao = SessaoJogo(
            id=str(uuid.uuid4())[:8],
            numero=numero,
            data=datetime.now().isoformat(),
        )
        self.sessoes[sessao.id] = sessao
        self.sessao_atual = sessao

        self._registrar_evento(
            tipo="sessao",
            descricao=f"Sessao {numero} iniciada",
            envolvidos=[],
            importancia=2,
        )
        self.save()
        return sessao

    def finalizar_sessao(self, resumo: str = "") -> None:
        """Finaliza sessao atual."""
        if not self.sessao_atual:
            return
        inicio = datetime.fromisoformat(self.sessao_atual.data)
        fim = datetime.now()
        duracao = int((fim - inicio).total_seconds() // 60)
        self.sessao_atual.duracao_minutos = duracao
        self.sessao_atual.resumo_gerado = resumo or self._gerar_resumo_sessao()

        self._registrar_evento(
            tipo="sessao",
            descricao=f"Sessao {self.sessao_atual.numero} finalizada ({duracao} min)",
            envolvidos=[],
            importancia=2,
        )
        self.sessao_atual = None
        self.combate_atual = None
        self.save()

    def adicionar_personagem(
        self,
        nome: str,
        tipo: str,
        raca: str,
        nivel: int,
        **kwargs: Any,
    ) -> PersonagemRecorrente:
        """Adiciona personagem à campanha."""
        personagem_id = str(uuid.uuid4())[:8]
        agora = datetime.now().isoformat()
        pc = PersonagemRecorrente(
            id=personagem_id,
            nome=nome,
            tipo=tipo,
            raca=raca,
            nivel=nivel,
            primeira_aparicao=agora,
            ultima_aparicao=agora,
            aparicoes=1,
            notas=kwargs.get("notas", ""),
        )
        self.personagens[nome] = pc
        if tipo == "pc":
            self.party_xp[nome] = kwargs.get("xp_inicial", 0)

        self._registrar_evento(
            tipo="social",
            descricao=f"{nome} ({raca} {tipo}) entra na campanha",
            envolvidos=[nome],
            importancia=3 if tipo == "pc" else 2,
        )
        self.save()
        return pc

    def registrar_evento(
        self,
        descricao: str,
        tipo: str = "exploracao",
        envolvidos: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Registra evento na campanha."""
        return self._registrar_evento(
            tipo, descricao, envolvidos or [], **kwargs
        )

    def _registrar_evento(
        self,
        tipo: str,
        descricao: str,
        envolvidos: List[str],
        **kwargs: Any,
    ) -> str:
        """Registro interno de evento."""
        evento_id = str(uuid.uuid4())[:8]
        evento = EventoCampanha(
            id=evento_id,
            timestamp=datetime.now().isoformat(),
            tipo=tipo,
            descricao=descricao,
            envolvidos=envolvidos,
            consequencias=kwargs.get("consequencias", []),
            xp_ganho=kwargs.get("xp_ganho", 0),
            tesouro=kwargs.get("tesouro", []),
            local=kwargs.get("local", ""),
            importancia=kwargs.get("importancia", 1),
        )
        self.eventos[evento_id] = evento
        self._index_por_tipo.setdefault(tipo, set()).add(evento_id)

        for nome in envolvidos:
            if nome in self.personagens:
                p = self.personagens[nome]
                p.ultima_aparicao = evento.timestamp
                p.aparicoes += 1

        if self.sessao_atual:
            self.sessao_atual.eventos.append(evento_id)

        if evento.xp_ganho > 0 and envolvidos:
            pcs_envolvidos = [e for e in envolvidos if e in self.party_xp]
            if pcs_envolvidos:
                xp_por_pc = evento.xp_ganho // len(pcs_envolvidos)
                for nome in pcs_envolvidos:
                    self.party_xp[nome] = self.party_xp.get(nome, 0) + xp_por_pc

        self.save()
        return evento_id

    def iniciar_combate(
        self,
        inimigos: List[Dict[str, Any]],
        local: str = "desconhecido",
    ) -> Dict[str, Any]:
        """Inicia combate persistente."""
        if not self.sessao_atual:
            raise ValueError(
                "Nenhuma sessao ativa. Inicie uma sessao primeiro."
            )

        self.combate_atual = {
            "id": str(uuid.uuid4())[:8],
            "inicio": datetime.now().isoformat(),
            "rodada": 1,
            "local": local,
            "inimigos": inimigos,
            "pcs": {
                nome: {"pv_atual": 999, "pm_atual": 0}
                for nome in self.party_xp.keys()
            },
            "iniciativa": [],
            "log": [],
            "status": "ativo",
        }

        for nome in self.party_xp.keys():
            if nome in self.personagens:
                self.combate_atual["iniciativa"].append({
                    "nome": nome,
                    "iniciativa": 6,
                    "tipo": "pc",
                })
        for ini in inimigos:
            self.combate_atual["iniciativa"].append({
                "nome": ini.get("nome", "Inimigo"),
                "iniciativa": ini.get("habilidade", 3) + 3,
                "tipo": "npc",
            })
        self.combate_atual["iniciativa"].sort(
            key=lambda x: x["iniciativa"],
            reverse=True,
        )

        self._registrar_evento(
            tipo="combate",
            descricao=f"Combate iniciado contra {len(inimigos)} inimigos em {local}",
            envolvidos=list(self.party_xp.keys()),
            local=local,
            importancia=3,
        )
        self.save()
        return self.combate_atual

    def executar_acao_combate(
        self,
        personagem: str,
        acao: str,
        alvo: Optional[str] = None,
        resultado: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registra acao no combate."""
        if not self.combate_atual:
            return {"erro": "Nenhum combate ativo"}

        entrada_log = {
            "rodada": self.combate_atual["rodada"],
            "timestamp": datetime.now().isoformat(),
            "personagem": personagem,
            "acao": acao,
            "alvo": alvo,
            "resultado": resultado or {},
        }
        self.combate_atual["log"].append(entrada_log)

        acoes_na_rodada = [
            a
            for a in self.combate_atual["log"]
            if a["rodada"] == self.combate_atual["rodada"]
        ]
        if len(acoes_na_rodada) >= len(self.combate_atual["iniciativa"]):
            self.combate_atual["rodada"] += 1

        self.save()
        return entrada_log

    def finalizar_combate(
        self,
        vitoria: bool,
        resumo: str = "",
    ) -> Optional[EventoCampanha]:
        """Finaliza combate e registra resultado."""
        if not self.combate_atual:
            return None

        xp_total = sum(
            i.get("xp", 0) for i in self.combate_atual.get("inimigos", [])
        )
        evento_id = self._registrar_evento(
            tipo="combate",
            descricao=(
                f"Combate finalizado - "
                f"{'Vitoria' if vitoria else 'Derrota/Fuga'}. {resumo}"
            ),
            envolvidos=list(self.party_xp.keys()),
            xp_ganho=xp_total if vitoria else xp_total // 2,
            local=self.combate_atual.get("local", ""),
            importancia=4,
        )

        if self.sessao_atual:
            self.sessao_atual.encontros.append(self.combate_atual["id"])

        combate_id = self.combate_atual["id"]
        self.combate_atual = None
        self.save()

        return self.eventos.get(evento_id)

    def lembrar(self, query: str, limite: int = 5) -> List[Dict[str, Any]]:
        """Consulta memoria da campanha."""
        query_lower = query.lower()
        resultados: List[Dict[str, Any]] = []

        for evento in self.eventos.values():
            score = 0
            if query_lower in evento.descricao.lower():
                score += 3
            if any(query_lower in e.lower() for e in evento.envolvidos):
                score += 2
            if query_lower in (evento.local or "").lower():
                score += 1
            if score > 0:
                resultados.append({
                    "tipo": "evento",
                    "score": score,
                    "data": evento.timestamp[:10],
                    "descricao": evento.descricao,
                    "importancia": evento.importancia,
                })

        for pc in self.personagens.values():
            if query_lower in pc.nome.lower():
                resultados.append({
                    "tipo": "personagem",
                    "score": 5,
                    "nome": pc.nome,
                    "tipo_personagem": pc.tipo,
                    "aparicoes": pc.aparicoes,
                    "destino": pc.destino_atual,
                })

        for thread in self.threads.values():
            if (
                query_lower in thread.titulo.lower()
                or query_lower in thread.descricao.lower()
            ):
                resultados.append({
                    "tipo": "thread",
                    "score": 4,
                    "titulo": thread.titulo,
                    "status": thread.status,
                })

        resultados.sort(key=lambda x: x["score"], reverse=True)
        return resultados[:limite]

    def gerar_resumo(self, sessoes_atras: int = 1) -> str:
        """Gera resumo das ultimas N sessoes."""
        sessoes_ordenadas = sorted(
            self.sessoes.values(),
            key=lambda s: s.numero,
            reverse=True,
        )[:sessoes_atras]

        eventos_recentes: List[EventoCampanha] = []
        for sessao in sessoes_ordenadas:
            for evento_id in sessao.eventos:
                if evento_id in self.eventos:
                    eventos_recentes.append(self.eventos[evento_id])

        importantes = [e for e in eventos_recentes if e.importancia >= 3]
        if not importantes:
            return "Nenhum evento importante registrado recentemente."

        linhas = [f"RESUMO DAS ULTIMAS {sessoes_atras} SESSOES\n"]
        for evt in sorted(importantes, key=lambda e: e.timestamp):
            linhas.append(f"[{evt.timestamp[:10]}] {evt.descricao}")
            if evt.consequencias:
                linhas.append(
                    f"  -> Consequencias: {', '.join(evt.consequencias)}"
                )
        return "\n".join(linhas)

    def sugerir_callback(self) -> Optional[str]:
        """Sugere trazer de volta elemento antigo da campanha."""
        agora = datetime.now()
        candidatos: List[tuple] = []

        for pc in self.personagens.values():
            if pc.aparicoes > 0 and pc.destino_atual == "vivo":
                try:
                    ultima = datetime.fromisoformat(pc.ultima_aparicao)
                except (ValueError, TypeError):
                    continue
                dias_sem_ver = (agora - ultima).days
                if dias_sem_ver > 14:
                    candidatos.append((pc, dias_sem_ver))

        if candidatos:
            candidatos.sort(key=lambda x: x[1], reverse=True)
            pc, dias = candidatos[0]
            rel_ref = (
                random.choice(list(pc.relacoes.keys()))
                if pc.relacoes
                else "seu passado"
            )
            notas_preview = (pc.notas or "")[:50]
            return (
                f"SUGESTAO: {pc.nome} ({pc.raca}) nao aparece ha {dias} dias. "
                f"Ultima aparicao: {notas_preview or 'Sem notas'}. "
                f"Que tal traze-lo de volta com um gancho relacionado a {rel_ref}?"
            )

        abandonadas = [
            t for t in self.threads.values() if t.status == "pausado"
        ]
        if abandonadas:
            thread = random.choice(abandonadas)
            env = ", ".join(thread.envolvidos[:3])
            return (
                f"Thread abandonada: '{thread.titulo}'. "
                f"Envolvidos: {env}. "
                f"Que tal reativar com: {thread.proximo_gancho or 'novo gancho'}?"
            )
        return None

    def verificar_progressao(self) -> Dict[str, Any]:
        """Verifica se jogadores devem subir de nivel."""
        relatorio: Dict[str, Any] = {}
        for nome, xp in self.party_xp.items():
            nivel_atual = self._calcular_nivel(xp)
            xp_proximo = self._xp_para_nivel(nivel_atual + 1)
            xp_faltante = xp_proximo - xp
            relatorio[nome] = {
                "nivel_atual": nivel_atual,
                "xp_atual": xp,
                "xp_para_proximo": xp_proximo,
                "xp_faltante": xp_faltante,
                "progresso": f"{(xp / xp_proximo * 100):.1f}%" if xp_proximo else "0%",
                "pronto_para_subir": xp_faltante <= 0,
            }
        return relatorio

    def _calcular_duracao_combate(self) -> int:
        """Calcula duracao do combate em minutos."""
        if not self.combate_atual:
            return 0
        try:
            inicio = datetime.fromisoformat(self.combate_atual["inicio"])
            return int((datetime.now() - inicio).total_seconds() // 60)
        except (ValueError, KeyError):
            return 0

    def _calcular_nivel(self, xp: int) -> int:
        """Calcula nivel baseado no XP."""
        niveis = [0, 1000, 3000, 6000, 10000, 15000, 21000, 28000, 36000, 45000]
        nivel = 1
        for i, xp_nivel in enumerate(niveis[1:], 2):
            if xp >= xp_nivel:
                nivel = i
        return min(nivel, 10)

    def _xp_para_nivel(self, nivel: int) -> int:
        """Retorna XP necessario para nivel."""
        niveis = [0, 1000, 3000, 6000, 10000, 15000, 21000, 28000, 36000, 45000]
        return niveis[min(nivel, 10)]

    def _gerar_resumo_sessao(self) -> str:
        """Gera resumo automatico da sessao."""
        if not self.sessao_atual:
            return ""
        tipos: Dict[str, int] = {}
        for eid in self.sessao_atual.eventos:
            if eid in self.eventos:
                t = self.eventos[eid].tipo
                tipos[t] = tipos.get(t, 0) + 1
        partes = [f"Sessao com {len(self.sessao_atual.eventos)} eventos:"]
        for tipo, qtd in sorted(tipos.items(), key=lambda x: -x[1]):
            partes.append(f"{qtd} {tipo}(s)")
        return ", ".join(partes)


def criar_ou_carregar_campanha(
    campaign_id: Optional[str] = None,
    nome: str = "Nova Aventura",
) -> CampaignMemory:
    """Cria nova campanha ou carrega existente."""
    if campaign_id:
        path = Path("data/campaigns") / f"campaign_{campaign_id}.json"
        if path.exists():
            return CampaignMemory(campaign_id=campaign_id)
    return CampaignMemory(nome=nome)


def demo_nivel6() -> None:
    """Demonstra funcionalidades do Nivel 6."""
    print("\n" + "=" * 80)
    print("NIVEL 6: SESSAO PERSISTENTE E MEMORIA DE CAMPANHA")
    print("=" * 80)

    campanha = CampaignMemory(nome="As Cronicas de Aldor")
    print(f"\n[OK] Campanha criada: {campanha.nome}")
    print(f"     ID: {campanha.campaign_id}")

    sessao = campanha.iniciar_sessao(1)
    print(f"\n[OK] Sessao {sessao.numero} iniciada")

    campanha.adicionar_personagem(
        "Thorin", "pc", "Anao", 2,
        xp_inicial=0, notas="Guerreiro buscando redencao",
    )
    campanha.adicionar_personagem(
        "Lyra", "pc", "Elfa", 2,
        xp_inicial=0, notas="Maga renegada",
    )
    print("\n[OK] Personagens adicionados: Thorin (Anao), Lyra (Elfa)")

    campanha.registrar_evento(
        "Party chega a vila de Millbrook",
        tipo="exploracao",
        envolvidos=["Thorin", "Lyra"],
        local="Millbrook",
        importancia=2,
    )
    campanha.registrar_evento(
        "Thorin insulta o chefe da guarda",
        tipo="social",
        envolvidos=["Thorin"],
        consequencias=["Guarda hostil ao party"],
        importancia=3,
    )
    print("\n[OK] Eventos registrados: chegada em Millbrook, conflito social")

    inimigos = [
        {"nome": "Goblin", "habilidade": 4, "pv": 8, "xp": 90},
        {"nome": "Goblin", "habilidade": 4, "pv": 8, "xp": 90},
    ]
    combate = campanha.iniciar_combate(inimigos, "Floresta de Millbrook")
    print(f"\n[OK] Combate iniciado: {len(inimigos)} Goblins")
    print(f"     Iniciativa: {[i['nome'] for i in combate['iniciativa']]}")

    campanha.executar_acao_combate(
        "Thorin", "atacar", "Goblin 1",
        {"resultado": "acerto", "dano": 6},
    )
    campanha.executar_acao_combate("Goblin 1", "atacar", "Thorin", {"resultado": "erro"})
    campanha.executar_acao_combate(
        "Lyra", "magia", "Goblin 2",
        {"resultado": "acerto", "dano": 8},
    )
    print("     Acoes registradas: Thorin acerta, Goblin erra, Lyra usa magia")

    campanha.finalizar_combate(True, "Goblins derrotados, um fugiu")
    print("     Combate finalizado: Vitoria, 180 XP ganho")

    campanha.finalizar_sessao("Party derrotou goblins, guarda continua hostil")
    print("\n[OK] Sessao 1 finalizada e salva")

    print("\n" + "=" * 80)
    print("CONSULTANDO MEMORIA")
    print("=" * 80)

    print("\n[BUSCA] 'Thorin':")
    for r in campanha.lembrar("Thorin", 3):
        print(f"   [{r['tipo']}] {r.get('descricao', r.get('nome', '???'))}")

    print("\n[BUSCA] 'combate':")
    for r in campanha.lembrar("combate", 3):
        if r["tipo"] == "evento":
            print(f"   [{r['data']}] {r['descricao'][:60]}...")

    print("\n[RESUMO]")
    print(campanha.gerar_resumo(1))

    sugestao = campanha.sugerir_callback()
    print("\n[SUGESTAO CALLBACK]")
    print(sugestao or "Nenhuma sugestao no momento (campanha nova)")

    print("\n[PROGRESSAO]")
    for nome, dados in campanha.verificar_progressao().items():
        print(f"   {nome}: Nivel {dados['nivel_atual']} ({dados['progresso']} para proximo)")

    print("\n" + "=" * 80)
    print("[OK] NIVEL 6 DEMONSTRADO")
    print("=" * 80)
    print(f"""
A campanha '{campanha.nome}' foi salva em:
   {campanha.save_path}

Proxima sessao, carregue com:
   campanha = CampaignMemory(campaign_id='{campanha.campaign_id}')

O sistema lembrara:
   - Todos os eventos, personagens e combates
   - XP ganho por cada jogador
   - Consequencias de decisoes passadas
   - Sugerir callbacks a elementos antigos
""")


if __name__ == "__main__":
    demo_nivel6()
