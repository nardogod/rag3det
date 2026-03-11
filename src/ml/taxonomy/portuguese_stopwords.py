"""
Stopwords PT-BR para TF-IDF e nomeação de clusters (evita "de_nao_que_os_ou").
"""
from __future__ import annotations

# Lista para uso em TfidfVectorizer(stop_words=...) ou filtro manual
STOPWORDS_PT_BR = frozenset({
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "da", "do", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "sob", "sobre", "entre", "até", "após",
    "e", "ou", "mas", "que", "se", "porque", "quando", "como", "onde",
    "ele", "ela", "eles", "elas", "isso", "isto", "aquilo", "eu", "tu", "nós", "vós",
    "é", "são", "foi", "foram", "será", "serão", "ser", "estar", "está", "estão",
    "não", "sim", "já", "ainda", "só", "também", "mais", "menos", "muito", "pouco",
    "porém", "entretanto", "todavia", "assim", "então", "logo", "portanto",
    "donde", "donde", "qual", "quais", "cujo", "cuja", "cujos", "cujas",
    "outro", "outra", "outros", "outras", "mesmo", "mesma", "mesmos", "mesmas",
    "todo", "toda", "todos", "todas", "algum", "alguma", "alguns", "algumas",
    "nenhum", "nenhuma", "cada", "qualquer", "certo", "certa",
    "função", "além", "exemplo", "demais", "próprio", "própria",
})


def is_stopword(word: str) -> bool:
    """True se a palavra (minúscula) é stopword."""
    return (word or "").strip().lower() in STOPWORDS_PT_BR


def filter_stopwords_from_terms(terms: list[str], min_len: int = 2) -> list[str]:
    """Remove stopwords e termos muito curtos da lista de termos."""
    return [t for t in terms if t and len(t) >= min_len and not is_stopword(t)]
