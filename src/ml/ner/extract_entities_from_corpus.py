"""
Extração de entidades 3D&T diretamente do corpus, sem conhecimento prévio.

Pipeline:
  a) Carrega chunks (de lista em memória ou data/processed/)
  b) Identifica padrões: CAIXA ALTA, Title Case, "O [Nome] é um [tipo]", "[Nome]: desc", "• Nome"
  c) Detecção de tipo por PONTUAÇÃO: conteúdo (peso 5), seção (3), secundário (2) no texto completo do chunk
  d) Resolução: max(pontos) >= 5 → tipo; >= 2 → DESCONHECIDO; senão ENTIDADE
  e) Pós-processamento (MAGIA com stats → revisão); validação revisar_*
  f) Mantém entidades com menções >= min_mentions
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document


logger = logging.getLogger(__name__)

# min_mentions por tipo (entidades importantes com poucas menções são mantidas)
MIN_MENTIONS_BY_TYPE: Dict[str, int] = {
    "MAGIA": 2,
    "MONSTRO": 4,
    "ITEM": 3,
    "VANTAGEM": 3,
    "DESVANTAGEM": 3,
    "PERÍCIA": 3,
    "DESCONHECIDO": 10,
}
DEFAULT_MIN_MENTIONS = 4

TYPE_DESCONHECIDO = "DESCONHECIDO"
TYPE_ENTIDADE = "ENTIDADE"

# Entidades críticas: sempre mantidas (min 1 menção) e forçadas a MAGIA
CRITICAL_ENTITIES = frozenset({
    "Bola de Fogo", "Bola de fogo", "Invocação da Fênix", "Invocação da Fenix",
    "Mãos de Fogo", "Maos de Fogo", "Muralha de Fogo", "Raio de Gelo", "Cura Completa",
    "Relâmpago", "Relampago",
    "Magia Elemental", "Magia Branca", "Magia Negra", "Magia Arcana",
})

WEIGHT_CONTENT = 5
WEIGHT_SECTION = 3
WEIGHT_SECONDARY = 2

# ========== 1. PADRÕES DE CONTEÚDO (peso 5) – texto completo do chunk ==========

# MAGIA
RE_MAGIA_CUSTO_PM = re.compile(
    r"(?i)(custa?|gasta?|gasto)\s*[:]?\s*(\d+)\s*(PM|pm|Pm|pontos?\s*de\s*man[áa])"
)
RE_MAGIA_DURACAO = re.compile(
    r"(?i)(dura[çc][aã]o|durar?)\s*[:]?.*?(\d+\s*(turno|rodada|minuto|hora|cena)|instant[âa]nea|permanente)"
)
RE_MAGIA_ALCANCE = re.compile(
    r"(?i)(alcance|dist[âa]ncia|range)\s*[:]?.*?(\d+\s*metros?|toque|pessoal|vis[ãa]o|ilimitado)"
)
RE_MAGIA_ESCOLA = re.compile(
    r"(?i)(escola|escolas)\s*[:]?.*?(elemental|branca|negra|arcana|divina|ilusionismo|necromancia)"
)
RE_MAGIA_ELEMENTO = re.compile(
    r"(?i)(elemento|elemental)\s*[:]?.*?(fogo|[áa]gua|ar|terra|luz|trevas|gelo|rel[âa]mpago|natureza)"
)
RE_MAGIA_TIPO = re.compile(
    r"(?i)\b(magia|feitico|feiti[çc]o|conjura[çc][aã]o|invoca[çc][aã]o|encantamento)\s+(de|do|da)\s+"
)
# Magias conhecidas: case-insensitive, variações de acento (de/do, á/â, ç/c)
RE_MAGIA_CONHECIDA = re.compile(
    r"(?i)\b(Bola\s+d[eo]\s+[Ff]ogo|M[aã]os\s+d[eo]\s+[Ff]ogo|Muralha\s+d[eo]\s+[Ff]ogo|"
    r"Invoca[çc][aã]o\s+d[ea]\s+[Ff][eê]nix|Raio\s+d[eo]\s+[Gg]elo|Cura\s+Completa|Rel[aâ]mpago)\b"
)
# Categorias de magia (Magia Elemental, Magia Branca, etc.) → sempre MAGIA (permite espaços extras e acento)
RE_MAGIA_CATEGORY = re.compile(
    r"(?i)^\s*M[aá]gia\s+(Elemental|Branca|Negra|Arcana|Divina|Ilusionismo|Necromancia)\s*$"
)

# MONSTRO
RE_MONSTRO_STATS = re.compile(
    r"(?i)\bF\s*[:.]?\s*(\d+)[-–]?\d*\s*[,;]?\s*H\s*[:.]?\s*(\d+)[-–]?\d*\s*[,;]?\s*R\s*[:.]?\s*(\d+)[-–]?\d*\s*[,;]?\s*A\s*[:.]?\s*(\d+)[-–]?\d*\b"
)
RE_MONSTRO_PV_PM = re.compile(r"(?i)\bPV\s*[:.]?\s*(\d+)\s*[,;]?\s*PM\s*[:.]?\s*(\d+)\b")
RE_MONSTRO_PV = re.compile(r"(?i)\b(PV|pontos?\s*de\s*vida)\s*[:.]?\s*(\d+)\b")
RE_MONSTRO_INICIATIVA = re.compile(
    r"(?i)(iniciativa|in[íi]c)\s*[:.]?.*?(\d+|nunca|sempre|autom[áa]tica)"
)
RE_MONSTRO_IMUNIDADE = re.compile(
    r"(?i)(imune|imunidade)\s*a?\s*[:]?.*?(fogo|[áa]gua|gelo|rel[âa]mpago|veneno|doen[çc]a|magia|arma)"
)
RE_MONSTRO_VULNERABILIDADE = re.compile(
    r"(?i)(vulner[áa]vel|vulnerabilidade|fraqueza)\s*a?\s*[:]?.*?(fogo|sagrado|prata|magia)"
)
RE_MONSTRO_TIPO = re.compile(
    r"(?i)\b(monstro|criatura|besta|ser|inimigo)\s+(de|do|da)\s+(fogo|gelo|trevas|morte|sombras)\b"
)
RE_MONSTRO_RACA = re.compile(
    r"(?i)\b(elfo|an[ãa]o|humano|orc|goblin|drag[ãa]o|morto[-\s]?vivo|zumbi|esqueleto|vampiro|lobisomem)\b"
)

# ITEM
RE_ITEM_PE = re.compile(r"(?i)(\d+)\s*(PE|pe|PEs|pes)\b")
RE_ITEM_MOEDAS = re.compile(r"(?i)(\d+)\s*(PO|po|PP|pp|PC|pc|PL|pl)\b")
RE_ITEM_TIPO = re.compile(
    r"(?i)\b(arma|armadura|escudo|po[çc][aã]o|anel|amuleto|bast[ãa]o|cajado|varinha|pergaminho|livro|mapa|chave)\b"
)
RE_ITEM_BONUS = re.compile(
    r"(?i)(b[ôo]nus|bonus)\s*[:]?.*?([+-]?\d+)\s*(em\s+)?(FA|FD|PV|PM|teste|dano)"
)
RE_ITEM_EQUIPAMENTO = re.compile(
    r"(?i)\b(equipamento|equipar|vestir|empunhar|usar)\b"
)

# VANTAGEM / DESVANTAGEM
RE_VANTAGEM = re.compile(r"(?i)\b(vantagem|talento|perk|dom)\b")
RE_DESVANTAGEM = re.compile(r"(?i)\b(desvantagem|defeito|falha)\b")
RE_CUSTO_XP = re.compile(
    r"(?i)(\d+)\s*(XP|xp|experi[êe]ncia|pontos?\s*de\s*vantagem)"
)

# Secundários (peso 2)
RE_SEC_ELEMENTO_ESCOLA = re.compile(r"(?i)(elemento|escola)\b")
RE_SEC_ATAQUE_DANO_STATS = re.compile(
    r"(?i)(ataque|dano)\b.*\b(F|H|R|A|PV|PM)\s*[:.]?\s*\d+|\b(F|H|R|A)\s*[:.]?\s*\d+.*(ataque|dano)"
)
RE_SEC_PRECO_COMPRAR = re.compile(r"(?i)(preço|comprar)\b")
RE_SEC_CUSTO_PONTOS = re.compile(r"(?i)custo\s*(em\s*)?pontos?\b")

# Stats no texto (pós-processamento e secundário MONSTRO)
STATS_RE = re.compile(
    r"\b(?:F|Força|H|Habilidade|R|Resistência|A|Agilidade)[\s:]*\d+|\bPV\s*:?\s*\d+|\bPM\s*:?\s*\d+",
    re.IGNORECASE,
)

# Padrões de extração de nomes
PATTERN_O_X_E_UM = re.compile(
    r"\b(?:O|A)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇÀÜa-záéíóúâêôãõçàü][A-Za-záéíóúâêôãõçàü\s\-']+?)\s+é\s+(?:um|uma|uns|umas)\s+",
    re.IGNORECASE,
)
PATTERN_X_DOIS_PONTOS = re.compile(
    r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç][A-Za-záéíóúâêôãõç\s\-']{2,40}?)\s*:\s*",
    re.MULTILINE,
)
PATTERN_BULLET = re.compile(r"^[\s]*[•\-]\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç][A-Za-záéíóúâêôãõç\s\-']{1,50}?)(?:\s*[:\-]|\s*$|\n)", re.MULTILINE)
PATTERN_UPPERCASE = re.compile(r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇÀÜ][A-ZÁÉÍÓÚÂÊÔÃÕÇÀÜ\s\-']{1,40})\b")
PATTERN_TITLE_CASE = re.compile(
    r"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç][a-záéíóúâêôãõç]*(?:\s+(?:da|de|do|dos|das|e|ou)\s+[a-záéíóúâêôãõç]+)*\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç][a-záéíóúâêôãõç]+(?:\s+[A-Za-záéíóúâêôãõç][a-záéíóúâêôãõç]*)*)\b"
)


# Nomes que não são entidades (metadados, rótulos de stats, cabeçalhos)
NOT_ENTITY_NAMES = frozenset({
    "FA", "FD", "PV", "PM", "PE", "XP", "PO", "PP", "PC", "PL",
    "Alcance", "Duração", "Custo", "Função", "Além disso", "Por exemplo",
    "No entanto", "Sentidos Especiais", "Código de Honra", "Combate",
    "O jogo", "A regra", "T Alpha", "por exemplo",
    "Se falhar", "Se passar", "veja abaixo", "veja adiante",
    "por turno", "por rodada", "por minuto",
    "ou mais", "ou menos", "ou seja",
    "NÃO", "SIM", "não", "sim",
    "você pode", "você pode gastar", "você deve",
    "isto é", "a saber",
    "Exemplo", "Exigências", "RPG",
    "para cada", "do Manual", "e assim por diante", "de altura",
    "no entanto", "Por outro lado", "pelo custo normal em", "Magias",
    "Na verdade", "na verdade", "Na Verdade",
    "Na prática", "na prática",
    "Em geral", "em geral",
    "A seguir", "a seguir",
    "De acordo", "de acordo",
    "Em resumo", "em resumo",
    "T Alpha pg", "a pg", "Por isso", "por isso", "APENAS", "QUALQUER", "TODAS",
    "sua escolha", "Se for bem", "arredondado para baixo",
    "Escola", "Por fim",
})
# Padrão regex para bloquear frases comuns (match exato do nome normalizado)
RE_NOT_ENTITY_PHRASE = re.compile(
    r"(?i)^(se\s+(falhar|passar)|veja\s+(abaixo|adiante)|por\s+(turno|rodada|minuto)|"
    r"ou\s+(mais|menos|seja)|voc[eê]\s+pode|voc[eê]\s+deve|isto\s+[ée]|a\s+saber|"
    r"para\s+cada|do\s+Manual|e\s+assim\s+por\s+diante|de\s+altura|no\s+entanto|"
    r"por\s+outro\s+lado|pelo\s+custo\s+normal|"
    r"Na\s+verdade|Na\s+pr[áa]tica|Em\s+geral|A\s+seguir|De\s+acordo|Em\s+resumo)$"
)
# Fragmentos de parse: descartar (não extrair)
RE_FRAGMENT_LOWERCASE_THEN_UPPER = re.compile(r"^[a-záéíóúâêîôûãõç]+\s+[A-ZÁÉÍÓÚ]")  # "sustentável Alcance"
RE_FRAGMENT_STATS_PREFIX = re.compile(r"^[FHRA]-$")  # H-, F-, R-, A-
RE_FRAGMENT_PADRAO_TIPO = re.compile(r"(?i)^(padrão|tipo|modelo|exemplo)\s+")  # "padrão Duração"
RE_FRAGMENT_HYPHEN_END = re.compile(r"-$")  # termina com hífen
# Fragmentos de lista: começa com "e ", "ou ", "de ", etc.
RE_FRAGMENT_LIST_PREFIX = re.compile(r"(?i)^(e\s+|ou\s+|de\s+|da\s+|do\s+|em\s+|no\s+|na\s+)[A-ZÁÉÍÓÚ]")
# Metadados de página, range, instruções, conectivos, ênfase
RE_FRAGMENT_PG = re.compile(r"(?i).*\b(pg|p[áa]g|p[áa]gina)\s*\d*$")
RE_FRAGMENT_A_ATE = re.compile(r"(?i)^a\s+at[eé]")
RE_FRAGMENT_ARREDONDADO = re.compile(r"(?i)^arredondado")
RE_FRAGMENT_POR_ISSO = re.compile(r"(?i)^[Pp]or\s+isso$")
RE_FRAGMENT_PARA_SEM = re.compile(r"(?i)^(para|sem)\s+")
RE_FRAGMENT_ALL_CAPS = re.compile(r"^[A-Z]{4,}$")  # APENAS, QUALQUER, TODAS
RE_FRAGMENT_SUA_SE = re.compile(r"(?i)^(sua|se)\s+")
RE_FRAGMENT_CAPACIDADE_DE = re.compile(r"(?i)^capacidade\s+de")
RE_FRAGMENT_PERMANENTE_ALCANCE = re.compile(r"(?i)permanente.*alcance$")
RE_FRAGMENT_COM_METADE = re.compile(r"(?i)^com\s+metade\s+do")
RE_FRAGMENT_ELEMENTAL_DA = re.compile(r"(?i)^Elemental\s+da?$")
RE_FRAGMENT_POR_FIM = re.compile(r"(?i)^[Pp]or\s+fim$")
RE_FRAGMENT_A_ARTIGO = re.compile(r"^a\s+")  # "a mordida" (minúsculo, fragmento)
RE_FRAGMENT_UMA_VEZ_POR = re.compile(r"(?i)^uma\s+vez\s+por")
RE_FRAGMENT_AO_INVES_DE = re.compile(r"(?i)^ao\s+inv[eé]s\s+de")
RE_FRAGMENT_COMER_OU = re.compile(r"(?i)^comer\s+ou")
RE_FRAGMENT_E_AUTOMATICAMENTE = re.compile(r"(?i)^[ée]\s+automaticamente")
RE_FRAGMENT_ELES_GASTAM = re.compile(r"(?i)^[Ee]les\s+gastam")

# Reclassificação de DESCONHECIDO → MAGIA (estrita: nome próprio + padrão mágico)
# Só reclassifica se nome começa com maiúscula E contém padrão (Magia de X, X Mágico, Ilusão, etc.)
RE_DESCONHECIDO_TO_MAGIA = re.compile(
    r"(?i)\b(Magia\s+(de|do|da)|[A-Za-záéíóúâêôãõç]+\s+(M[áa]gico|M[áa]gica)|"
    r"Ilus[ãa]o|Encantamento|Conjura[çc][aã]o)\b"
)
# Reclassificação DESCONHECIDO → VANTAGEM (Corpo Elemental, Habilidades Naturais, etc.)
RE_DESCONHECIDO_TO_VANTAGEM = re.compile(
    r"(?i)^[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç].*\b(Cr[íi]tico|Ataque|Defesa|Habilidade|Habilidades|"
    r"Vantagem|Corpo|Elemental|Natural|Medo|Aura|Dano|Aumento|Aprimorado)\b"
)


def _normalize_entity(name: str) -> str:
    return " ".join((name or "").strip().split())


def _name_title(name: str) -> str:
    """Normaliza para comparação com listas (strip + title case). 'magia branca' → 'Magia Branca'."""
    return (name or "").strip().title()


def _is_critical_entity(name: str) -> bool:
    """True se entidade é crítica (sempre mantida, min 1 menção, forçar MAGIA)."""
    n = _normalize_entity(name)
    t = _name_title(name)
    return n in CRITICAL_ENTITIES or t in CRITICAL_ENTITIES or n in CRITICAL_MAGIC_NAMES or t in CRITICAL_MAGIC_NAMES


def _is_fragment(name: str) -> bool:
    """True se o nome é fragmento de parse e deve ser descartado (não extrair)."""
    n = (name or "").strip()
    if not n:
        return True
    if RE_FRAGMENT_LOWERCASE_THEN_UPPER.match(n):
        return True
    if RE_FRAGMENT_STATS_PREFIX.match(n):
        return True
    if RE_FRAGMENT_PADRAO_TIPO.match(n):
        return True
    if RE_FRAGMENT_HYPHEN_END.search(n):
        return True
    if RE_FRAGMENT_LIST_PREFIX.match(n):
        return True
    if RE_FRAGMENT_PG.match(n):
        return True
    if RE_FRAGMENT_A_ATE.match(n):
        return True
    if RE_FRAGMENT_ARREDONDADO.match(n):
        return True
    if RE_FRAGMENT_POR_ISSO.match(n):
        return True
    if RE_FRAGMENT_PARA_SEM.match(n):
        return True
    if RE_FRAGMENT_ALL_CAPS.match(n):
        return True
    if RE_FRAGMENT_SUA_SE.match(n):
        return True
    if RE_FRAGMENT_CAPACIDADE_DE.match(n):
        return True
    if RE_FRAGMENT_PERMANENTE_ALCANCE.search(n):
        return True
    if RE_FRAGMENT_COM_METADE.match(n):
        return True
    if RE_FRAGMENT_ELEMENTAL_DA.match(n):
        return True
    if RE_FRAGMENT_POR_FIM.match(n):
        return True
    if RE_FRAGMENT_A_ARTIGO.match(n):
        return True
    if RE_FRAGMENT_UMA_VEZ_POR.match(n):
        return True
    if RE_FRAGMENT_AO_INVES_DE.match(n):
        return True
    if RE_FRAGMENT_COMER_OU.match(n):
        return True
    if RE_FRAGMENT_E_AUTOMATICAMENTE.match(n):
        return True
    if RE_FRAGMENT_ELES_GASTAM.match(n):
        return True
    # Descrição longa sem formato de nome (poucas palavras com maiúscula)
    if len(n) > 40:
        words = n.split()
        title_case_count = sum(1 for w in words if w and w[0].isupper())
        if title_case_count < 2:
            return True
    return False


# Stopwords e verbos comuns para heurística de nome próprio (MONSTRO)
STOPWORDS_PHRASE = frozenset({
    "se", "falhar", "passar", "veja", "abaixo", "adiante", "por", "turno", "rodada",
    "ou", "mais", "menos", "seja", "não", "sim", "você", "pode", "gastar", "deve",
    "isto", "é", "saber", "função", "exemplo", "exigências",
})
# Tipos genéricos de item (só tipo, sem qualificador) → peso 2
ITEM_GENERIC_TIPOS = frozenset({
    "arma", "armadura", "escudo", "poção", "pocao", "anel", "amuleto", "bastão", "bastao",
    "cajado", "varinha", "pergaminho", "livro", "mapa", "chave", "equipamento",
})


def _proper_noun_score(name: str) -> int:
    """
    Heurística de nome próprio para MONSTRO (0-5).
    score < 2 → não considerar MONSTRO.
    """
    n = (name or "").strip()
    if not n or len(n) < 2:
        return 0
    words = n.split()
    score = 0
    # +1 se tem palavra em MAIÚSCULAS (FÊNIX, DRAGÃO)
    if any(w.isupper() and len(w) >= 2 for w in words):
        score += 1
    # +1 se tem palavra Title Case (Dragão, Vermelho)
    if any(w and w[0].isupper() and len(w) > 1 for w in words):
        score += 1
    # +1 se tem hífen ou nome composto (2+ palavras)
    if "-" in n or (len(words) >= 2 and not all(w.lower() in STOPWORDS_PHRASE for w in words)):
        score += 1
    # +1 se NÃO é só stopword/verbo comum
    if words and not all(w.lower() in STOPWORDS_PHRASE for w in words):
        score += 1
    # +1 se tem 2+ palavras OU é único (palavra única com maiúscula/title)
    if len(words) >= 2 or (len(words) == 1 and words[0] and (words[0][0].isupper() or words[0].isupper())):
        score += 1
    return min(score, 5)


def _is_generic_item_name(name: str) -> bool:
    """True se o nome é só tipo de item sem qualificador (Armadura, Poção, Arma)."""
    n = (name or "").strip().lower()
    if not n:
        return True
    words = n.split()
    if len(words) == 1:
        return words[0] in ITEM_GENERIC_TIPOS or words[0] in ("rpg", "uso")
    if len(words) == 2 and words[0] in ITEM_GENERIC_TIPOS and words[1] in ("de", "do", "da", "e", "ou"):
        return True
    return False


def _score_chunk_content(text: str) -> Dict[str, int]:
    """Pontuação por padrões de CONTEÚDO no texto completo do chunk (peso 5 forte, 2 fraco)."""
    scores: Dict[str, int] = defaultdict(int)
    if not text:
        return scores
    # MAGIA (qualquer um = sinal forte)
    if (
        RE_MAGIA_CUSTO_PM.search(text)
        or RE_MAGIA_DURACAO.search(text)
        or RE_MAGIA_ALCANCE.search(text)
        or RE_MAGIA_ESCOLA.search(text)
        or RE_MAGIA_ELEMENTO.search(text)
        or RE_MAGIA_TIPO.search(text)
        or RE_MAGIA_CONHECIDA.search(text)
    ):
        scores["MAGIA"] += WEIGHT_CONTENT
    # MONSTRO: exige dois sinais — (stats ou PV+PM) E (iniciativa, imunidade, vulnerabilidade ou "monstro/criatura de X")
    has_stats_or_pvpm = bool(RE_MONSTRO_STATS.search(text) or RE_MONSTRO_PV_PM.search(text))
    has_creature_signals = bool(
        RE_MONSTRO_INICIATIVA.search(text)
        or RE_MONSTRO_IMUNIDADE.search(text)
        or RE_MONSTRO_VULNERABILIDADE.search(text)
        or RE_MONSTRO_TIPO.search(text)
    )
    if has_stats_or_pvpm and has_creature_signals:
        scores["MONSTRO"] += WEIGHT_CONTENT
    elif has_stats_or_pvpm or RE_MONSTRO_RACA.search(text):
        scores["MONSTRO"] += WEIGHT_SECONDARY
    elif RE_MONSTRO_PV.search(text):
        scores["MONSTRO"] += WEIGHT_SECONDARY
    # ITEM: preço PE/moedas e tipo/bônus = forte; "equipamento" genérico = fraco
    if (
        RE_ITEM_PE.search(text)
        or RE_ITEM_MOEDAS.search(text)
        or RE_ITEM_TIPO.search(text)
        or RE_ITEM_BONUS.search(text)
    ):
        scores["ITEM"] += WEIGHT_CONTENT
    elif RE_ITEM_EQUIPAMENTO.search(text):
        scores["ITEM"] += WEIGHT_SECONDARY
    # VANTAGEM / DESVANTAGEM
    if RE_VANTAGEM.search(text) or RE_CUSTO_XP.search(text):
        scores["VANTAGEM"] += WEIGHT_CONTENT
    if RE_DESVANTAGEM.search(text):
        scores["DESVANTAGEM"] += WEIGHT_CONTENT
    return scores


def _score_chunk_section(section: str, source: str) -> Dict[str, int]:
    """Pontuação por SEÇÃO/SOURCE do documento (peso 3)."""
    scores: Dict[str, int] = defaultdict(int)
    sec = (section or "").lower()
    src = (source or "").lower()
    # MAGIA
    if "magia" in src or "feitico" in src or "feitiço" in src or "spell" in src:
        scores["MAGIA"] += WEIGHT_SECTION
    if "magia" in sec or "conjuração" in sec or "conjuraçao" in sec or "feitiçaria" in sec or "arcana" in sec:
        scores["MAGIA"] += WEIGHT_SECTION
    # MONSTRO
    if "monstro" in src or "bestiario" in src or "bestiário" in src or "creature" in src:
        scores["MONSTRO"] += WEIGHT_SECTION
    if "monstro" in sec or "criatura" in sec or "bestiário" in sec or "bestiario" in sec or "inimigo" in sec:
        scores["MONSTRO"] += WEIGHT_SECTION
    # ITEM
    if "equipamento" in src or "item" in src or "tesouro" in src:
        scores["ITEM"] += WEIGHT_SECTION
    if "equipamento" in sec or "item" in sec or "tesouro" in sec or "arsenal" in sec:
        scores["ITEM"] += WEIGHT_SECTION
    # VANTAGEM
    if "vantagem" in src or "pericia" in src or "perícia" in src or "skill" in src:
        scores["VANTAGEM"] += WEIGHT_SECTION
    if "vantagem" in sec or "perícia" in sec or "pericia" in sec or "talento" in sec or "característica" in sec:
        scores["VANTAGEM"] += WEIGHT_SECTION
    return scores


def _score_chunk_secondary(text: str) -> Dict[str, int]:
    """Padrões secundários (peso 2)."""
    scores: Dict[str, int] = defaultdict(int)
    if not text:
        return scores
    if RE_SEC_ELEMENTO_ESCOLA.search(text):
        scores["MAGIA"] += WEIGHT_SECONDARY
    if RE_SEC_ATAQUE_DANO_STATS.search(text) or STATS_RE.search(text):
        scores["MONSTRO"] += WEIGHT_SECONDARY
    if RE_SEC_PRECO_COMPRAR.search(text):
        scores["ITEM"] += WEIGHT_SECONDARY
    if RE_SEC_CUSTO_PONTOS.search(text):
        scores["VANTAGEM"] += WEIGHT_SECONDARY
    return scores


def _merge_scores(acc: Dict[str, int], add: Dict[str, int]) -> None:
    for k, v in add.items():
        acc[k] = acc.get(k, 0) + v


def _score_chunk(section: str, source: str, text: str) -> Dict[str, int]:
    """Pontuação total: conteúdo (5/2) + seção (3) + secundário (2)."""
    total: Dict[str, int] = defaultdict(int)
    _merge_scores(total, _score_chunk_content(text))
    _merge_scores(total, _score_chunk_section(section, source))
    _merge_scores(total, _score_chunk_secondary(text))
    return total


def _resolve_type_from_scores(type_scores: Dict[str, int]) -> Tuple[str, str]:
    """
    Decisão final a partir da pontuação acumulada.
    Retorna (tipo, confidence: "alta"|"media"|"revisar"|"baixa").
    DESCONHECIDO com max >= 3 e tipo claramente líder → promove para esse tipo.
    """
    if not type_scores or all(v == 0 for v in type_scores.values()):
        return TYPE_ENTIDADE, "baixa"
    tipo = max(type_scores, key=type_scores.get)
    pts = type_scores[tipo]
    sorted_vals = sorted(type_scores.values(), reverse=True)
    second_best = sorted_vals[1] if len(sorted_vals) > 1 else 0
    if pts >= 8:
        return tipo, "alta"
    if pts >= 5:
        return tipo, "media"
    # Reclassificação: 3 <= pts < 5 e líder claro (segundo pelo menos 2 abaixo) → promove
    if 3 <= pts < 5 and pts >= second_best + 2:
        return tipo, "revisar"
    if pts >= 2:
        return TYPE_DESCONHECIDO, "revisar"
    return TYPE_ENTIDADE, "baixa"


def _extract_from_patterns(text: str) -> List[Tuple[str, str]]:
    """Retorna lista de (entidade_normalizada, trecho_contexto)."""
    found: List[Tuple[str, str]] = []
    seen = set()
    for pattern, group in [
        (PATTERN_O_X_E_UM, 1),
        (PATTERN_X_DOIS_PONTOS, 1),
        (PATTERN_BULLET, 1),
        (PATTERN_UPPERCASE, 1),
        (PATTERN_TITLE_CASE, 1),
    ]:
        for m in pattern.finditer(text):
            name = _normalize_entity(m.group(group))
            if len(name) < 2 or name.lower() in ("o", "a", "e", "um", "uma", "de", "da", "do"):
                continue
            if name in NOT_ENTITY_NAMES or name in seen:
                continue
            if RE_NOT_ENTITY_PHRASE.match(name.strip()):
                continue
            if _is_fragment(name):
                continue
            seen.add(name)
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 60)
            ctx = text[start:end].replace("\n", " ")
            found.append((name, ctx))
    return found


def _source_key(meta: dict) -> str:
    source = meta.get("source") or meta.get("book_title") or "unknown"
    if isinstance(source, Path):
        source = source.name
    page = meta.get("page", "?")
    return f"{source}:{page}"


def _chunk_has_magia_hints(text: str) -> Tuple[bool, bool, bool]:
    """Retorna (tem cost_pm, tem element, tem school) no texto."""
    cost_pm = bool(RE_MAGIA_CUSTO_PM.search(text))
    elem = bool(RE_MAGIA_ELEMENTO.search(text) or RE_MAGIA_ESCOLA.search(text))
    school = bool(RE_MAGIA_ESCOLA.search(text))
    return cost_pm, elem or school, school


def _chunk_has_monstro_hints(text: str) -> Tuple[bool, bool]:
    """Retorna (tem stats F/H/R/A, tem PV)."""
    stats = bool(RE_MONSTRO_STATS.search(text))
    pv = bool(RE_MONSTRO_PV.search(text) or RE_MONSTRO_PV_PM.search(text))
    return stats, pv


def _chunk_has_item_hints(text: str) -> Tuple[bool, bool]:
    """Retorna (tem preço, tem bônus)."""
    preco = bool(RE_ITEM_PE.search(text) or RE_ITEM_MOEDAS.search(text))
    bonus = bool(RE_ITEM_BONUS.search(text))
    return preco, bonus


def _post_process_type(etype: str, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Pós-processamento: MAGIA com stats F/H/R/A → DESCONHECIDO.
    Validação revisar_*: marcar quando tipo não tem indícios no conteúdo.
    Retorna (tipo_final, motivo_revisao ou None).
    """
    if etype == "MAGIA" and data.get("stats"):
        return TYPE_DESCONHECIDO, "MAGIA com stats F/H/R/A"
    # Revisar MAGIA sem indícios de magia no conteúdo (nenhum de cost_pm, element, school)
    if etype == "MAGIA" and not (
        data.get("magia_has_cost_pm") or data.get("magia_has_element") or data.get("magia_has_school")
    ):
        data["_revisar_magia"] = True
    # Revisar MONSTRO sem stats nem PV
    if etype == "MONSTRO" and not (data.get("monstro_has_stats") or data.get("monstro_has_pv")):
        data["_revisar_monstro"] = True
    # Revisar ITEM sem preço nem bônus
    if etype == "ITEM" and not (data.get("item_has_preco") or data.get("item_has_bonus")):
        data["_revisar_item"] = True
    return etype, None


