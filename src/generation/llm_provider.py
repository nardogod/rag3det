from __future__ import annotations

import logging
from functools import lru_cache
from langchain_core.language_models import BaseChatModel

from src.config import llm_config


logger = logging.getLogger(__name__)

OLLAMA_NOT_RUNNING_MSG = (
    "O Ollama não está rodando ou não está acessível.\n"
    "Para usar o LLM local:\n"
    "  1. Instale o Ollama: https://ollama.com\n"
    "  2. No terminal, execute: ollama serve\n"
    "  3. Baixe um modelo: ollama pull llama3.1\n"
    "  4. Tente novamente."
)


@lru_cache(maxsize=1)
def get_chat_llm() -> BaseChatModel:
    """
    Retorna o LLM configurado (Ollama ou OpenAI).

    - Provedor e modelo vêm do `.env` ou de `config/settings.yaml`.
    - Se Ollama estiver configurado mas não responder, exibe instruções claras.
    """
    provider = llm_config.provider

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        logger.info(
            "Usando Ollama: model=%s, base_url=%s",
            llm_config.ollama_model,
            llm_config.ollama_base_url,
        )
        try:
            return ChatOllama(
                model=llm_config.ollama_model,
                base_url=llm_config.ollama_base_url,
                temperature=0.3,
            )
        except Exception as e:
            err_str = str(e).lower()
            if "connection" in err_str or "refused" in err_str or "ollama" in err_str:
                raise RuntimeError(OLLAMA_NOT_RUNNING_MSG) from e
            raise

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not llm_config.openai_api_key:
            raise ValueError(
                "LLM_PROVIDER=openai exige OPENAI_API_KEY no .env. "
                "Defina a variável e tente novamente."
            )
        logger.info("Usando OpenAI: model=%s", llm_config.openai_model_name)
        return ChatOpenAI(
            model=llm_config.openai_model_name,
            api_key=llm_config.openai_api_key,
            temperature=0.3,
        )

    raise ValueError(
        f"LLM_PROVIDER desconhecido: {provider}. Use 'ollama' ou 'openai'."
    )
