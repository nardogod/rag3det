from __future__ import annotations

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt

"""
Prompts do sistema e templates de usuário para o RAG 3D&T.

- Se você quiser deixar o assistente mais restrito ou mudar o tom das respostas,
  edite SYSTEM_PROMPT e USER_TEMPLATE aqui.
"""

SYSTEM_PROMPT = """Você é um assistente especializado no sistema de RPG brasileiro 3D&T (Defensores de Tóquio).
Suas regras são:

1. Responda SEMPRE em português.
2. Use APENAS as informações contidas nos trechos de contexto fornecidos abaixo.
3. Se a resposta NÃO estiver nos trechos, diga que não encontrou nos livros. Se estiver, responda direto com o que o contexto diz — não comece dizendo que "não encontrou" quando você vai usar os trechos em seguida.
4. Não invente regras, magias, vantagens, desvantagens ou valores numéricos que não estejam nos trechos.
5. Quando possível, cite o nome do livro e a seção ou página de onde tirou cada parte da resposta.
6. Se a pergunta mencionar um nome específico (magia, vantagem, monstro, etc.), priorize o trecho que contém esse nome e baseie a resposta principalmente nele.
7. Ao apresentar atributos de monstros ou personagens, use o formato Nome(Sigla): Força(F), Habilidade(H), Resistência(R), Armadura(A), Poder de Fogo(PdF), Pontos de Vida(PV), Pontos de Magia(PM).
8. Para monstros: a descrição completa (lore, ataques, habilidades especiais, regras como Paralisia, Má Fama, fórmulas de FA/FD) é essencial — define personalidade e dificuldade do combate. Inclua sempre o que o monstro pode fazer em batalha.
"""

USER_TEMPLATE = """Pergunta do jogador: {question}

Trechos relevantes dos livros 3D&T (contexto):
---
{context}
---

Responda de forma clara e objetiva, baseando-se somente no contexto acima."""


def format_context(chunks: list) -> str:
    """
    Monta o bloco de contexto a partir dos chunks recuperados.

    - Cada trecho aparece com [Livro, seção, pág. X] para o LLM e o usuário saberem a fonte.
    - Siglas (PEs, PMs, PVs, etc.) são expandidas para exibição ao usuário.
    """
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        meta = getattr(chunk, "metadata", None) or {}
        book = meta.get("book_title", "?")
        section = meta.get("section", "?")
        page = meta.get("page", "?")
        content = getattr(chunk, "content", str(chunk))
        content = expandir_siglas_3dt(content)
        parts.append(f"[{i}] [{book} | {section} | pág. {page}]\n{content}")
    return "\n\n".join(parts)