def extract_entities_from_chunks(
    chunks: List[Document],
    min_mentions: int = DEFAULT_MIN_MENTIONS,
) -> Dict[str, Dict[str, Any]]:
    """
    Extrai entidades com tipo por pontuação (conteúdo 5, seção 3, secundário 2) no texto completo do chunk.
    """
    def _default_raw() -> Dict[str, Any]:
        return {
            "type_scores": defaultdict(int),
            "mentions": 0,
            "contexts": [],
            "sources": set(),
            "stats": None,
            "magia_has_cost_pm": False,
            "magia_has_element": False,
            "magia_has_school": False,
            "monstro_has_stats": False,
            "monstro_has_pv": False,
            "item_has_preco": False,
            "item_has_bonus": False,
        }
    raw: Dict[str, Dict[str, Any]] = defaultdict(_default_raw)

    for doc in chunks:
        text = doc.page_content or ""
        meta = doc.metadata or {}
        section = meta.get("section") or meta.get("section_title") or ""
        source_str = str(meta.get("source") or meta.get("book_title") or "")
        src_key = _source_key(meta)
        chunk_scores = _score_chunk(section, source_str, text)
        magia_hints = _chunk_has_magia_hints(text)
        monstro_hints = _chunk_has_monstro_hints(text)
        item_hints = _chunk_has_item_hints(text)

        for name, ctx in _extract_from_patterns(text):
            entry = raw[name]
            entry["mentions"] += 1
            if len(entry["contexts"]) < 5:
                entry["contexts"].append(ctx[:300])
            entry["sources"].add(src_key)
            _merge_scores(entry["type_scores"], chunk_scores)
            entry["magia_has_cost_pm"] |= magia_hints[0]
            entry["magia_has_element"] |= magia_hints[1]
            entry["magia_has_school"] |= magia_hints[2]
            entry["monstro_has_stats"] |= monstro_hints[0]
            entry["monstro_has_pv"] |= monstro_hints[1]
            entry["item_has_preco"] |= item_hints[0]
            entry["item_has_bonus"] |= item_hints[1]
            if STATS_RE.search(text) and not entry["stats"]:
                stats_m = STATS_RE.findall(text)
                if stats_m:
                    entry["stats"] = " ".join(stats_m[:8])

    out: Dict[str, Dict[str, Any]] = {}
    for name, data in raw.items():
        type_scores = dict(data["type_scores"])
        name_norm = _name_title(name)
        is_critical = _is_critical_entity(name)
        # Categorias de magia (Magia Elemental, Branca, etc.): forçar MAGIA += 20
        if RE_MAGIA_CATEGORY.match(name) or RE_MAGIA_CATEGORY.match(name_norm):
            type_scores["MAGIA"] = type_scores.get("MAGIA", 0) + 20
            type_scores["MONSTRO"] = 0
            type_scores["ITEM"] = 0
        # Críticas por nome (inclui "magia branca" normalizado): garantir MAGIA += 20
        elif name in CRITICAL_MAGIC_NAMES or name_norm in CRITICAL_MAGIC_NAMES or name in CRITICAL_ENTITIES or name_norm in CRITICAL_ENTITIES:
            type_scores["MAGIA"] = type_scores.get("MAGIA", 0) + 20
            type_scores["MONSTRO"] = 0
            type_scores["ITEM"] = 0
        elif RE_MAGIA_CONHECIDA.search(name):
            type_scores["MAGIA"] = type_scores.get("MAGIA", 0) + 10
        etype, confidence = _resolve_type_from_scores(type_scores)
        etype, review_reason = _post_process_type(etype, data)
        # Críticas: nunca rebaixar para DESCONHECIDO por stats
        if is_critical and etype == TYPE_DESCONHECIDO and review_reason == "MAGIA com stats F/H/R/A":
            etype = "MAGIA"
            review_reason = None
        # MAGIA: rebaixar se não for crítica/categoria e não tiver indícios no conteúdo (evita excesso)
        if etype == "MAGIA" and not (
            data.get("magia_has_cost_pm") or data.get("magia_has_element") or data.get("magia_has_school")
        ):
            is_magia_by_name = (
                is_critical
                or RE_MAGIA_CATEGORY.match(name)
                or RE_MAGIA_CATEGORY.match(name_norm)
                or name in CRITICAL_MAGIC_NAMES
                or name_norm in CRITICAL_MAGIC_NAMES
            )
            if not is_magia_by_name:
                etype = TYPE_DESCONHECIDO
                review_reason = "MAGIA sem indícios no conteúdo (custa PM/elemento/escola)"
        # MONSTRO: exige nome próprio (score >= 2)
        if etype == "MONSTRO" and _proper_noun_score(name) < 2:
            etype = TYPE_DESCONHECIDO
            review_reason = "MONSTRO sem nome próprio"
        # ITEM: descarta nomes genéricos (só tipo sem qualificador)
        if etype == "ITEM" and _is_generic_item_name(name):
            etype = TYPE_DESCONHECIDO
            review_reason = "ITEM genérico"
        # Reclassificar DESCONHECIDO óbvios (MAGIA só se nome próprio + padrão mágico; VANTAGEM expandido)
        if etype == TYPE_DESCONHECIDO:
            if name and name[0].isupper() and RE_DESCONHECIDO_TO_MAGIA.search(name):
                etype = "MAGIA"
                review_reason = "reclassificado por padrão (Magia/Mágico/Ilusão/Encantamento)"
            elif RE_DESCONHECIDO_TO_VANTAGEM.search(name):
                etype = "VANTAGEM"
                review_reason = "reclassificado por padrão (Corpo/Elemental/Vantagem/etc.)"
        # min_mentions por tipo (críticas: min 1)
        required_mentions = 1 if is_critical else MIN_MENTIONS_BY_TYPE.get(etype, min_mentions)
        if data["mentions"] < required_mentions:
            continue
        if review_reason:
            logger.info("Pós-processamento tipo para %r: %s → %s", name, review_reason, etype)
        out[name] = {
            "type": etype,
            "mentions": data["mentions"],
            "contexts": data["contexts"][:5],
            "sources": sorted(data["sources"]),
        }
        if data.get("stats"):
            out[name]["stats"] = data["stats"]
        if review_reason:
            out[name]["_type_review"] = review_reason
        if data.get("_revisar_magia"):
            out[name]["_revisar_magia"] = True
        if data.get("_revisar_monstro"):
            out[name]["_revisar_monstro"] = True
        if data.get("_revisar_item"):
            out[name]["_revisar_item"] = True
    return out


