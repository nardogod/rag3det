from __future__ import annotations

import logging
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm_config
from src.generation.llm_provider import OLLAMA_NOT_RUNNING_MSG, get_chat_llm
from src.generation.prompts import SYSTEM_PROMPT, USER_TEMPLATE, format_context
from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.retrieval.pipeline import retrieve_relevant_chunks
from src.types import QAResult, RetrievedChunk, SourceMetadata


logger = logging.getLogger(__name__)


def answer_question(
    question: str,
    k: Optional[int] = None,
) -> QAResult:
    """
    Responde uma pergunta sobre 3D&T usando apenas os livros indexados (RAG).

    Fluxo:
    1. Busca trechos relevantes com `retrieve_relevant_chunks(question, k)`.
    2. Monta o contexto formatado e o prompt de usuário.
    3. Chama o LLM com system prompt restritivo.
    4. Retorna a resposta em português e a lista de fontes (metadados dos chunks).

    Este é o ponto de entrada que a interface Streamlit e os scripts devem usar.
    """
    logger.info("Processando pergunta: %s", question[:80])

    chunks: List[RetrievedChunk] = retrieve_relevant_chunks(query=question, k=k)

    if not chunks:
        logger.warning("Nenhum trecho encontrado para a pergunta.")
        return QAResult(
            answer="Não encontrei trechos relevantes nos livros indexados. "
                   "Verifique se o índice foi construído (scripts/build_index.py) e se há PDFs no diretório configurado.",
            sources=[],
        )

    context_str = format_context(chunks)
    user_message = USER_TEMPLATE.format(question=question, context=context_str)

    llm = get_chat_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    try:
        response = llm.invoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)
        answer = expandir_siglas_3dt(answer)
    except RuntimeError as e:
        if e.args and OLLAMA_NOT_RUNNING_MSG in str(e.args[0]):
            return QAResult(answer=str(e.args[0]), sources=[c.metadata for c in chunks])
        logger.exception("Erro ao chamar o LLM: %s", e)
        return QAResult(answer=f"Erro: {e}.", sources=[c.metadata for c in chunks])
    except Exception as e:
        logger.exception("Erro ao chamar o LLM: %s", e)
        err_lower = str(e).lower()
        if llm_config.provider == "ollama" and (
            "connection" in err_lower or "refused" in err_lower or "ollama" in err_lower
        ):
            return QAResult(answer=OLLAMA_NOT_RUNNING_MSG, sources=[c.metadata for c in chunks])
        return QAResult(
            answer=f"Erro ao gerar resposta: {e}. Verifique se o Ollama está rodando (ou a API key da OpenAI) e tente novamente.",
            sources=[c.metadata for c in chunks],
        )

    sources: List[SourceMetadata] = [c.metadata for c in chunks]

    logger.info("Resposta gerada com sucesso. Fontes: %d", len(sources))

    return QAResult(answer=answer, sources=sources)
