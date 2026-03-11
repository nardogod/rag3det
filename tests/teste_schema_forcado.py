"""
Teste de validacao do schema forcado.
Verifica que acoes de investigar/atacar retornam atributo_usado, dificuldade, etc.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.master.master_autonomo_3dt import EstiloNarrativo, MestreAutonomo3DT


def teste_investigar_runas() -> None:
    """Investigar runas deve retornar teste com atributo e descoberta."""
    mestre = MestreAutonomo3DT(estilo=EstiloNarrativo.HEROICO)
    mestre.criar_campanha_autonoma("Teste schema")
    mestre.preparar_sessao(1)
    mestre.use_llm_narracao = False  # Usa fluxo sistema (garantido)

    dec = mestre.processar_acao_jogadores([
        {
            "personagem": "Thorin",
            "acao_descricao": "Investigar runas na parede",
            "intencao": "investigar",
        }
    ])

    assert dec is not None, "Decisao nao pode ser None"
    assert dec.teste_necessario is not None, "Investigar deve ter teste"
    assert dec.teste_necessario.atributo, "Deve ter atributo"
    assert dec.teste_necessario.cd in (3, 4, 5, 6), "CD deve ser 3-6"
    assert dec.conteudo, "Deve ter narracao"
    assert "1d6" in (dec.teste_necessario.descricao or ""), "Descricao deve mencionar 1d6"

    print("Schema valido:")
    print(f"  Atributo: {dec.teste_necessario.atributo}")
    print(f"  CD: {dec.teste_necessario.cd}")
    print(f"  Resultado: {dec.teste_necessario.resultado}")
    print(f"  Sucesso: {dec.teste_necessario.sucesso}")
    print(f"  Conteudo: {dec.conteudo[:100]}...")
    if dec.mudanca_estado.get("descobertas_add"):
        print(f"  Descobertas: {dec.mudanca_estado['descobertas_add']}")


if __name__ == "__main__":
    teste_investigar_runas()
    print("\n[OK] Teste schema forcado passou")
