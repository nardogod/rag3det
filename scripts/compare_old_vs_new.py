"""
Comparacao lado a lado: Sistema Antigo (Nivel 2) vs Sistema Novo (Niveis 3-8).
Mostra a evolucao da resposta para a mesma query.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Garantir que o pacote src esteja no path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.vectorstore.chroma_store import get_vectorstore


def old_system_query(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """
    Sistema ANTIGO (nivel 2): apenas busca semantica no ChromaDB.
    Aproximadamente equivalente ao antigo scripts/test_query.py.
    """
    print("=" * 80)
    print("SISTEMA ANTIGO (Nivel 2): Busca Semantica Pura")
    print("Arquivo de referencia: scripts/test_query.py (versao antiga)")
    print("=" * 80)

    # Carrega o mesmo Chroma usado pelo sistema, mas sem nenhuma logica extra.
    # Aqui podemos usar o indice baseline (quando existir) para comparar.
    try:
        vector_db = get_vectorstore(use_baseline=False)
    except Exception as e:
        print("\n[ERRO] Nao foi possivel carregar o indice Chroma antigo.")
        print(f"Detalhes: {e}")
        return []

    docs = vector_db.similarity_search_with_score(query, k=top_k)

    print(f"\n[QUERY] '{query}'")
    print("Tipo de sistema: busca vetorial pura (sem tabelas / raciocinio)")
    print(f"Top-{top_k} trechos:\n")

    results: List[Dict[str, Any]] = []
    for i, (doc, score) in enumerate(docs, 1):
        content = (doc.page_content or "")[:200].replace("\n", " ")
        print(f"  {i}. [score={score:.4f}] {content}...")
        results.append(
            {
                "rank": i,
                "score": float(score),
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", "?"),
            }
        )

    print("\n" + "-" * 80)
    print("LIMITACOES DO SISTEMA ANTIGO:")
    print(" - Apenas texto solto, sem estrutura")
    print(" - Sem atributos (F/H/R/A/PV/PM)")
    print(" - Sem calculos (XP, poder de combate)")
    print(" - Sem comparacao entre entidades")
    print(" - Sem geracao de conteudo")
    print(" - Sem contexto de regras ou tabelas")
    print("-" * 80)

    return results


def new_system_query(query: str) -> List[Dict[str, Any]]:
    """
    Sistema NOVO (niveis 3-8): dados estruturados + raciocinio.
    Usa os chunks de tabelas gerados pela demo da TablePipeline.
    """
    print("\n" + "=" * 80)
    print("SISTEMA NOVO (Niveis 3-8): Dados Estruturados + Raciocinio")
    print("Fonte: data/demo_processed/demo_chunks.json (demo)")
    print("=" * 80)

    chunks_path = Path("data/demo_processed/demo_chunks.json")

    if not chunks_path.exists():
        print(f"\n[AVISO] Arquivo nao encontrado: {chunks_path}")
        print("Rode primeiro: python tests/demo_table_pipeline.py")
        return []

    with chunks_path.open("r", encoding="utf-8") as f:
        chunks = json.load(f)

    query_lower = query.lower()
    results: List[Dict[str, Any]] = []

    for chunk in chunks:
        meta = chunk.get("metadata", {}) or {}
        content = (chunk.get("content") or "").lower()

        entity_name = (meta.get("entity_name") or "").lower()
        table_type = meta.get("table_type", "")

        if query_lower in entity_name or query_lower in content:
            data = meta.get("structured_data", {}) or {}
            result = {
                "tipo": meta.get("type", "unknown"),
                "tabela": table_type,
                "entidade": meta.get("entity_name"),
                "fonte": f"{meta.get('source', 'Desconhecido')} (p. {meta.get('page', '?')})",
                "conteudo": (chunk.get("content") or "")[:300],
                "dados_estruturados": data,
            }
            results.append(result)

    por_tipo: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        tipo = r["tabela"] or "outro"
        por_tipo.setdefault(tipo, []).append(r)

    print(f"\n[QUERY] '{query}'")
    print("Fontes: tabelas estruturadas (stats, magias, equipamentos)\n")

    for tipo, itens in por_tipo.items():
        print(f"\nCATEGORIA: {tipo.upper()} ({len(itens)} resultados)")
        print("-" * 70)

        for item in itens[:2]:
            data = item["dados_estruturados"]

            if tipo == "stats" and data:
                print(f"\n  ENTIDADE: {data.get('nome', 'Desconhecido')}")
                print(
                    "     Atributos: "
                    f"F={data.get('forca')} H={data.get('habilidade')} "
                    f"R={data.get('resistencia')} A={data.get('armadura')} "
                    f"PV={data.get('pv')} PM={data.get('pm')}"
                )
                print(
                    "     Poder de Combate: "
                    f"{data.get('poder_combate')} | "
                    f"Categoria: {data.get('categoria_poder')} | "
                    f"XP: {data.get('xp_sugerido')}"
                )

            elif tipo == "magias" and data:
                print(f"\n  MAGIA: {data.get('nome', 'Desconhecido')}")
                print(
                    f"     Custo: {data.get('custo_pm')} PM | "
                    f"Circulo: {data.get('circulo')}"
                )
                print(
                    f"     Alcance: {data.get('alcance')} | "
                    f"Duracao: {data.get('duracao')}"
                )
                if data.get("is_combate"):
                    print("     Tipo: magia de combate")

            elif tipo == "equipamentos" and data:
                print(
                    f"\n  EQUIPAMENTO: {data.get('nome', 'Desconhecido')} "
                    f"({data.get('tipo')})"
                )
                print(
                    f"     Dano: {data.get('dano')} | PE: {data.get('pe')} | "
                    f"Bonus: {data.get('bonus')}"
                )
                if data.get("eficiencia_dano_pe"):
                    print(
                        "     Eficiencia: "
                        f"{data.get('eficiencia_dano_pe')} dano por PE"
                    )

            else:
                print(f"\n  ITEM: {item['entidade'] or 'Item'}")
                print(f"     {item['conteudo'][:150]}...")

            print(f"     Fonte: {item['fonte']}")

    print("\n" + "-" * 80)
    print("VANTAGENS DO SISTEMA NOVO:")
    print(" - Dados estruturados (F/H/R/A/PV/PM)")
    print(" - Calculos automaticos (XP, poder, eficiencia)")
    print(" - Comparacao entre entidades (via HybridRetriever)")
    print(" - Geracao de NPCs e encontros (ContentGenerator)")
    print(" - Recomendacoes inteligentes (equipamentos por build)")
    print(" - Sessoes persistentes (CampaignSession)")
    print("-" * 80)

    return results


def compare_systems(query: str) -> None:
    """
    Compara os dois sistemas lado a lado.
    """
    print("\n" + "=" * 40)
    print("COMPARACAO: SISTEMA ANTIGO vs NOVO")
    print("Mesma query, resultados completamente diferentes")
    print("=" * 40)

    old_results = old_system_query(query)
    new_results = new_system_query(query)

    print("\n" + "=" * 80)
    print("RESUMO COMPARATIVO")
    print("=" * 80)

    print(f"\nQuery: '{query}'")

    print("\nSISTEMA ANTIGO:")
    print(" - Tipo: busca semantica em textos")
    print(f" - Resultados: {len(old_results)} trechos de texto")
    print(" - Estrutura: nenhuma (texto solto)")
    print(" - Atributos: nao extraidos")
    print(" - Calculos: nao realizados")
    print(" - Uso: leitura manual do mestre de jogo")

    stats_count = len([r for r in new_results if r.get("tabela") == "stats"])
    magias_count = len([r for r in new_results if r.get("tabela") == "magias"])
    equip_count = len([r for r in new_results if r.get("tabela") == "equipamentos"])

    print("\nSISTEMA NOVO:")
    print(" - Tipo: busca hibrida (texto + tabelas)")
    print(f" - Resultados: {len(new_results)} itens estruturados")
    print(f"    - {stats_count} entidades com stats")
    print(f"    - {magias_count} magias")
    print(f"    - {equip_count} equipamentos")
    print(" - Estrutura: JSON completo")
    print(" - Atributos: F/H/R/A/PV/PM disponiveis")
    print(" - Calculos: XP, poder, eficiencia")
    print(" - Uso: automacao + geracao de conteudo")

    print("\n" + "=" * 80)
    print("CONCLUSAO")
    print("=" * 80)
    print(
        """
O sistema novo transforma a consulta \"goblin\" de:

ANTES: \"Achei alguns trechos de texto que mencionam goblin. Leia e interprete.\"

DEPOIS: \"Goblin: F3 H4 R2 A1 PV8 PM0. Categoria: Fraco. Poder de combate: 9.
         XP sugerido: 90. Ideal para encontros de nivel 1. Posso gerar 4 goblins
         para sua party (360 XP total) com tatica de flanqueamento.\"
        """.rstrip()
    )
    print("=" * 80)


def main() -> None:
    """Executa a comparacao para uma query."""
    parser = argparse.ArgumentParser(
        description="Compara sistema antigo vs novo para uma query."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="goblin",
        help="Query de busca (padrao: goblin)",
    )
    args = parser.parse_args()
    compare_systems(args.query)


if __name__ == "__main__":
    main()

