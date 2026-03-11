"""
Schemas Pydantic para resposta estruturada do Mestre 3D&T.
Forca o LLM a retornar formato valido via function calling / structured output.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class MudancaEstado(BaseModel):
    """Mudancas no estado do jogo (merge, nao replace)."""

    descobertas_add: List[str] = Field(default_factory=list, description="Novas descobertas")
    inimigos_add: List[str] = Field(default_factory=list, description="Inimigos que apareceram")
    objetivos_add: List[str] = Field(default_factory=list, description="Novos objetivos")
    em_combate: Optional[bool] = Field(default=None, description="Entrou ou saiu de combate")


class AcaoResolvida(BaseModel):
    """
    Schema obrigatorio para resposta do Mestre.
    O LLM DEVE preencher este formato. Violar resulta em resposta invalida.
    """

    tipo_acao: Literal[
        "teste_atributo",
        "ataque",
        "defesa",
        "social",
        "exploracao",
        "movimento",
        "narracao",
    ] = Field(..., description="Tipo da acao sendo resolvida")
    atributo_usado: Optional[
        Literal["Forca", "Habilidade", "Resistencia", "Armadura"]
    ] = Field(default=None, description="Atributo do teste (F/H/R/A)")
    dificuldade: Optional[
        Literal["Facil", "Normal", "Dificil", "Muito Dificil"]
    ] = Field(default=None, description="Classe de Dificuldade: Facil=3, Normal=4, Dificil=5")
    descricao_teste: str = Field(
        default="",
        description="O que esta sendo testado (ex: Percepcao das runas)",
    )
    resultado_narrativo: str = Field(
        ...,
        description="O QUE ACONTECEU DE FATO apos a acao. Concreto, especifico. PROIBIDO: 'parece que', 'talvez', 'você tenta'",
    )
    mudanca_estado: MudancaEstado = Field(
        default_factory=MudancaEstado,
        description="Mudancas no estado (descobertas, inimigos, objetivos)",
    )
    proximas_opcoes: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2 a 4 opcoes de acao para o jogador",
    )

    @model_validator(mode="after")
    def deve_ter_teste_para_acoes_incertas(self) -> "AcaoResolvida":
        """Acoes de exploracao, social, ataque, defesa requerem atributo_usado e dificuldade."""
        acoes_com_teste = ("exploracao", "social", "ataque", "defesa", "teste_atributo")
        if self.tipo_acao in acoes_com_teste:
            if not self.atributo_usado:
                raise ValueError(
                    f"Acao '{self.tipo_acao}' requer atributo_usado: Forca, Habilidade, Resistencia ou Armadura"
                )
            if not self.dificuldade:
                raise ValueError(
                    f"Acao '{self.tipo_acao}' requer dificuldade: Facil, Normal, Dificil ou Muito Dificil"
                )
        return self
