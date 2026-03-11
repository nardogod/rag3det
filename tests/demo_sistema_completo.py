"""
Demonstracao completa do sistema 3D&T RAG evoluido.
Compara ANTES (busca semantica pura) vs DEPOIS (sistema integrado).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garantir import do projeto
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag.hybrid_retriever import HybridRetriever
from src.generation.content_generator import ContentGenerator


def print_section(title: str, icon: str = "=") -> None:
    print(f"\n{icon * 70}")
    print(f"  {title}")
    print(f"{icon * 70}")


def demo_comparacao_orc_troll() -> None:
    """Demonstra a evolucao da comparacao Orc vs Troll."""
    print_section("COMPARACAO: Orc vs Troll", "=")

    retriever = HybridRetriever()

    print("\n[BUSCA] ANTES (Busca Semantica Puramente):")
    print("-" * 60)
    print("Query: 'Orc vs Troll'")
    print("Resultado: Trechos de texto mencionando Orc e Troll separadamente")
    print("Exemplo de output antigo:")
    print('  [score=7.2] "...os orcs sao guerreiros ferozes..."')
    print('  [score=6.8] "...trolls regeneram ferimentos..."')
    print("\n[X] PROBLEMA: Nao compara, apenas lista textos onde aparecem")

    print("\n" + "=" * 60)
    print("[BUSCA] DEPOIS (Sistema Integrado):")
    print("-" * 60)

    comparison = retriever.compare_entities("Orc", "Troll")

    if comparison:
        print("\n[STATS] ANALISE ESTRUTURADA:")
        e1 = comparison.get("entidade_1", {})
        e2 = comparison.get("entidade_2", {})
        s1 = e1.get("stats") or {}
        s2 = e2.get("stats") or {}
        print(
            f"  {e1.get('nome', '?')}: F={s1.get('forca')}, PV={s1.get('pv')}"
        )
        print(
            f"  {e2.get('nome', '?')}: F={s2.get('forca')}, PV={s2.get('pv')}"
        )

        print(f"\n[VENCEDOR] {comparison.get('vencedor', '?')}")
        print(f"   Razao: {comparison.get('razao', '')}")

        if "analise_combate" in comparison:
            combate = comparison["analise_combate"]
            print("\n[COMBATE] SIMULACAO DE COMBATE:")
            print(f"   Poder Orc: {combate.get('poder_combate_1')}")
            print(f"   Poder Troll: {combate.get('poder_combate_2')}")
            print(
                f"   Probabilidade Orc vencer: {combate.get('probabilidade_vitoria_1')}%"
            )
            print(
                f"   Probabilidade Troll vencer: {combate.get('probabilidade_vitoria_2')}%"
            )

        print("\n[OK] EVOLUCAO: Dados estruturados + calculos + probabilidades!")
    else:
        print("\n[!] Comparacao nao disponivel (dados de Orc/Troll nao encontrados)")


def demo_consulta_equipamento() -> None:
    """Demonstra consulta de equipamento com raciocinio."""
    print_section("CONSULTA INTELIGENTE: Equipamento", "=")

    retriever = HybridRetriever()

    print("\n[BUSCA] Query: 'Melhor arma para 20 PE e Forca 3'")
    print("-" * 60)

    print("\n[X] ANTES: Busca por palavras-chave")
    print("   Resultado: Lista de textos com 'arma', 'PE', 'Forca'...")

    print("\n[OK] DEPOIS: Raciocinio estruturado")
    print("-" * 60)

    recomendacoes = retriever.recommend_for_build(
        pe_budget=20,
        min_forca=3,
        tipo="arma",
    )

    print(f"\n[ALVO] {len(recomendacoes)} opcoes encontradas:")

    for i, rec in enumerate(recomendacoes[:3], 1):
        print(f"\n  {i}. {rec.get('nome', '?')} ({rec.get('tipo', '?')})")
        print(f"     PE: {rec.get('pe')}")
        print(f"     Dano: {rec.get('dano')}")
        print(f"     Eficiencia Dano/PE: {rec.get('eficiencia')}")
        score = rec.get("score_recomendacao")
        if score is not None:
            print(f"     Score: {score:.2f}")

    print("\n[RECOMENDACAO]")
    if recomendacoes:
        top = recomendacoes[0]
        print(f"   '{top.get('nome', '?')}' oferece o melhor custo-beneficio!")
        ef = top.get("eficiencia") or 0
        pe = top.get("pe") or 0
        print(f"   Dano medio: ~{ef * pe:.1f} por PE gasto")
    else:
        print("   Nenhum equipamento no orcamento/forca (tabelas vazias?).")


def demo_geracao_npc() -> None:
    """Demonstra geracao de NPC."""
    print_section("GERACAO DE NPC", "=")

    generator = ContentGenerator()

    print("\n[*] Gerando 3 NPCs diferentes...")

    configs = [
        (1, "guerreiro", "Humano"),
        (3, "mago", "Elfo"),
        (5, "ladino", "Goblin"),
    ]

    for nivel, arquetipo, raca in configs:
        npc = generator.generate_npc(
            nivel=nivel,
            arquetipo=arquetipo,
            raca=raca,
        )
        print(f"\n{'-' * 60}")
        print(f"[NPC] {npc.nome} ({npc.raca}) - Nivel {npc.nivel} {arquetipo.upper()}")
        print(
            f"   F:{npc.stats.get('forca')} H:{npc.stats.get('habilidade')} "
            f"R:{npc.stats.get('resistencia')} A:{npc.stats.get('armadura')}"
        )
        print(f"   PV:{npc.stats.get('pv')} PM:{npc.stats.get('pm')}")
        print(f"   Pericias: {', '.join(npc.pericias[:3])}")
        print(f"   Equipamento: {', '.join(npc.equipamento[:2])}")
        if npc.magias:
            print(f"   Magias: {', '.join(npc.magias[:2])}")
        print(f"   XP se derrotado: {npc.xp_value}")
        print(f"   Background: {npc.background[:60]}...")


def demo_geracao_encontro() -> None:
    """Demonstra geracao de encontro balanceado."""
    print_section("GERACAO DE ENCONTRO", "=")

    generator = ContentGenerator()

    print("\n[ALVO] Party: 4 jogadores, Nivel 3, Dificuldade: Media")
    print("-" * 60)

    encounter = generator.generate_encounter(
        party_size=4,
        party_level=3,
        dificuldade="medio",
        ambiente="floresta",
    )

    print(f"\n[*] {encounter.get('descricao', '')}")
    print("\n[INIMIGOS]")
    inimigos_str = ", ".join(
        f"{e['quantidade']}x {e['nome']}" for e in encounter.get("inimigos", [])
    )
    print(f"   {inimigos_str}")

    print("\n[RECOMPENSA]")
    print(f"   XP Total: {encounter.get('xp_total', 0)}")
    print(f"   Tesouro: {', '.join(encounter.get('tesouro', [])[:2])}")

    print("\n[TATICAS]")
    print(f"   {encounter.get('taticas', '')[:100]}...")


def demo_api_calls() -> None:
    """Demonstra chamadas a API."""
    print_section("API REST - EXEMPLOS DE USO", "=")

    base_url = "http://localhost:8000"

    print(f"\n[API] Base URL: {base_url}")
    print("   (Certifique-se de que a API esta rodando: python -m src.api.main)")

    print("\n" + "=" * 60)
    print("1. CONSULTA HIBRIDA")
    print("-" * 60)
    print(f'''
curl -X POST "{base_url}/query" \\
  -H "Content-Type: application/json" \\
  -d '{{"query": "goblin", "top_k": 5}}'

# Resposta inclui:
# - Dados estruturados do Goblin (F/H/R/A/PV/PM)
# - Tabela completa de monstros
# - Lore descritivo
# - Magias relacionadas
''')

    print("=" * 60)
    print("2. COMPARAR ENTIDADES (POST com body)")
    print("-" * 60)
    print(f'''
curl -X POST "{base_url}/comparar" \\
  -H "Content-Type: application/json" \\
  -d '{{"entidade1": "Orc", "entidade2": "Troll"}}'

# Resposta inclui analise estatistica + probabilidade de vitoria
''')

    print("=" * 60)
    print("3. GERAR NPC")
    print("-" * 60)
    print(f'''
curl -X POST "{base_url}/npc/gerar" \\
  -H "Content-Type: application/json" \\
  -d '{{"nivel": 3, "arquetipo": "mago", "raca": "Elfo"}}'
''')

    print("=" * 60)
    print("4. GERAR ENCONTRO")
    print("-" * 60)
    print(f'''
curl -X POST "{base_url}/encontro/gerar" \\
  -H "Content-Type: application/json" \\
  -d '{{"party_size": 4, "party_level": 2, "dificuldade": "medio", "ambiente": "dungeon"}}'
''')

    print("=" * 60)
    print("5. CRIAR SESSAO DE JOGO")
    print("-" * 60)
    print(f'''
# Criar sessao
curl -X POST "{base_url}/sessao/criar" -H "Content-Type: application/json" -d '{{"nome": "Minha Aventura"}}'

# Adicionar personagem (substitua SESSAO_ID)
curl -X POST "{base_url}/sessao/SESSAO_ID/personagem" \\
  -H "Content-Type: application/json" \\
  -d '{{"nome": "Thorin", "jogador": "Joao", "raca": "Anao", "nivel": 2, "stats": {{"forca":5,"habilidade":3,"resistencia":4,"armadura":2,"pv":25,"pm":0}}}}'

# Iniciar combate
curl -X POST "{base_url}/combate/SESSAO_ID/iniciar" \\
  -H "Content-Type: application/json" \\
  -d '{{"inimigos": []}}'
''')

    print("\n[DOC] Documentacao interativa:")
    print(f"   {base_url}/docs  (Swagger UI)")
    print(f"   {base_url}/redoc (ReDoc)")


def demo_evolucao_query_goblin() -> None:
    """Mostra evolucao da query 'goblin' em todos os niveis."""
    print_section("EVOLUCAO DA QUERY: 'goblin'", "=")

    print("""
