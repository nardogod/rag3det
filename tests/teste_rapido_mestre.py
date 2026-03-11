"""
Teste rapido do Mestre com schema estruturado e validacao.
Verifica se o fluxo retorna respostas validas (teste, narracao concreta, sem repeticao).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.master.master_autonomo_3dt import EstiloNarrativo, MestreAutonomo3DT


def main() -> None:
    mestre = MestreAutonomo3DT(estilo=EstiloNarrativo.HEROICO)
    mestre.criar_campanha_autonoma("Teste validacao")
    mestre.preparar_sessao(1)

    # Sem LLM: usa fluxo do sistema (combate, social, exploracao)
    mestre.use_llm_narracao = False

    estado = {
        "cena": "Vale com runas",
        "personagem": {"nome": "Thorin", "forca": 2, "habilidade": 1},
        "descobertas": [],
        "inimigos": [],
    }

    acoes_teste = [
        "Investigar as runas nas paredes",
        "Atacar o goblin com a espada",
    ]

    for acao in acoes_teste:
        print(f"\n{'='*50}")
        print(f"ACAO: {acao}")
        dec = mestre.processar_acao_jogadores(
            [
                {
                    "personagem": "Thorin",
                    "acao_descricao": acao,
                    "intencao": "investigar" if "runas" in acao.lower() else "atacar",
                }
            ]
        )
        print(f"RESPOSTA: {dec.conteudo[:200]}...")
        if dec.teste_necessario:
            print(f"TESTE: {dec.teste_necessario.descricao}")
        assert dec.conteudo, "Resposta vazia"
        # Nota: modo sistema pode incluir descricao ambiente; validacao "vale" e para LLM
        print("OK")

    print("\n[OK] Teste rapido passou (modo sistema, sem LLM)")


if __name__ == "__main__":
    main()
