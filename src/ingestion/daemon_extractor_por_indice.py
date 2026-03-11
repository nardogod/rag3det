"""
Estratégia 2: Busca por nome no índice.
Para cada criatura faltante, busca o nome no texto e extrai o bloco (nome -> descrição)
mesmo sem stats explícitos. Usa daemon_stats_fallback para F/H/R/A/PdF.
"""

from __future__ import annotations

import re
from typing import Any

# Índice de criaturas do Guia de Monstros de Arton
INDICE_ARTON = [
    "Abelha-Gigante", "Água-Viva", "Ameba-Gigante", "Anões", "Aparições",
    "Aranhas-Gigantes", "Arraia", "Asa-Assassina", "Asa-Negra", "Asflor",
    "Assassino da Savana", "Assustador", "Avatares", "Baleias", "Banshee",
    "Basilisco", "Beijo-de-Tenebra", "Besouros", "Brownies", "Bruxas",
    "Canários-do-Sono", "Caoceronte", "Carniceiros", "Carrasco de Lena",
    "Cavalos", "Centauro", "Centopéia-Gigante", "Ceratops", "Cocatriz",
    "Colosso da Tormenta", "Composognato", "Corcel do Deserto", "Corcel das Trevas",
    "Couatl", "Crocodilos", "Demônios", "Devoradores", "Diabo-de-Keenn",
    "Dimmak", "Dinonico", "Dionys", "Dragões", "Dríade", "Duplo",
    "Elefantes", "Elementais", "Elfos", "Enfermeiras", "Entes", "Esfinge",
    "Esqueletos", "Familiares", "Fantasma", "Fênix", "Feras-Caçus", "Fil-Gikin",
    "Fofo", "Fogo-Fátuo", "Formigas-Hiena", "Fungi", "Gafanhoto-Tigre",
    "Gambá", "Gárgula", "Gênios", "Ghoul", "Gigantes", "Gnolls",
    "Goblinóides", "Golens", "Golfinho", "Gondo", "Górgon", "Grama Carnívora",
    "Grandes Felinos", "Grandes Símios", "Grifo", "Guerreiro da Luz",
    "Halflings", "Harpia", "Hidra", "Hipogrifo", "Homens-Escorpião",
    "Homens-Lagarto", "Homens-Morcego", "Homens-Serpente", "Homúnculo",
    "Horror dos Túmulos", "Ictiossauro", "Incubador", "Kaatar-nirav",
    "Kanatur", "Katrak", "Killbone", "Kobolds", "Kraken", "Leão-de-Keenn",
    "Lesma-Carnívora", "Licantropos", "Lich", "Lobo-das-Cavernas",
    "Mago-Fantasma", "Manticora", "Mortos-Vivos", "Múmia", "Naga",
    "Neblina-Fantasma", "Neblina-Vampírica", "Necrodracos", "Nereida Abissal",
    "Ninfa", "Observadores", "Ogres", "Ores", "Pantera-do-Vidro",
    "Pássaros Arco-Íris", "Pássaros do Caos", "Pégaso", "Peixe-Couraca",
    "Peixe-Gancho", "Peixe-Recife", "Planador", "Povo-Dinossauro", "Povo-Sapo",
    "Predador dos Sonhos", "Predador-Toupeira", "Protocraco", "Pteranodonte",
    "Pteros", "Pudim Negro", "Quelicerossauros", "Quelonte", "Quimera",
    "Random", "Ratazanas", "Serpentes Venenosas", "Siba Gigante", "Sharks",
    "Shimav", "Shinobi", "Soldados-Mortos", "Sprites", "Tahab-krar",
    "Tai-Kanatur", "Tasloi", "Tatu-Aranha", "Tentáculo", "Terizinossauro",
    "Tigre-de-Hyninn", "Toscos", "T-Rex", "Triceratops", "Trilobitas",
    "Trobos", "Trogloditas", "Troll", "Ursos", "Unicórnio", "Vampiro",
    "Varano de Krah", "Velociraptor", "Velocis",
]

# Aliases: nomes no PDF podem diferir do índice
ALIASES_BUSCA: dict[str, list[str]] = {
    "Feras-Caçus": ["Feras-Cactus", "Feras Cactus"],
    "Fil-Gikin": ["Fil-Gikim", "Fil Gikim"],
}


def _normalizar_busca(nome: str) -> str:
    return nome.strip().lower().replace("-", " ").replace("  ", " ")


