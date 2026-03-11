"""
Geração de conteúdo novo DENTRO das regras do 3D&T.
Não inventa fora do canon, mas combina elementos existentes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.rag.hybrid_retriever import HybridRetriever


@dataclass
class GeneratedNPC:
    """NPC gerado seguindo regras do 3D&T."""

    nome: str
    raca: str
    nivel: int
    stats: Dict[str, int]  # F, H, R, A, PV, PM
    pericias: List[str]
    equipamento: List[str]
    magias: Optional[List[str]]
    background: str
    motivacao: str
    xp_value: int

    def to_dict(self) -> Dict[str, Any]:
        base = (
            self.stats.get("forca", 0)
            + self.stats.get("habilidade", 0)
            + self.stats.get("resistencia", 0)
        )
        return {
            "nome": self.nome,
            "raca": self.raca,
            "nivel": self.nivel,
            "stats": self.stats,
            "pericias": self.pericias,
            "equipamento": self.equipamento,
            "magias": self.magias,
            "background": self.background,
            "motivacao": self.motivacao,
            "xp_value": self.xp_value,
            "poder_combate": base,
        }


class ContentGenerator:
    """
    Gera conteúdo novo combinando elementos do corpus.
    Respeita regras do sistema 3D&T.
    """

    BACKGROUND_TEMPLATES = {
        "guerreiro": [
            "Ex-soldado de {origem} que perdeu tudo na guerra.",
            "Mercenário que luta por {motivacao} e glória.",
            "Guarda de {origem} demitido por corrupção.",
        ],
        "mago": [
            "Aprendiz de {origem} expulso por experimentos perigosos.",
            "Ermitão que vive em {local} estudando magia.",
            "Acadêmico de {origem} em busca de conhecimento proibido.",
        ],
        "ladino": [
            "Ladrão de {origem} tentando se redimir.",
            "Espião de {organizacao} em missão secreta.",
            "Contrabandista de {origem} procurado pela lei.",
        ],
    }

    RACAS_VALIDAS = ["Humano", "Elfo", "Anão", "Goblin", "Orc", "Meio-Elfo"]

    def __init__(self, retriever: Optional[HybridRetriever] = None) -> None:
        self.retriever = retriever or HybridRetriever()
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        """Carrega dados de referência do corpus (entidades, magias, equipamentos)."""
        self.reference_monstros = getattr(
            self.retriever, "_entity_cache", {}
        )

        magias = self.retriever.query("magias", top_k=50)
        self.magias_conhecidas = [
            m.entity_name
            for m in magias
            if m.source == "table_magias" and m.entity_name
        ]

        equip = self.retriever.query("armas equipamentos", top_k=50)
        self.equipamentos_conhecidos = [
            e.entity_name
            for e in equip
            if e.source == "table_equipamentos" and e.entity_name
        ]

    def generate_npc(
        self,
        nivel: int = 1,
        arquetipo: Optional[str] = None,
        raca: Optional[str] = None,
        forca_total: Optional[int] = None,
    ) -> GeneratedNPC:
        """
        Gera um NPC balanceado para o nível especificado.
        """
        if not raca:
            raca = random.choice(self.RACAS_VALIDAS)
        if not arquetipo:
            arquetipo = random.choice(["guerreiro", "mago", "ladino", "generalista"])

        pontos_totais = 10 + (nivel * 2)
        distribuicao = {
            "guerreiro": {"forca": 0.4, "habilidade": 0.2, "resistencia": 0.3, "armadura": 0.1},
            "mago": {"forca": 0.1, "habilidade": 0.3, "resistencia": 0.2, "armadura": 0.0, "pm_bonus": True},
            "ladino": {"forca": 0.2, "habilidade": 0.4, "resistencia": 0.2, "armadura": 0.2},
            "generalista": {"forca": 0.25, "habilidade": 0.25, "resistencia": 0.25, "armadura": 0.25},
        }.get(arquetipo, {"forca": 0.25, "habilidade": 0.25, "resistencia": 0.25, "armadura": 0.25})

        stats: Dict[str, int] = {
            "forca": max(1, int(pontos_totais * distribuicao.get("forca", 0.25))),
            "habilidade": max(1, int(pontos_totais * distribuicao.get("habilidade", 0.25))),
            "resistencia": max(1, int(pontos_totais * distribuicao.get("resistencia", 0.25))),
            "armadura": max(0, int(pontos_totais * distribuicao.get("armadura", 0.1))),
        }
        stats["pv"] = stats["resistencia"] * random.randint(2, 5)
        stats["pm"] = stats["habilidade"] * (
            random.randint(2, 4) if distribuicao.get("pm_bonus") else random.randint(1, 2)
        )

        if forca_total:
            total = sum(stats.values())
            if total > 0:
                fator = forca_total / total
                stats = {k: max(1, int(v * fator)) for k, v in stats.items()}

        pericias = self._select_pericias(arquetipo, nivel)
        equipamento = self._select_equipamento(arquetipo, nivel)
        magias = None
        if arquetipo == "mago" and nivel >= 1:
            magias = self._select_magias(nivel)

        background = self._generate_background(arquetipo)
        motivacao = self._generate_motivacao()
        xp_value = (
            stats["forca"] + stats["habilidade"] + stats["resistencia"] + (stats["pv"] // 10)
        ) * 10
        nome = self._generate_name(raca, arquetipo)

        return GeneratedNPC(
            nome=nome,
            raca=raca,
            nivel=nivel,
            stats=stats,
            pericias=pericias,
            equipamento=equipamento,
            magias=magias,
            background=background,
            motivacao=motivacao,
            xp_value=xp_value,
        )

    def _select_pericias(self, arquetipo: str, nivel: int) -> List[str]:
        pericias_por_arquetipo = {
            "guerreiro": ["Luta", "Atletismo", "Intimidação", "Resistência", "Armas"],
            "mago": ["Magia", "Conhecimento Arcano", "Alquimia", "Percepção", "Linguagens"],
            "ladino": ["Furtividade", "Roubo", "Enganação", "Acrobacia", "Percepção", "Lockpicking"],
            "generalista": ["Sobrevivência", "Cura", "Negociação", "Percepção", "Atletismo"],
        }
        pool = pericias_por_arquetipo.get(arquetipo, pericias_por_arquetipo["generalista"])
        num_pericias = min(nivel + 1, len(pool))
        return random.sample(pool, num_pericias)

    def _select_equipamento(self, arquetipo: str, nivel: int) -> List[str]:
        pe_budget = nivel * 20 + 10
        recs = self.retriever.recommend_for_build(
            pe_budget=pe_budget,
            tipo="arma" if arquetipo == "guerreiro" else None,
        )
        equipamento: List[str] = []
        pe_gasto = 0

        armas = [r for r in recs if r.get("tipo") and "arma" in str(r["tipo"]).lower()]
        if armas and arquetipo in ("guerreiro", "ladino"):
            arma = armas[0]
            pe_arma = arma.get("pe") or 0
            if pe_gasto + pe_arma <= pe_budget:
                equipamento.append(f"{arma.get('nome', 'Arma')} (Dano: {arma.get('dano', '-')})")
                pe_gasto += pe_arma

        armaduras = self.retriever.recommend_for_build(
            pe_budget=pe_budget - pe_gasto,
            tipo="armadura",
        )
        if armaduras:
            arm = armaduras[0]
            pe_arm = arm.get("pe") or 0
            if pe_gasto + pe_arm <= pe_budget:
                equipamento.append(f"{arm.get('nome', 'Armadura')} (Def: {arm.get('defesa', '-')})")
                pe_gasto += pe_arm

        equipamento.extend(["Mochila", "Cantil", "Ração (3 dias)", "Tocha (2)"])
        return equipamento

    def _select_magias(self, nivel: int) -> List[str]:
        circulo_max = min(5, (nivel // 2) + 1)
        magias_disponiveis: List[str] = []
        for magia in (self.magias_conhecidas or [])[:20]:
            data = self.retriever._get_entity_data(magia)
            if data:
                sd = data.get("structured_data") or {}
                circulo = sd.get("circulo", 1)
                if circulo is not None and circulo <= circulo_max:
                    magias_disponiveis.append(magia)
        num_magias = min(nivel + 2, len(magias_disponiveis))
        if not magias_disponiveis:
            return ["Bola de Fogo"]
        return random.sample(magias_disponiveis, num_magias)

    def _generate_background(self, arquetipo: str) -> str:
        templates = self.BACKGROUND_TEMPLATES.get(
            arquetipo, ["Aventureiro de origem desconhecida."]
        )
        origens = ["Aldor", "Khalifor", "Terras Selvagens", "Porto Livre", "Montanhas de Gelo"]
        motivacoes = ["ouro", "vingança", "justiça", "poder", "proteção dos inocentes"]
        locais = ["floresta proibida", "ruínas antigas", "cavernas sombrias", "torre isolada"]
        organizacoes = ["Guilda dos Ladrões", "Ordem dos Magos", "Exército Imperial", "Culto Sombrio"]
        template = random.choice(templates)
        return template.format(
            origem=random.choice(origens),
            motivacao=random.choice(motivacoes),
            local=random.choice(locais),
            organizacao=random.choice(organizacoes),
        )

    def _generate_motivacao(self) -> str:
        motivacoes = [
            "Proteger um segredo perigoso",
            "Vingar a morte de um ente querido",
            "Acumular riqueza para salvar a família",
            "Provar seu valor aos antigos companheiros",
            "Encontrar um artefato lendário",
            "Escapar de um passado criminoso",
            "Proteger um refugiado inocente",
            "Destruir uma organização maligna",
        ]
        return random.choice(motivacoes)

    def _generate_name(self, raca: str, arquetipo: str) -> str:
        prefixos: Dict[str, List[str]] = {
            "Humano": ["Al", "Be", "Cor", "Dun", "El", "Fer"],
            "Elfo": ["Ael", "Syl", "Thal", "Mith", "Eld", "Lor"],
            "Anão": ["Thor", "Dur", "Bal", "Gim", "Kaz", "Mor"],
            "Goblin": ["Grk", "Zug", "Mak", "Ruk", "Tik", "Vok"],
            "Orc": ["Gor", "Thrak", "Mog", "Kur", "Zug", "Ruk"],
            "Meio-Elfo": ["Ad", "Sil", "Cor", "Ael", "Dun", "Lor"],
        }
        sufixos = {
            "guerreiro": ["gar", "rik", "thor", "son"],
            "mago": ["ius", "ar", "ian", "or", "is"],
            "ladino": ["ek", "is", "ar", "o", "in"],
            "generalista": ["an", "or", "is", "ek", "ar"],
        }
        pre = random.choice(prefixos.get(raca, prefixos["Humano"]))
        suf = random.choice(sufixos.get(arquetipo, sufixos["generalista"]))
        return f"{pre}{suf}"

    def generate_encounter(
        self,
        party_size: int = 4,
        party_level: int = 1,
        dificuldade: str = "medio",
        ambiente: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gera um encontro balanceado para a party.
        """
        xp_multiplicadores = {"facil": 0.5, "medio": 1.0, "dificil": 1.5, "epico": 2.5}
        xp_base_por_jogador = party_level * 100
        xp_total_alvo = (
            xp_base_por_jogador * party_size * xp_multiplicadores.get(dificuldade, 1.0)
        )

        monstros_query = f"monstros nível {party_level}"
        monstros_disponiveis = self.retriever.query(monstros_query, top_k=20)
        monstros_validos: List[Dict[str, Any]] = []

        for m in monstros_disponiveis:
            data = (m.metadata or {}).get("structured_data") or {}
            if not data:
                continue
            poder = (
                data.get("forca", 0)
                + data.get("habilidade", 0)
                + data.get("resistencia", 0)
            )
            if abs(poder - (party_level * 3)) <= party_level * 2:
                monstros_validos.append({
                    "nome": data.get("nome", "Criatura"),
                    "poder": poder,
                    "xp": data.get("xp_sugerido", poder * 10),
                })

        if not monstros_validos:
            monstros_validos = [
                {"nome": "Goblin", "poder": 9, "xp": 90},
                {"nome": "Orc", "poder": 12, "xp": 120},
            ]

        encontro: Dict[str, Any] = {
            "descricao": self._generate_encounter_description(ambiente, dificuldade),
            "inimigos": [],
            "xp_total": 0,
            "tesouro": [],
            "taticas": "",
        }
        xp_atual = 0
        tentativas = 0

        while xp_atual < xp_total_alvo * 0.8 and tentativas < 50:
            monstro = random.choice(monstros_validos)
            if monstro["poder"] < party_level * 2:
                qtd = random.randint(2, 4)
            elif monstro["poder"] < party_level * 3:
                qtd = random.randint(1, 2)
            else:
                qtd = 1
            xp_ganho = monstro["xp"] * qtd
            if xp_atual + xp_ganho <= xp_total_alvo * 1.2:
                encontro["inimigos"].append({
                    "nome": monstro["nome"],
                    "quantidade": qtd,
                    "xp_por_criatura": monstro["xp"],
                    "xp_total": xp_ganho,
                })
                xp_atual += xp_ganho
            tentativas += 1

        encontro["xp_total"] = xp_atual
        pe_tesouro = int(xp_atual * random.uniform(0.5, 1.5))
        encontro["tesouro"] = self._generate_treasure(pe_tesouro, party_level)
        encontro["taticas"] = self._generate_tactics(encontro["inimigos"], ambiente)
        return encontro

    def _generate_encounter_description(self, ambiente: Optional[str], dificuldade: str) -> str:
        ambientes = {
            "floresta": "entre árvores antigas e sombrias",
            "dungeon": "em um corredor escuro com tochas piscantes",
            "cidade": "em um beco sujo da periferia",
            "montanha": "em um desfiladeiro estreito com vento cortante",
            "caverna": "em uma caverna úmida com estalactites",
        }
        descricoes_dificuldade = {
            "facil": "Um grupo de oponentes desorganizados",
            "medio": "Uma ameaça calculada que testará suas habilidades",
            "dificil": "Um desafio perigoso que exigirá estratégia",
            "epico": "Uma batalha lendária contra forças esmagadoras",
        }
        loc = ambientes.get(ambiente or "", "em terreno hostil")
        return f"{descricoes_dificuldade.get(dificuldade, 'Encontro')} {loc}."

    def _generate_treasure(self, pe_total: int, nivel_party: int) -> List[str]:
        tesouro: List[str] = []
        moedas = pe_total // 2
        if moedas > 0:
            tesouro.append(f"{moedas} PE em moedas e objetos de valor")
        if nivel_party >= 3 and random.random() < 0.3:
            tesouro.append("Poção de Cura (2d8 PV)")
        if nivel_party >= 5 and random.random() < 0.2:
            tesouro.append("Pergaminho de Magia (1º círculo)")
        if random.random() < 0.5:
            tesouro.append("Equipamento padrão dos inimigos (valor 20% do normal)")
        return tesouro

    def _generate_tactics(
        self, inimigos: List[Dict[str, Any]], ambiente: Optional[str]
    ) -> str:
        if not inimigos:
            return "Ataque frontal desorganizado."
        nomes = [f"{e['quantidade']}x {e['nome']}" for e in inimigos]
        composicao = ", ".join(nomes)
        tacticas_base = [
            "Os inimigos tentam cercar os personagens usando o terreno.",
            "Ataque surpresa! Os inimigos estavam emboscados.",
            "Os inimigos formam uma linha defensiva e protegem um líder.",
            "Ataque em waves: metade ataca, metade espera reforços.",
            "Os inimigos tentam fugir se perderem metade das forças.",
        ]
        return f"Composição: {composicao}. Tática: {random.choice(tacticas_base)}"


