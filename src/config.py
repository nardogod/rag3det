from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


load_dotenv()


@lru_cache(maxsize=1)
def _load_settings_from_yaml() -> Dict[str, Any]:
    """
    Carrega `config/settings.yaml`, se existir.

    - Valores em `.env` continuam válidos e têm prioridade sobre o YAML.
    - YAML serve como configuração “documentada” e fácil de versionar.
    """
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    if not settings_path.exists():
        return {}

    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        # Se PyYAML não estiver instalado, seguimos só com .env e defaults.
        return {}

    try:
        with settings_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        # Em caso de YAML malformado, não quebramos o app – apenas ignoramos.
        return {}


def _get_setting(path: str, default: Any) -> Any:
    """
    Busca um valor no YAML usando um caminho do tipo "secao.subchave".
    Se não existir ou o arquivo não estiver disponível, retorna `default`.
    """
    data = _load_settings_from_yaml()
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


@dataclass(frozen=True)
class Paths:
    """Caminhos principais usados no projeto."""

    project_root: Path = Path(__file__).resolve().parents[1]
    data_dir: Path = project_root / "data"
    raw_data_dir: Path = data_dir / "raw"
    chroma_dir: Path = Path(os.getenv("CHROMA_DB_DIR", data_dir / "chroma"))

    @property
    def source_pdf_dir(self) -> Path:
        """Diretório de onde ler os PDFs originais dos livros 3D&T."""
        env_path = os.getenv("SOURCE_PDF_DIR")
        return Path(env_path) if env_path else self.raw_data_dir


def _env_or_yaml(env_key: str, yaml_path: str, fallback: Any) -> Any:
    """Prioridade: variável de ambiente > YAML > fallback."""
    return os.getenv(env_key) or _get_setting(yaml_path, fallback)


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuração do modelo de embeddings."""

    # Caminho local do modelo fine-tuned (3D&T) ou nome HuggingFace.
    model_name: str = _env_or_yaml(
        "EMBEDDING_MODEL_NAME",
        "embedding.model_name",
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    )
    # Caminho do modelo fine-tuned; se existir, tem prioridade sobre model_name.
    embedding_model: str = _env_or_yaml(
        "EMBEDDING_MODEL",
        "embedding.embedding_model",
        "models/embeddings/3dt_finetuned",
    )
    # Fallback quando o modelo fine-tuned não existe ou falha ao carregar.
    embedding_fallback: str = _env_or_yaml(
        "EMBEDDING_FALLBACK",
        "embedding.embedding_fallback",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )


@dataclass(frozen=True)
class LLMConfig:
    """Configuração dos modelos de linguagem (LLM)."""

    provider: str = _env_or_yaml("LLM_PROVIDER", "llm.provider", "ollama").lower()

    # Ollama
    ollama_model: str = _env_or_yaml("OLLAMA_MODEL", "llm.ollama_model", "llama3.1")
    ollama_base_url: str = _env_or_yaml(
        "OLLAMA_BASE_URL", "llm.ollama_base_url", "http://localhost:11434"
    )

    # OpenAI
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model_name: str = _env_or_yaml(
        "OPENAI_MODEL_NAME", "llm.openai_model_name", "gpt-4.1-mini"
    )


@dataclass(frozen=True)
class ChunkingConfig:
    """Parâmetros de chunking de texto."""

    chunk_size: int = int(_env_or_yaml("CHUNK_SIZE", "chunking.chunk_size", "1000"))
    chunk_overlap: int = int(_env_or_yaml("CHUNK_OVERLAP", "chunking.chunk_overlap", "200"))


@dataclass(frozen=True)
class RetrievalConfig:
    """Parâmetros de busca e reranking."""

    # Quantidade final de trechos enviados para o LLM.
    k: int = int(_env_or_yaml("RETRIEVAL_K", "retrieval.top_k", "6"))

    # Candidatos na primeira etapa (antes do rerank). Retrieve 20 → rerank → top k.
    candidate_k: int = int(_env_or_yaml("RETRIEVAL_CANDIDATE_K", "retrieval.candidate_k", "20"))

    # Busca híbrida: pesos para combinar score semântico e BM25.
    hybrid_semantic_weight: float = float(
        _env_or_yaml("HYBRID_SEMANTIC_WEIGHT", "retrieval.hybrid_semantic_weight", "0.7")
    )
    hybrid_bm25_weight: float = float(
        _env_or_yaml("HYBRID_BM25_WEIGHT", "retrieval.hybrid_bm25_weight", "0.3")
    )
    hybrid_enabled: bool = (os.getenv("HYBRID_ENABLED", "true").lower() == "true")
    query_expansion_enabled: bool = (
        os.getenv("QUERY_EXPANSION_ENABLED", "true").lower() == "true"
    )

    # Flag geral para habilitar/desabilitar reranking (cross-encoder).
    reranking_enabled: bool = (
        os.getenv("RERANKING_ENABLED", "true").lower() == "true"
    )


paths = Paths()
embedding_config = EmbeddingConfig()
llm_config = LLMConfig()
chunking_config = ChunkingConfig()
retrieval_config = RetrievalConfig()