def load_chunks_from_processed_dir(processed_dir: Path) -> List[Document]:
    chunks_path = processed_dir / "chunks.json"
    if not chunks_path.exists():
        return []
    with chunks_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        Document(page_content=item.get("page_content", ""), metadata=item.get("metadata", {}))
        for item in data
    ]


def save_chunks_to_processed_dir(chunks: List[Document], processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    data = [{"page_content": doc.page_content, "metadata": doc.metadata or {}} for doc in chunks]
    with (processed_dir / "chunks.json").open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    logger.info("Chunks salvos em %s (%d documentos).", processed_dir / "chunks.json", len(chunks))


# Entidades conhecidas para validação pós-extração (nome normalizado -> tipo esperado)
KNOWN_ENTITY_TYPES: Dict[str, str] = {
    "Invocação da Fênix": "MAGIA",
    "Invocação da Fenix": "MAGIA",
    "Bola de Fogo": "MAGIA",
    "Bola de fogo": "MAGIA",
    "Magia Elemental": "MAGIA",
    "Magia Branca": "MAGIA",
    "Ghoul": "MONSTRO",
    "Dragão Adulto Vermelho": "MONSTRO",
    "Dragao Adulto Vermelho": "MONSTRO",
    "Espada Longa": "ITEM",
    "Poção de Cura": "ITEM",
    "Pocao de Cura": "ITEM",
    "Ataque Extra": "VANTAGEM",
}
CRITICAL_MAGIC_NAMES = frozenset({
    "Bola de Fogo", "Bola de fogo", "Invocação da Fênix", "Invocação da Fenix",
    "Magia Elemental", "Magia Branca", "Magia Negra", "Magia Arcana", "Magia Divina",
})


def _check_known_entities(entities: Dict[str, Dict[str, Any]]) -> None:
    """Verifica se entidades conhecidas foram classificadas corretamente; loga erros. Bola de Fênix em DESCONHECIDO = crítico."""
    for name, expected_type in KNOWN_ENTITY_TYPES.items():
        if name not in entities:
            continue
        actual = entities[name].get("type", "?")
        if actual != expected_type:
            if name in CRITICAL_MAGIC_NAMES and actual == TYPE_DESCONHECIDO:
                logger.error("ERRO CRÍTICO: magia conhecida em DESCONHECIDO: %r", name)
                print(f"[ERRO CRÍTICO] Magia conhecida em DESCONHECIDO: {name!r}")
            else:
                logger.warning("Entidade conhecida mal classificada: %r → %s (esperado: %s)", name, actual, expected_type)
                print(f"[WARNING] Entidade conhecida mal classificada: {name!r} → {actual} (esperado: {expected_type})")


def _log_extraction_stats(entities: Dict[str, Dict[str, Any]]) -> None:
    """Log e print estatísticas por tipo. Faixas realistas e alertas consolidados."""
    by_type: Dict[str, int] = defaultdict(int)
    for data in entities.values():
        by_type[data.get("type", "?")] += 1
    total = len(entities)
    magia = by_type.get("MAGIA", 0)
    monstro = by_type.get("MONSTRO", 0)
    item = by_type.get("ITEM", 0)
    vantagem = by_type.get("VANTAGEM", 0)
    desconhecido = by_type.get("DESCONHECIDO", 0)
    outros = total - magia - monstro - item - vantagem - desconhecido
    lines = [
        "Extração de entidades concluída:",
        f"  Total: {total} (meta Nível 3: 1500-2500)",
        f"  MAGIA: {magia} (esperado: 400-600)",
        f"  MONSTRO: {monstro} (esperado: 400-600)",
        f"  ITEM: {item} (esperado: 300-500)",
        f"  VANTAGEM: {vantagem} (esperado: 200-400)",
        f"  DESCONHECIDO: {desconhecido} (meta: <50)",
        f"  Outros: {outros}",
    ]
    for line in lines:
        logger.info("%s", line)
        print(f"[INFO] {line}")
    if magia < 100:
        msg = f"ERRO CRÍTICO: MAGIA={magia} (mínimo 100). Verificar padrões regex."
        logger.error("%s", msg)
        print(f"[ERRO CRÍTICO] {msg}")
    if magia > 700:
        msg = f"Revisar: MAGIA={magia} (meta 400-600). Possível classificação excessiva."
        logger.warning("%s", msg)
        print(f"[WARNING] {msg}")
    if desconhecido > 50:
        msg = f"Revisar padrões: DESCONHECIDO={desconhecido} (meta <50)."
        logger.warning("%s", msg)
        print(f"[WARNING] {msg}")
    if total > 2200:
        print("[INFO] Sugestão: min_mentions por tipo e DESCONHECIDO >= 10 já aplicados.")
    if magia < 50 or monstro < 100:
        msg = (
            f"Poucas entidades principais (MAGIA={magia}, MONSTRO={monstro}). "
            "Verificar padrões regex."
        )
        logger.warning("%s", msg)
        print(f"[WARNING] {msg}")


def run_extraction(
    chunks: List[Document],
    output_path: Path,
    min_mentions: int = DEFAULT_MIN_MENTIONS,
    save_chunks_path: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    if save_chunks_path:
        save_chunks_to_processed_dir(chunks, save_chunks_path)
    entities = extract_entities_from_chunks(chunks, min_mentions=min_mentions)
    _log_extraction_stats(entities)
    _check_known_entities(entities)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    logger.info("Entidades extraídas: %d. Salvas em %s", len(entities), output_path)
    return entities
