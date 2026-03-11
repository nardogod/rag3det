"""
Gerenciamento de sessão de jogo persistente.
Mantém estado entre interações e fornece ferramentas de mesa para 3D&T.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.rag.hybrid_retriever import HybridRetriever
from src.generation.content_generator import ContentGenerator


@dataclass
class PlayerCharacter:
    """Personagem de jogador na sessão."""

    id: str
    nome: str
    jogador: str
    raca: str
    nivel: int
    stats: Dict[str, int]
    pv_atual: int
    pm_atual: int
    pericias: List[str]
    inventario: List[str]
    notas: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CombatRound:
    """Rodada de combate."""

    numero: int
    iniciativas: List[Dict[str, Any]]  # [{nome, iniciativa, stats...}]
    acoes: List[Dict[str, Any]]  # Registro de ações
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "numero": self.numero,
            "iniciativas": self.iniciativas,
            "acoes": self.acoes,
            "timestamp": self.timestamp,
        }


class CampaignSession:
    """
    Sessão de campanha ativa com persistência em disco.
    """

    def __init__(self, session_id: Optional[str] = None, nome: str = "Aventura") -> None:
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.nome = nome
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

        # Estado
        self.player_characters: List[PlayerCharacter] = []
        self.npcs_ativos: List[Dict[str, Any]] = []
        self.combate_ativo: Optional[CombatRound] = None
        self.historia: List[Dict[str, Any]] = []
        self.notas_mestre: str = ""

        # Ferramentas
        self.retriever = HybridRetriever()
        self.generator = ContentGenerator(self.retriever)

        # Arquivo de persistência
        self.save_path = Path("data/sessions") / f"session_{self.session_id}.json"

    # ------------------------------------------------------------------ #
    # Persistência
    # ------------------------------------------------------------------ #

    def save(self) -> None:
        """Salva estado da sessão em JSON."""
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now().isoformat()

        data = {
            "session_id": self.session_id,
            "nome": self.nome,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "player_characters": [p.to_dict() for p in self.player_characters],
            "npcs_ativos": self.npcs_ativos,
            "combate_ativo": self.combate_ativo.to_dict() if self.combate_ativo else None,
            "historia": self.historia,
            "notas_mestre": self.notas_mestre,
        }

        with self.save_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, session_id: str) -> Optional["CampaignSession"]:
        """Carrega sessão existente a partir do disco."""
        path = Path("data/sessions") / f"session_{session_id}.json"
        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        session = cls(data["session_id"], data["nome"])
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.notas_mestre = data.get("notas_mestre", "")
        session.historia = data.get("historia", [])
        session.npcs_ativos = data.get("npcs_ativos", [])

        for pc_data in data.get("player_characters", []):
            session.player_characters.append(PlayerCharacter(**pc_data))

        if data.get("combate_ativo"):
            c = data["combate_ativo"]
            session.combate_ativo = CombatRound(
                numero=c["numero"],
                iniciativas=c["iniciativas"],
                acoes=c["acoes"],
                timestamp=c["timestamp"],
            )

        return session

    # ------------------------------------------------------------------ #
    # Personagens
    # ------------------------------------------------------------------ #

    def add_player_character(
        self,
        nome: str,
        jogador: str,
        raca: str,
        nivel: int,
        stats: Dict[str, int],
    ) -> PlayerCharacter:
        """Adiciona um personagem de jogador (PC) à sessão."""
        pc = PlayerCharacter(
            id=str(uuid.uuid4())[:8],
            nome=nome,
            jogador=jogador,
            raca=raca,
            nivel=nivel,
            stats=stats,
            pv_atual=stats.get("pv", 10),
            pm_atual=stats.get("pm", 0),
            pericias=[],
            inventario=[],
        )
        self.player_characters.append(pc)
        self._log_event(f"Personagem {nome} ({jogador}) entrou na sessão")
        self.save()
        return pc

    # ------------------------------------------------------------------ #
    # Combate
    # ------------------------------------------------------------------ #

    def iniciar_combate(self, inimigos: List[Dict[str, Any]]) -> str:
        """Inicia um tracker de combate."""
        iniciativas: List[Dict[str, Any]] = []

        for pc in self.player_characters:
            if pc.pv_atual > 0:
                ini = pc.stats.get("habilidade", 0) + self._rolar_d6()
                iniciativas.append(
                    {
                        "tipo": "pc",
                        "id": pc.id,
                        "nome": pc.nome,
                        "iniciativa": ini,
                        "pv_atual": pc.pv_atual,
                        "pm_atual": pc.pm_atual,
                        "stats": pc.stats,
                    }
                )

        for npc in inimigos:
            ini = npc.get("habilidade", 0) + self._rolar_d6()
            iniciativas.append(
                {
                    "tipo": "npc",
                    "nome": npc.get("nome", "Inimigo"),
                    "iniciativa": ini,
                    "pv": npc.get("pv", 10),
                    "stats": {
                        k: v
                        for k, v in npc.items()
                        if k in ["forca", "habilidade", "resistencia", "armadura"]
                    },
                }
            )

        iniciativas.sort(key=lambda x: x["iniciativa"], reverse=True)

        self.combate_ativo = CombatRound(
            numero=1,
            iniciativas=iniciativas,
            acoes=[],
            timestamp=datetime.now().isoformat(),
        )
        self.npcs_ativos = inimigos

        self._log_event(f"Combate iniciado contra {len(inimigos)} inimigos")
        self.save()
        return self._format_combate_status()

    @staticmethod
    def _rolar_d6() -> int:
        import random

        return random.randint(1, 6)

    def _rolar_3d6(self) -> int:
        return sum(self._rolar_d6() for _ in range(3))

    def executar_acao(
        self,
        personagem_nome: str,
        acao: str,
        alvo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executa uma ação no combate (ataque básico / magia simplificada)."""
        if not self.combate_ativo:
            return {"erro": "Nenhum combate ativo"}

        resultado: Dict[str, Any] = {
            "personagem": personagem_nome,
            "acao": acao,
            "rolagem": None,
            "sucesso": None,
            "dano": None,
            "efeito": None,
        }

        acao_lower = acao.lower()

        if "atacar" in acao_lower or "ataque" in acao_lower:
            atacante = self._find_in_combate(personagem_nome)
            if not atacante:
                return {"erro": f"{personagem_nome} não encontrado no combate"}

            roll = self._rolar_3d6()
            hab = atacante.get("stats", {}).get("habilidade", 0)
            resultado["rolagem"] = roll
            resultado["sucesso"] = roll <= hab

            if resultado["sucesso"] and alvo:
                forca = atacante.get("stats", {}).get("forca", 0)
                dano_bonus = forca // 2
                dano_arma = self._rolar_d6() + dano_bonus
                resultado["dano"] = dano_arma
                self._aplicar_dano(alvo, dano_arma)
                resultado["efeito"] = f"{alvo} sofre {dano_arma} de dano!"
            else:
                resultado["efeito"] = "Ataque falhou!"

        elif "magia" in acao_lower or "lançar" in acao_lower or "lancar" in acao_lower:
            resultado["efeito"] = "Magia lançada (verificar custo de PM e efeito nas regras)."

        self.combate_ativo.acoes.append(
            {
                "rodada": self.combate_ativo.numero,
                "personagem": personagem_nome,
                "acao": acao,
                "resultado": resultado,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.save()
        return resultado

    def _find_in_combate(self, nome: str) -> Optional[Dict[str, Any]]:
        if not self.combate_ativo:
            return None
        for ini in self.combate_ativo.iniciativas:
            if ini.get("nome", "").lower() == nome.lower():
                return ini
        return None

    def _aplicar_dano(self, alvo_nome: str, dano: int) -> None:
        for pc in self.player_characters:
            if pc.nome.lower() == alvo_nome.lower():
                pc.pv_atual = max(0, pc.pv_atual - dano)
                return
        for npc in self.npcs_ativos:
            if npc.get("nome", "").lower() == alvo_nome.lower():
                npc["pv"] = max(0, npc.get("pv", 0) - dano)
                return

    def _format_combate_status(self) -> str:
        if not self.combate_ativo:
            return "Sem combate ativo."

        lines: List[str] = []
        lines.append(f"COMBATE - Rodada {self.combate_ativo.numero}")
        lines.append("=" * 50)
        lines.append("Ordem de Iniciativa:")

        for i, ini in enumerate(self.combate_ativo.iniciativas, 1):
            tipo_label = "PC" if ini.get("tipo") == "pc" else "NPC"
            pv_info = ini.get("pv_atual", ini.get("pv", "?"))
            lines.append(
                f"{i}. [{tipo_label}] {ini.get('nome', '?')} (INI: {ini.get('iniciativa')}) - PV: {pv_info}"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Histórico / regras / encontro rápido
    # ------------------------------------------------------------------ #

    def _log_event(self, descricao: str) -> None:
        self.historia.append(
            {"timestamp": datetime.now().isoformat(), "descricao": descricao}
        )

    def consultar_regra(self, pergunta: str) -> str:
        results = self.retriever.query(pergunta, top_k=5)
        if not results:
            return "Nenhuma regra encontrada para esta consulta."

        lines = [f"Regras encontradas para '{pergunta}':", ""]
        for r in results[:3]:
            lines.append(f"[{r.source}] {r.content[:200]}...")
        return "\n".join(lines)

    def gerar_encontro_rapido(self, dificuldade: str = "medio") -> str:
        if not self.player_characters:
            return "Nenhum personagem na sessão."

        party_level = sum(pc.nivel for pc in self.player_characters) // max(
            1, len(self.player_characters)
        )
        encounter = self.generator.generate_encounter(
            party_size=len(self.player_characters),
            party_level=party_level,
            dificuldade=dificuldade,
        )

        for inimigo in encounter.get("inimigos", []):
            for _ in range(inimigo.get("quantidade", 0)):
                data = self.retriever._get_entity_data(inimigo.get("nome", ""))
                if data and data.get("structured_data"):
                    self.npcs_ativos.append(data["structured_data"])

        self.save()

        inimigos_desc = ", ".join(
            f"{e['quantidade']}x {e['nome']}" for e in encounter.get("inimigos", [])
        )
        tesouro_desc = ", ".join(encounter.get("tesouro", [])[:2])

        return (
            f"ENCONTRO GERADO ({dificuldade.upper()})\n"
            f"{encounter.get('descricao', '')}\n\n"
            f"Inimigos: {inimigos_desc}\n"
            f"XP Total: {encounter.get('xp_total', 0)}\n"
            f"Tesouro: {tesouro_desc}\n\n"
            "Use /combate iniciar para começar o combate!"
        )


class SessionCLI:
    """Interface de linha de comando para sessão."""

    def __init__(self) -> None:
        self.session: Optional[CampaignSession] = None

    def run(self) -> None:
        print("=" * 60)
        print("3D&T ASSISTENTE DE SESSÃO")
        print("=" * 60)

        session_id = input("ID da sessão (deixe em branco para nova): ").strip()
        if session_id:
            self.session = CampaignSession.load(session_id)
            if self.session:
                print(f"Sessão '{self.session.nome}' carregada.")
            else:
                print("Sessão não encontrada, criando nova...")
                self.session = CampaignSession(nome=input("Nome da aventura: "))
        else:
            self.session = CampaignSession(nome=input("Nome da aventura: "))

        print(f"\nSessão ID: {self.session.session_id}")
        print("Comandos: /ajuda, /personagem, /combate, /consultar, /encontro, /sair")

        while True:
            try:
                comando = input("\n> ").strip()
                if comando == "/sair":
                    self.session.save()
                    print("Sessão salva. Até logo!")
                    break
                if comando == "/ajuda":
                    self._show_help()
                elif comando.startswith("/personagem"):
                    self._handle_personagem(comando)
                elif comando.startswith("/combate"):
                    self._handle_combate(comando)
                elif comando.startswith("/consultar"):
                    query = comando.replace("/consultar", "").strip()
                    print(self.session.consultar_regra(query))
                elif comando.startswith("/encontro"):
                    dif = comando.replace("/encontro", "").strip() or "medio"
                    print(self.session.gerar_encontro_rapido(dif))
                else:
                    print(self._handle_freeform(comando))
            except Exception as e:
                print(f"Erro: {e}")

    @staticmethod
    def _show_help() -> None:
        print(
            """
Comandos disponíveis:
  /personagem add <nome> <jogador> <raca> <nivel>    - Adicionar PC
  /personagem list                                   - Listar PCs
  /combate iniciar                                   - Iniciar combate
  /combate status                                    - Ver ordem de iniciativa
  /combate acao <nome> <acao> [alvo]                - Executar ação
  /consultar <pergunta>                              - Consultar regras
  /encontro [facil/medio/dificil/epico]             - Gerar encontro
  /sair                                              - Salvar e sair
"""
        )

    def _handle_personagem(self, cmd: str) -> None:
        parts = cmd.split()
        if len(parts) >= 2 and parts[1] == "add" and len(parts) >= 6:
            nome, jogador, raca, nivel_str = parts[2], parts[3], parts[4], parts[5]
            try:
                nivel = int(nivel_str)
            except ValueError:
                print("Nível inválido.")
                return
            stats = {
                "forca": 3 + nivel,
                "habilidade": 3 + nivel,
                "resistencia": 3 + nivel,
                "armadura": 1,
                "pv": 20 + (nivel * 5),
                "pm": nivel * 3,
            }
            pc = self.session.add_player_character(nome, jogador, raca, nivel, stats)
            print(f"{pc.nome} ({pc.jogador}) adicionado.")
        elif len(parts) >= 2 and parts[1] == "list":
            if not self.session.player_characters:
                print("Nenhum personagem cadastrado.")
                return
            for pc in self.session.player_characters:
                print(
                    f"{pc.nome} (N{pc.nivel} {pc.raca}) - "
                    f"PV:{pc.pv_atual}/{pc.stats['pv']} PM:{pc.pm_atual}/{pc.stats['pm']}"
                )
        else:
            print("Uso: /personagem add <nome> <jogador> <raca> <nivel>  ou  /personagem list")

    def _handle_combate(self, cmd: str) -> None:
        parts = cmd.split()
        if len(parts) >= 2 and parts[1] == "iniciar":
            if not self.session.npcs_ativos:
                print("Nenhum inimigo ativo. Use /encontro primeiro.")
                return
            status = self.session.iniciar_combate(self.session.npcs_ativos)
            print(status)
        elif len(parts) >= 2 and parts[1] == "status":
            print(self.session._format_combate_status())
        elif len(parts) >= 4 and parts[1] == "acao":
            nome = parts[2]
            acao = parts[3]
            alvo = parts[4] if len(parts) > 4 else None
            result = self.session.executar_acao(nome, acao, alvo)
            print(f"Rolagem: {result.get('rolagem')} vs Habilidade")
            print("Sucesso!" if result.get("sucesso") else "Falha!")
            if result.get("dano") is not None:
                print(f"Dano: {result['dano']}")
            if result.get("efeito"):
                print(f"Efeito: {result['efeito']}")
        else:
            print("Uso: /combate iniciar | /combate status | /combate acao <nome> <acao> [alvo]")

    @staticmethod
    def _handle_freeform(text: str) -> str:
        return (
            "[Assistente] Entendi: "
            f"'{text}'. Use /consultar para regras específicas ou /ajuda para comandos."
        )


def main() -> None:
    cli = SessionCLI()
    cli.run()


if __name__ == "__main__":
    main()

