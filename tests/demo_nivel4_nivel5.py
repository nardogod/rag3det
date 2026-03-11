"""
Demonstracao integrada: Nivel 4 (Raciocinio) + Nivel 5 (Geracao Inteligente)
Mostra a evolucao do sistema com analise contextual e geracao adaptativa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.generation.smart_generator import SmartGenerator
from src.rag.smart_reasoning import SmartReasoning, analisar_consulta


def print_header(text: str, icon: str = "=") -> None:
    print(f"\n{icon * 80}")
    print(f"  {text}")
    print(f"{icon * 80}")


def print_section(title: str) -> None:
    print(f"\n{'-' * 80}")
    print(f"[*] {title}")
    print("-" * 80)


def demo_nivel4_analise() -> None:
    """Demonstra Nivel 4: Analise Inteligente de Contexto."""
    print_header("NIVEL 4: RACIOCINIO INTELIGENTE", "=")

    reasoning = SmartReasoning()

    consultas_teste = [
        "goblin",
        "Orc vs Troll",
        "melhor arma para 20 PE e Forca 3",
        "quanto XP para nivel 5?",
        "crie encontro medio para 4 jogadores nivel 2",
        "2d6 de dano e bom?",
    ]

    for query in consultas_teste:
        print_section(f"Query: '{query}'")

        analise = reasoning.analisar(query)

        print(f"  [TIPO] {analise.tipo.value}")
        print(f"  [INTENCAO] {analise.intencao_principal}")

        if analise.entidades:
            print(f"  [ENTIDADES] {', '.join(analise.entidades)}")

        if analise.parametros:
            print(f"  [PARAMETROS] {analise.parametros}")

        print(f"  [SUGESTAO] {analise.sugestao_acao}")

        if analise.tipo.value != "desconhecido":
            print("\n  [RECOMENDACAO]")
            rec = reasoning.gerar_recomendacao(analise, [])
            print(f"    Titulo: {rec.titulo}")
            desc = (rec.descricao or "")[:100]
            print(f"    Descricao: {desc}...")
            if rec.calculos:
                print(f"    Calculos: {list(rec.calculos.keys())}")


def demo_nivel5_geracao() -> None:
    """Demonstra Nivel 5: Geracao Contextual Inteligente."""
    print_header("NIVEL 5: GERACAO CONTEXTUAL INTELIGENTE", "=")

    cache = carregar_entity_cache()
    generator = SmartGenerator(entity_cache=cache)

    print_section("Geracao 1: NPC Inteligente")
    print("Query: 'crie um NPC mago nivel 3 para minha party'")

    resultado_npc = generator.gerar(
        "crie um NPC mago nivel 3",
        contexto={"party_level": 3, "tema": "elemental_fogo"},
    )

    if resultado_npc.get("tipo") == "npc":
        npc = resultado_npc["npc"]
        print(f"\n  [NPC] {npc['nome']}")
        print(
            f"     Nivel: {npc['nivel']} | Raca: {npc['raca']} | "
            f"Arquetipo: {npc.get('arquetipo', 'N/A')}"
        )
        st = npc.get("stats", {})
        print(
            f"     Stats: F{st.get('forca')} H{st.get('habilidade')} "
            f"R{st.get('resistencia')} A{st.get('armadura')}"
        )
        print(f"     PV: {st.get('pv')} | PM: {st.get('pm')}")

        if npc.get("magias"):
            print(f"     Magias: {', '.join(npc['magias'][:3])}")

        print("\n  [PERSONALIZACAO]")
        pers = resultado_npc.get("personalizacao", {})
        print(f"     Papel: {pers.get('papel_sugerido')}")
        print(f"     Gancho: {pers.get('gancho_imediato')}")

        print("\n  [SUGESTOES DE USO]")
        for sug in resultado_npc.get("sugestoes_uso", []):
            print(f"     - {sug}")

    print_section("Geracao 2: Encontro Inteligente")
    print("Query: 'crie encontro medio para 4 jogadores nivel 2'")

    resultado_encontro = generator.gerar(
        "crie encontro medio para 4 jogadores nivel 2",
        contexto={"party_size": 4, "party_level": 2},
    )

    if resultado_encontro.get("tipo") == "encontro":
        enc = resultado_encontro["encontro"]
        analise = resultado_encontro["analise"]

        print(f"\n  [ENCONTRO] {enc['nome']}")
        print(f"     Descricao: {enc['descricao']}")
        print(
            f"     Dificuldade: {enc['dificuldade']} "
            f"({analise.get('dificuldade_real', 'N/A')})"
        )

        print("\n  [BALANCEAMENTO]")
        print(f"     XP Alvo: {analise.get('xp_alvo')}")
        print(f"     XP Atingido: {analise.get('xp_atingido')}")
        print(f"     Percentual: {analise.get('balanceamento')}")

        inimigos = enc.get("inimigos", [])
        print(f"\n  [INIMIGOS] ({len(inimigos)})")
        for i, ini in enumerate(inimigos[:5], 1):
            variant = (
                f" [{ini.get('variante', 'comum')}]"
                if ini.get("variante") != "comum"
                else ""
            )
            print(f"     {i}. {ini.get('nome', '?')}{variant} - {ini.get('xp', 0)} XP")

        print("\n  [TESOURO]")
        for item in enc.get("tesouro", []):
            print(f"     - {item}")

        print("\n  [TATICAS]")
        print(f"     {enc.get('taticas', '')}")

        timeline = resultado_encontro.get("timeline", [])
        print("\n  [TIMELINE]")
        for evento in timeline:
            print(f"     Rodada {evento.get('rodada')}: {evento.get('evento')}")

        print("\n  [AJUSTES RAPIDOS]")
        ajustes = resultado_encontro.get("ajustes_rapidos", {})
        for chave, val in ajustes.items():
            print(f"     - {chave}: {val}")


def demo_integracao_nivel4_nivel5() -> None:
    """Demonstra integracao: Analise -> Geracao -> Recomendacao."""
    print_header("INTEGRACAO: NIVEL 4 + NIVEL 5", "=")

    cache = carregar_entity_cache()
    reasoning = SmartReasoning(entity_cache=cache)
    generator = SmartGenerator(entity_cache=cache)

    cenario = {
        "party_size": 4,
        "party_level": 3,
        "ultimo_encontro": "facil",
        "jogadores_solicitam": "algo mais desafiador",
    }

    query = (
        "preciso de um encontro desafiador para minha party de 4 nivel 3"
    )

    print_section(f"Cenario: {query}")
    print(f"Contexto da party: {cenario}")

    print("\n  [NIVEL 4 - ANALISE]")
    analise = reasoning.analisar(query)
    print(f"     Tipo: {analise.tipo.value}")
    print(f"     Intencao: {analise.intencao_principal}")
    print(
        f"     Detectado: Party {cenario['party_size']} jogadores, "
        f"nivel ~{cenario['party_level']}, querem desafio"
    )

    if cenario.get("ultimo_encontro") == "facil" and "desafiador" in query:
        dificuldade_ajustada = "dificil"
        print(
            "     Ajuste: 'facil' -> 'dificil' (jogadores pediram desafio)"
        )
    else:
        dificuldade_ajustada = analise.parametros.get("dificuldade", "medio")

    print("\n  [NIVEL 5 - GERACAO]")

    query_ajustada = (
        f"crie encontro {dificuldade_ajustada} para "
        f"{cenario['party_size']} jogadores nivel {cenario['party_level']}"
    )
    resultado = generator.gerar(query_ajustada, contexto=cenario)

    if resultado.get("tipo") == "encontro":
        enc = resultado["encontro"]
        print(f"     Gerado: {enc['nome']}")
        print(
            f"     XP: {enc['xp_total']} "
            f"({resultado.get('analise', {}).get('balanceamento', 'N/A')})"
        )
        print(f"     Inimigos: {len(enc.get('inimigos', []))} criaturas")

        print("\n  [RECOMENDACAO FINAL]")
        rec = reasoning.gerar_recomendacao(analise, [])
        print(f"     {rec.descricao}")
        print(f"     Proximo passo: {rec.proximo_passo}")

        if rec.alternativas:
            print("\n     Alternativas:")
            for alt in rec.alternativas[:2]:
                key = "variante" if "variante" in alt else "cenario"
                print(f"       - {alt.get(key, 'N/A')}")


def carregar_entity_cache() -> dict:
    """Carrega entity_cache do demo se disponivel."""
    cache: dict = {}
    chunks_path = ROOT / "data" / "demo_processed" / "demo_chunks.json"

    if chunks_path.exists():
        try:
            with chunks_path.open("r", encoding="utf-8") as f:
                chunks = json.load(f)
            for chunk in chunks:
                meta = chunk.get("metadata", {}) or {}
                entity = meta.get("entity_name")
                if entity:
                    key = str(entity).lower()
                    cache.setdefault(key, []).append(chunk)
            print(f"\n[OK] Cache carregado: {len(cache)} entidades")
        except Exception as e:
            print(f"\n[AVISO] Erro ao carregar cache: {e}")
    else:
        print(f"\n[AVISO] Cache nao encontrado: {chunks_path}")
        print("        Rode primeiro: python tests/demo_table_pipeline.py")

    return cache


def comparar_geracao_simples_vs_inteligente() -> None:
    """Compara geracao basica vs inteligente."""
    print_header("COMPARACAO: Geracao Simples vs Inteligente", "=")

    print_section("Geracao Simples (Nivel 3)")
    print("  Apenas cria dados aleatorios dentro das regras")
    print("  Ex: NPC nivel 3 com stats aleatorios")

    print_section("Geracao Inteligente (Nivel 5)")
    print("  1. Analisa contexto (party nivel 3, tema elemental)")
    print("  2. Detecta necessidade (falta mago de fogo na party)")
    print("  3. Gera NPC especifico (mago elemental nivel 3)")
    print("  4. Personaliza (conhece o vilao, tem gancho de missao)")
    print("  5. Sugere uso (aliado temporario com informacoes chave)")


def main() -> None:
    """Executa demonstracao completa."""
    print("\n" + "=" * 80)
    print("  SISTEMA 3D&T - NIVEL 4 + NIVEL 5")
    print("  Raciocinio Inteligente + Geracao Contextual")
    print("=" * 80)

    carregar_entity_cache()

    demo_nivel4_analise()
    demo_nivel5_geracao()
    demo_integracao_nivel4_nivel5()
    comparar_geracao_simples_vs_inteligente()

    print_header("RESUMO DA EVOLUCAO", "=")
    print("""