def _nome_match(texto: str, nome: str) -> list[tuple[int, int]]:
    """Retorna [(start, end), ...] de ocorrências do nome no texto."""
    norm = _normalizar_busca(nome)
    variantes = [nome, nome.replace("-", " "), nome.replace("-", "- ")]
    resultados: list[tuple[int, int]] = []
    for v in variantes:
        pat = r"\b" + re.escape(v) + r"\b"
        for m in re.finditer(pat, texto, re.IGNORECASE):
            resultados.append((m.start(), m.end()))
    if not resultados:
        idx = texto.lower().find(norm)
        if idx >= 0:
            resultados.append((idx, idx + len(nome)))
    return resultados


def _extrair_bloco_apos_nome(
    texto: str, pos_nome: int, fim_nome: int, max_chars: int = 2500
) -> str:
    """Extrai bloco de texto após o nome até próximo monstro ou limite."""
    inicio = fim_nome
    fim = min(len(texto), inicio + max_chars)
    bloco = texto[inicio:fim]
    for pat in [
        r"\n\s*[A-ZÀ-ÿ][a-zà-ÿ\s\-']{2,40}\s*\n\s*[\"'-]",
        r"\n\s*CON\s+\d",
        r"\n\s*#\s*[Aa]taques",
    ]:
        m = re.search(pat, bloco)
        if m and m.start() < 500:
            bloco = bloco[: m.start()]
    return bloco.strip()


def _pagina_para_pos(pos: int, page_breaks: list[int]) -> int:
    for i in range(len(page_breaks) - 1):
        if page_breaks[i] <= pos < page_breaks[i + 1]:
            return i + 1
    return len(page_breaks) if page_breaks else 1


def extrair_por_indice(
    texto: str,
    livro: str,
    bestiario: list[dict],
    nomes_faltantes: list[str],
    nomes_ja_extraidos: set[str],
    page_breaks: list[int] | None = None,
) -> list[dict]:
    """
    Para cada nome em nomes_faltantes que não está em nomes_ja_extraidos,
    busca no texto e extrai bloco. Usa fallback para stats.
    """
    from src.ingestion.daemon_stats_fallback import (
        buscar_no_bestiario,
        extrair_stats_da_descricao,
        mesclar_stats,
    )
    from src.ingestion.extrair_habilidades_daemon import extrair_habilidades_daemon

    def _ja_tem(n: str) -> bool:
        nlow = _normalizar_busca(n)
        for ex in nomes_ja_extraidos:
            if nlow in _normalizar_busca(ex) or _normalizar_busca(ex) in nlow:
                return True
        return False

    resultados: list[dict] = []
    for nome in nomes_faltantes:
        if _ja_tem(nome):
            continue
        # Buscar nome e aliases (ex.: Feras-Caçus → Feras-Cactus)
        nomes_buscar = [nome] + ALIASES_BUSCA.get(nome, [])
        ocorrencias: list[tuple[int, int]] = []
        nome_encontrado = nome
        for nb in nomes_buscar:
            occ = _nome_match(texto, nb)
            if occ:
                ocorrencias = occ
                nome_encontrado = nb
                break
        if not ocorrencias:
            continue
        pos_nome, fim_nome = ocorrencias[0]
        bloco = _extrair_bloco_apos_nome(texto, pos_nome, fim_nome)
        if len(bloco) < 50:
            continue

        stats_desc = extrair_stats_da_descricao(bloco)
        ref = buscar_no_bestiario(nome, bestiario)
        stats_ref = ref.get("caracteristicas") if ref else None
        caracteristicas = mesclar_stats(
            {"F": "0", "H": "0", "R": "0", "A": "0", "PdF": "0"},
            stats_desc,
            stats_ref,
        )
        hab_combate = extrair_habilidades_daemon(bloco)

        resultados.append({
            "nome": nome.strip(),  # Nome do índice (canônico)
            "tipo": "outro",
            "caracteristicas": caracteristicas,
            "pv": "variável",
            "pm": "0",
            "habilidades": [],
            "habilidades_combate": hab_combate,
            "tesouro": "",
            "vulnerabilidades": [],
            "fraqueza": "",
            "descricao": bloco,
            "livro": livro,
            "pagina": _pagina_para_pos(pos_nome, page_breaks or []),
            "_fonte": "daemon_por_indice",
        })

    return resultados
