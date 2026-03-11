"""
Camada 3: Extrator flexível que tolera variações de formato no Manual da Magia 3D&T.
Usado para validar/corrigir extrações e tratar casos com formatação irregular.
"""

from __future__ import annotations

import re
from typing import Dict, Optional


class ExtratorMagiaFlexivel:
    """
    Extrator que tolera variações de formato no Manual da Magia 3D&T.
    Escolas: Branca, Negra, Elemental (água/fogo/ar/terra/espírito), etc.
    """

    # Padrão de custo (aceita "1 PM", "2 a 10 PMs", "padrão", etc.)
    PAT_CUSTO = re.compile(
        r"Custo:\s*([^.]+?)(?:\.|$)",
        re.IGNORECASE | re.DOTALL,
    )
    PAT_ALCANCE = re.compile(
        r"Alcance:\s*([^;]+?)(?:;|\.|$)",
        re.IGNORECASE,
    )
    PAT_DURACAO = re.compile(
        r"Dura[çc][ãa]o:\s*([^.]+?)(?=\n|$|Escola|Custo|Alcance|Exig[eê]ncias)",
        re.IGNORECASE,
    )
    PAT_ESCOLA = re.compile(
        r"Escola:\s*([^.]+)\.",
        re.IGNORECASE,
    )

    @classmethod
    def extrair(
        cls,
        texto: str,
        nome_esperado: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Extrai campos de uma magia mesmo com formatação irregular.

        Args:
            texto: Bloco de texto da magia
            nome_esperado: Se soubermos o nome (do índice), validar

        Returns:
            Dict com nome, escola, custo, alcance, duracao, descricao, confianca
            ou None se confiança < 0.6
        """
        resultado: Dict = {
            "nome": nome_esperado or cls._extrair_nome(texto),
            "escola": None,
            "custo": None,
            "alcance": None,
            "duracao": None,
            "descricao": None,
            "confianca": 0.0,
        }

        escola_m = cls.PAT_ESCOLA.search(texto)
        if escola_m:
            resultado["escola"] = escola_m.group(1).strip()
            resultado["confianca"] += 0.2

        custo_m = cls.PAT_CUSTO.search(texto)
        if custo_m:
            resultado["custo"] = custo_m.group(1).strip()
            resultado["confianca"] += 0.2

        alcance_m = cls.PAT_ALCANCE.search(texto)
        if alcance_m:
            resultado["alcance"] = alcance_m.group(1).strip()
            resultado["confianca"] += 0.2

        duracao_m = cls.PAT_DURACAO.search(texto)
        if duracao_m:
            resultado["duracao"] = duracao_m.group(1).strip()
            resultado["confianca"] += 0.2

        resultado["descricao"] = cls._extrair_descricao(texto)
        if resultado["descricao"] and len(resultado["descricao"]) > 20:
            resultado["confianca"] += 0.2

        return resultado if resultado["confianca"] >= 0.6 else None

    @classmethod
    def _extrair_nome(cls, texto: str) -> str:
        """Extrai nome da primeira linha não-vazia que parece título de magia."""
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        for linha in linhas:
            if any(x in linha.lower() for x in ["escola:", "custo:", "alcance:", "duração"]):
                break
            nome = re.sub(r"^\d+\s*[-.]\s*", "", linha)
            if len(nome) > 2 and nome[0].isupper():
                return nome
        return "Desconhecida"

    @classmethod
    def _extrair_descricao(cls, texto: str) -> str:
        """Extrai descrição removendo linhas de metadados."""
        linhas = texto.split("\n")
        descricao_linhas = []
        for linha in linhas:
            ls = linha.strip()
            if any(
                x in ls.lower()
                for x in [
                    "escola:",
                    "custo:",
                    "alcance:",
                    "duração:",
                    "duraçao:",
                    "exigências:",
                    "exigencias:",
                ]
            ):
                continue
            if ls:
                descricao_linhas.append(ls)
        return " ".join(descricao_linhas)
