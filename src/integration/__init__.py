"""Integracao entre modulos do sistema 3D&T (multimodal, API, etc.)."""

from src.integration.sistema_multimodal_3dt import (
    SistemaMultimodal3DT,
    RespostaMultimodal,
    ContextoVisual,
    TipoConsultaVisual,
    demo_multimodal,
)

__all__ = [
    "SistemaMultimodal3DT",
    "RespostaMultimodal",
    "ContextoVisual",
    "TipoConsultaVisual",
    "demo_multimodal",
]
