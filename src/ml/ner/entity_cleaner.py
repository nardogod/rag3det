"""
Filtros de qualidade para entidades extraídas do corpus 3D&T.

Elimina: "O jogo", "No entanto", "RPG", siglas genéricas, só minúsculas, metadados.
Requisitos: tamanho 4–60, pelo menos uma palavra 3+ chars, substantivo próprio (Title Case ou CAIXA ALTA).
"""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple

# Siglas conhecidas 3D&T (permitidas com 2–3 caracteres)
KNOWN_ACRONYMS = frozenset({"PM", "PV", "FA", "FD", "PE", "PV"})

# Stopwords PT-BR expandidas
STOPWORDS = frozenset({
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "da", "do", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "sob", "sobre", "entre", "até", "após",
    "e", "ou", "mas", "que", "se", "porque", "pois", "logo", "assim",
    "ele", "ela", "eles", "elas", "isso", "isto", "aquilo", "eu", "tu", "você", "nós", "vós",
    "é", "são", "foi", "foram", "será", "serão", "era", "eram", "ser", "estar",
    "não", "sim", "já", "ainda", "só", "também", "bem", "mal", "mais", "menos", "muito", "pouco",
    "porém", "entretanto", "todavia", "então", "portanto", "donde", "qual", "quais",
    "função", "além", "exemplo", "demais", "próprio", "própria",
    "rpg", "jogo", "regra", "regras", "sistema", "manual", "livro", "livros",
})

# Expressões inteiras que são sempre inválidas (frases, não nomes)
INVALID_PHRASES = frozenset({
    "no entanto", "além disso", "por exemplo", "ou seja", "isto é",
    "o jogo", "a regra", "o sistema", "a partir",
    "na verdade", "na prática", "em geral", "a seguir", "de acordo", "em resumo",
    "se falhar", "se passar", "veja abaixo", "veja adiante",
})

# Prefixos que indicam início com artigo/preposição (excluir "O Nome", "A Coisa", "De Algo")
STARTS_WITH_STOPWORD = re.compile(
    r"^\s*(o\s+|a\s+|os\s+|as\s+|um\s+|uma\s+|de\s+|da\s+|do\s+|em\s+|no\s+|na\s+|e\s+|ou\s+)",
    re.IGNORECASE,
)

# Padrões de EXCLUSÃO
ONLY_1_2_LETTERS = re.compile(r"^[A-Za-z]{1,2}$")
ONLY_LOWERCASE = re.compile(r"^[a-záéíóúâêôãõç\s\-']+$")
ONLY_NUMBERS_PUNCT = re.compile(r"^[0-9\W]+$")
METADATA_NOISE = re.compile(
    r"\b(pg\.?|página|manual|pdf|m3d|alpha|biblioteca|elfica|digital)\b",
    re.IGNORECASE,
)

MIN_LEN = 4
MAX_LEN = 60
MIN_WORD_LEN = 3
CONTEXT_MIN_CHARS = 60
MIN_CONTEXTS_IF_NO_SUBSTANTIVE = 1

# Razões para estatísticas
REASON_SIZE = "tamanho"
REASON_STOPWORDS = "stopwords"
REASON_PATTERN = "padrão"
REASON_PROPER_NOUN = "substantivo"
REASON_CONTEXT = "contexto"


def _has_word_min_length(name: str, min_len: int = MIN_WORD_LEN) -> bool:
    """True se pelo menos uma palavra tem min_len+ caracteres."""
    words = (name or "").split()
    return any(len(w) >= min_len for w in words)


def _is_stopword_or_phrase(name: str) -> bool:
    """True se o nome é stopword, frase inválida ou só stopwords."""
    n = (name or "").strip().lower()
    if not n:
        return True
    if n in STOPWORDS or n in INVALID_PHRASES:
        return True
    words = n.split()
    if all(w in STOPWORDS for w in words):
        return True
    return False


def _invalid_size_or_structure(name: str) -> bool:
    """True se tamanho fora do intervalo ou estrutura inválida."""
    n = name.strip()
    if not n:
        return True
    # Siglas conhecidas podem ter 2 chars
    if n.upper() in KNOWN_ACRONYMS:
        return False
    if len(n) < MIN_LEN or len(n) > MAX_LEN:
        return True
    if not _has_word_min_length(n):
        return True
    if ONLY_NUMBERS_PUNCT.match(n):
        return True
    return False


