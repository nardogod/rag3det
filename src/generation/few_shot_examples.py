"""
Exemplos Few-Shot para o consultor 3D&T.

- 3 pares (pergunta + contexto + resposta ideal) para o LLM seguir o formato.
"""
from __future__ import annotations

FEW_SHOT_EXAMPLES = """
EXEMPLO 1:

Pergunta: O que é Atributo no 3D&T?
Contexto: [1] [3D&T 3ª Edição | Atributos | pág. 12]
Atributos definem as características do personagem: Força, Agilidade, etc. Cada um varia de 1 a 5 na criação.

Resposta esperada:
📜 REGRA LITERAL: "Atributos definem as características do personagem: Força, Agilidade, etc. Cada um varia de 1 a 5 na criação."
🎲 EXPLICAÇÃO: Atributos são as características numéricas do personagem (1 a 5), como Força e Agilidade.
📊 MECÂNICA: Valores de 1 a 5; usados em testes (rolagem + modificadores).
📖 FONTE PRIMÁRIA: 3D&T 3ª Edição, página 12
⚠️ LIMITAÇÃO: (nenhuma)

---

EXEMPLO 2:

Pergunta: Como funciona magia elemental de fogo?
Contexto: [1] [Manual 3D&T | Magias Elementais | pág. 45]
Magias elementais de fogo causam dano por chamas. O conjurador faz um teste de Vontade; o alvo pode resistir com teste de Reflexos.

Resposta esperada:
📜 REGRA LITERAL: "Magias elementais de fogo causam dano por chamas. O conjurador faz um teste de Vontade; o alvo pode resistir com teste de Reflexos."
🎲 EXPLICAÇÃO: Magia de fogo causa dano; conjurador rola Vontade, alvo pode resistir com Reflexos.
📊 MECÂNICA: Teste Vontade (conjurador) vs Reflexos (alvo); dano conforme regras de fogo.
📖 FONTE PRIMÁRIA: Manual 3D&T, página 45
⚠️ LIMITAÇÃO: (nenhuma)

---

EXEMPLO 3:

Pergunta: O que são mortos-vivos?
Contexto: [1] [Bestiário 3D&T | Criaturas | pág. 78]
Mortos-vivos são criaturas reanimadas por necromancia. Não possuem Constituição; usam atributos especiais conforme o tipo (esqueleto, zumbi, etc.).

Resposta esperada:
📜 REGRA LITERAL: "Mortos-vivos são criaturas reanimadas por necromancia. Não possuem Constituição; usam atributos especiais conforme o tipo (esqueleto, zumbi, etc.)."
🎲 EXPLICAÇÃO: São criaturas reanimadas; sem Constituição; regras por tipo (esqueleto, zumbi).
📊 MECÂNICA: Conforme tipo (atributos especiais no bestiário).
📖 FONTE PRIMÁRIA: Bestiário 3D&T, página 78
⚠️ LIMITAÇÃO: (nenhuma)
""".strip()


def get_few_shot_block() -> str:
    """Retorna o bloco de exemplos para injetar no system prompt."""
    return FEW_SHOT_EXAMPLES