def demo_generation() -> None:
    """Demonstra geração de conteúdo."""
    print("=" * 70)
    print("GERAÇÃO DE CONTEÚDO 3D&T")
    print("=" * 70)

    generator = ContentGenerator()

    print("\n[NPCs GERADOS]\n")
    for i, (nivel, arquetipo) in enumerate(
        [(1, "guerreiro"), (3, "mago"), (5, "ladino")], 1
    ):
        npc = generator.generate_npc(nivel=nivel, arquetipo=arquetipo)
        print(f"{i}. {npc.nome} ({npc.raca}) - Nível {npc.nivel} {arquetipo.upper()}")
        print(
            f"   F:{npc.stats['forca']} H:{npc.stats['habilidade']} R:{npc.stats['resistencia']} "
            f"A:{npc.stats['armadura']} PV:{npc.stats['pv']} PM:{npc.stats['pm']}"
        )
        print(f"   Perícias: {', '.join(npc.pericias[:3])}")
        print(f"   Equip: {', '.join(npc.equipamento[:2])}")
        if npc.magias:
            print(f"   Magias: {', '.join(npc.magias[:3])}")
        print(f"   Background: {npc.background[:80]}...")
        print(f"   XP se derrotado: {npc.xp_value}")
        print()

    print("\n[ENCONTROS GERADOS]\n")
    for dificuldade in ["facil", "medio", "dificil"]:
        encounter = generator.generate_encounter(
            party_size=4,
            party_level=3,
            dificuldade=dificuldade,
            ambiente="floresta",
        )
        print(f"[{dificuldade.upper()}] {encounter['descricao']}")
        inimigos_str = ", ".join(
            f"{e['quantidade']}x {e['nome']}" for e in encounter["inimigos"]
        )
        print(f"   Inimigos: {inimigos_str}")
        print(f"   XP Total: {encounter['xp_total']}")
        print(f"   Tesouro: {', '.join(encounter['tesouro'][:2])}")
        print(f"   Táticas: {encounter['taticas'][:100]}...")
        print()

    print("=" * 70)
    print("[OK] Geração concluída. Conteúdo segue as regras do 3D&T.")
    print("=" * 70)


if __name__ == "__main__":
    demo_generation()