def _invalid_exclusion_patterns(name: str) -> bool:
    """True se bate em padrões de exclusão (regex)."""
    n = name.strip()
    if ONLY_1_2_LETTERS.match(n) and n.upper() not in KNOWN_ACRONYMS:
        return True
    if ONLY_LOWERCASE.match(n) and len(n) >= MIN_LEN:
        return True
    if ONLY_NUMBERS_PUNCT.match(n):
        return True
    if METADATA_NOISE.search(n):
        return True
    # Permitir "O Nome", "A Coisa" quando o resto é substantivo próprio (ex.: "O Grendel")
    if STARTS_WITH_STOPWORD.match(n):
        rest = re.sub(r"^\s*(?:o|a|os|as|um|uma|de|da|do|em|no|na|e|ou)\s+", "", n, count=1, flags=re.IGNORECASE).strip()
        if rest and _is_proper_noun(rest):
            return False
        return True
    return False


def _is_proper_noun(name: str) -> bool:
    """
    Heurística: deve ter pelo menos uma palavra em Title Case ou ser TODO EM MAIÚSCULAS.
    Exceção: artigos/preposições em nomes compostos ("Invocação da Fênix").
    """
    n = name.strip()
    if not n:
        return False
    words = n.split()
    allowed_lower = {"de", "da", "do", "dos", "das", "e", "ou", "o", "a", "os", "as"}
    has_title_or_upper = False
    for w in words:
        if not w:
            continue
        if w.lower() in allowed_lower:
            continue
        if w.isupper() and len(w) >= 2:
            has_title_or_upper = True
            break
        if w[0].isupper():
            has_title_or_upper = True
            break
    return has_title_or_upper


def _context_ok(contexts: list, data: Dict[str, Any]) -> bool:
    """
    Deve ter: pelo menos 1 menção em contexto
    OU descrição substantiva (>= CONTEXT_MIN_CHARS em algum contexto)
    OU stats/propriedades identificáveis.
    Entidades com 4+ menções são aceitas (extração já filtrou por relevância).
    """
    ctx_list = contexts or []
    if data.get("mentions", 0) >= 4:
        return True
    if len(ctx_list) >= MIN_CONTEXTS_IF_NO_SUBSTANTIVE:
        return True
    for ctx in ctx_list:
        if ctx and len(ctx.strip()) >= CONTEXT_MIN_CHARS:
            return True
    if data.get("stats"):
        return True
    if data.get("type") == "MONSTRO":
        return True
    return False


def _context_is_only_stats(contexts: list) -> bool:
    """True se todos os contextos são basicamente só stats sem descrição."""
    for ctx in (contexts or []):
        if not ctx or len(ctx) < 30:
            continue
        if re.search(r"[a-záéíóúâêôãõç]{5,}", ctx, re.IGNORECASE):
            return False
    return True


# Entidades no top 1400 (min_mentions=4) são de alta confiança; só rejeitamos stopwords/tamanho/padrão
MIN_MENTIONS_FAST_PATH = 4


def classify_entity(
    name: str,
    data: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Classifica entidade como "valid" ou "suspect" e retorna razão (para suspect).

    Retorna ( "valid" | "suspect", reason_string ).
    """
    if _is_stopword_or_phrase(name):
        return "suspect", REASON_STOPWORDS
    if _invalid_size_or_structure(name):
        return "suspect", REASON_SIZE
    # Alta confiança: 4+ menções (top 1400) — aceita sem checar padrão/substantivo/contexto
    if data.get("mentions", 0) >= MIN_MENTIONS_FAST_PATH:
        return "valid", ""
    if _invalid_exclusion_patterns(name):
        return "suspect", REASON_PATTERN
    if not _is_proper_noun(name):
        return "suspect", REASON_PROPER_NOUN
    contexts = data.get("contexts") or []
    if not contexts:
        return "suspect", REASON_CONTEXT
    if not _context_ok(contexts, data):
        return "suspect", REASON_CONTEXT
    # Rejeitar só quando contexto é só stats E tipo é genérico (DESCONHECIDO/ENTIDADE)
    if _context_is_only_stats(contexts) and data.get("type") in ("DESCONHECIDO", "ENTIDADE", None):
        return "suspect", REASON_CONTEXT
    return "valid", ""


def clean_entities(
    entities: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, int]]:
    """
    Separa entidades em válidas e suspeitas e retorna estatísticas por razão.

    Retorna (valid_entities, suspect_entities, stats).
    stats: { "tamanho": N, "stopwords": N, "padrão": N, "substantivo": N, "contexto": N }.
    """
    valid: Dict[str, Dict[str, Any]] = {}
    suspect: Dict[str, Dict[str, Any]] = {}
    stats: Dict[str, int] = {
        REASON_SIZE: 0,
        REASON_STOPWORDS: 0,
        REASON_PATTERN: 0,
        REASON_PROPER_NOUN: 0,
        REASON_CONTEXT: 0,
    }
    for name, data in entities.items():
        kind, reason = classify_entity(name, data)
        if kind == "valid":
            valid[name] = data
        else:
            suspect[name] = {**data, "_reason": reason}
            if reason in stats:
                stats[reason] += 1
    return valid, suspect, stats