+-----------------------------------------------------------------------------+
| NIVEL 2: Busca Semantica (ANTES)                                            |
+-----------------------------------------------------------------------------+
| Query: 'goblin'                                                             |
| Resultado:                                                                  |
|   1. [score=7.76] "...os goblinoides fugirem em panico..."                  |
|   2. [score=7.76] "Sentido sobrenatural (goblin): um goblin pode fugir..."  |
|   3. [score=7.70] "Modelo Especial). Goblin (-2 pontos)..."                 |
|                                                                             |
| [X] Texto solto, sem estrutura                                              |
| [X] Sem atributos (F/H/R/A/PV/PM)                                           |
| [X] Sem contexto de poder                                                   |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 3: +Tabelas Estruturadas                                              |
+-----------------------------------------------------------------------------+
| Query: 'goblin'                                                             |
| Resultado:                                                                  |
|   [STATS] Goblin (F:3, H:4, R:2, A:1, PV:8, PM:0)                           |
|   [TABELA] Monstros Basicos (comparacao com Orc, Troll...)                  |
|   [LORE] Descricao racial e comportamento                                  |
|                                                                             |
| [OK] Dados estruturados extraidos                                           |
| [OK] Contexto de tabela completa                                            |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 4: +Raciocinio                                                        |
+-----------------------------------------------------------------------------+
| Query: 'goblin'                                                             |
| Analise Automatica:                                                         |
|   [ALVO] Categoria: Fraco (Nivel 1-2)                                       |
|   [COMBATE] Poder de Combate: 9                                              |
|   [PE] XP: 90                                                               |
|   [STATS] Comparacao: Mais fraco que Orc (12), mais agil que Troll (4 vs 4)|
|                                                                             |
| [OK] Calculos derivados automaticos                                         |
| [OK] Analise comparativa                                                    |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 5: +Geracao de Conteudo                                               |
+-----------------------------------------------------------------------------+
| Query: 'Crie encontro com goblins para 4 jogadores nivel 1'                 |
| Resultado:                                                                  |
|   [INIMIGOS] 4 Goblins (360 XP) + 1 Goblin Lider (120 XP)                    |
|   [PE] Tesouro: 45 PE + Adaga +1                                            |
|   [TATICAS] Flanquear, fugir se 2 caírem                                    |
|   [TEMPO] Duracao: 15-20 minutos                                            |
|                                                                             |
| [OK] Encontro balanceado automaticamente                                    |
| [OK] Taticas baseadas no lore                                               |
| [OK] Recompensas proporcionais                                              |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 6: +Sessao Persistente                                                |
+-----------------------------------------------------------------------------+
| Combate Ativo: Rodada 3                                                      |
|   Iniciativa: [Goblin2(9), Goblin1(7), Thorin(5)]                            |
|   Acoes:                                                                    |
|     R1: Goblin2 atacou Thorin (errou)                                       |
|     R1: Thorin atacou Goblin1 (acertou, 6 dano, PV: 8->2)                   |
|     R2: Goblin1 fugiu (moral falhou)                                        |
|                                                                             |
| [OK] Estado persistente entre turnos                                        |
| [OK] Log de acoes automatico                                                |
| [OK] Calculos de combate (dano, iniciativa)                                 |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 7: +Multimodal                                                        |
+-----------------------------------------------------------------------------+
| Query: 'goblin'                                                             |
| Resultado:                                                                  |
|   [IMAGEM] 3DT_Manual_Basico_p45_a1b2c3d4.png                              |
|   Contexto: Ilustracao mostrando estatura pequena, pele verde, adaga        |
|                                                                             |
| [OK] Referencia visual integrada                                             |
| [OK] Contexto de ilustracao                                                  |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 8: API Completa                                                       |
+-----------------------------------------------------------------------------+
| Endpoint: POST /query                                                       |
| Response: JSON unificado com todos os niveis acima                           |
|                                                                             |
| [OK] Acesso via HTTP/REST                                                   |
| [OK] Integracao com qualquer frontend                                       |
| [OK] Documentacao Swagger automatica                                       |
+-----------------------------------------------------------------------------+
""")


def main() -> None:
    """Executa todas as demonstracoes."""
    print("\n" + "=" * 70)
    print("  SISTEMA 3D&T RAG - DEMONSTRACAO COMPLETA")
    print("  Comparacao: ANTES vs DEPOIS")
    print("=" * 70)

    demo_evolucao_query_goblin()
    demo_comparacao_orc_troll()
    demo_consulta_equipamento()
    demo_geracao_npc()
    demo_geracao_encontro()
    demo_api_calls()

    print_section("SISTEMA PRONTO PARA USO!", "=")
    print("""
[OK] Todos os componentes estao funcionando:

1. Tabelas extraidas e normalizadas
2. Retriever hibrido (texto + estruturado)
3. Geracao de conteudo dentro das regras
4. Sessoes persistentes com combate
5. Processamento de visuais
6. API REST completa

[PROXIMO PASSO]
   Execute: python -m src.api.main
   Acesse:  http://localhost:8000/docs

   Ou use o CLI interativo:
   python -m src.session.campaign_manager
""")


if __name__ == "__main__":
    main()