+-----------------------------------------------------------------------------+
| NIVEL 3: Geracao Basica                                                    |
+-----------------------------------------------------------------------------+
| - Cria NPCs/encontros aleatorios dentro das regras                         |
| - Nao considera contexto da party/sessao                                    |
| - Requer ajuste manual pelo MJ                                              |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 4: Raciocinio Inteligente  [IMPLEMENTADO]                            |
+-----------------------------------------------------------------------------+
| - Detecta intencao da query (comparacao, otimizacao, calculo)              |
| - Extrai parametros automaticamente (nivel, PE, dificuldade)               |
| - Gera recomendacoes com calculos e analises                               |
| - Sugere proximas acoes baseadas no contexto                                |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
| NIVEL 5: Geracao Contextual  [IMPLEMENTADO]                               |
+-----------------------------------------------------------------------------+
| - Usa analise Nivel 4 para guiar geracao                                   |
| - Adapta ao contexto da party (nivel, composicao, historico)               |
| - Gera conteudo com proposito (NPCs com ganchos, encontros balanceados)     |
| - Fornece timeline, taticas e ajustes rapidos                               |
| - Personaliza baseado nas necessidades detectadas                           |
+-----------------------------------------------------------------------------+

[PROXIMO PASSO] NIVEL 6: Sessao Persistente
   - Manter estado entre interacoes
   - Historico de combates e NPCs usados
   - Evolucao da campanha ao longo do tempo
""")

    print("\n[OK] Sistema pronto para uso!")
    print("   from src.generation.smart_generator import gerar_inteligente")
    print("   resultado = gerar_inteligente('sua query aqui')")


if __name__ == "__main__":
    main()
