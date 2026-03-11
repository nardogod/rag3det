from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import retrieval_config
from src.generation.few_shot_examples import get_few_shot_block
from src.generation.llm_provider import get_chat_llm
from src.generation.prompts import format_context
from src.retrieval.pipeline import retrieve_relevant_chunks
from src.types import QAResult, RetrievedChunk, SourceMetadata


logger = logging.getLogger(__name__)


def _build_structured_system_prompt() -> str:
    few_shot = get_few_shot_block()
    return """
Você é o CONSULTOR OFICIAL do sistema 3D&T (Defensores de Tóquio 3ª Edição).
Você consulta APENAS os documentos fornecidos no contexto.
NÃO use conhecimento de D&D, Pathfinder ou outros RPGs.
NÃO invente regras que não estão nos textos.

FORMATO OBRIGATÓRIO DE RESPOSTA:

📜 REGRA LITERAL: "[citação exata do livro entre aspas]"

🎲 EXPLICAÇÃO: [sua interpretação objetiva, sem fluff]

📊 FÓRMULA/MECÂNICA:
- Se houver cálculo: mostre a matemática
- Se houver teste: mostre o que rolar contra o quê
- Se houver tabela: reproduza a tabela

📖 FONTE PRIMÁRIA: [Nome do Livro], página [X]
📖 FONTES SECUNDÁRIAS (se aplicável): [Outros livros mencionados]

🔗 RELAÇÕES (opcional): Se houver informações do grafo de conhecimento (tipo, elemento, custo PM), resuma em uma linha. Ex.: "Fênix é uma Magia Elemental de Fogo (custo: 10 PM)"

👥 SIMILARES (opcional): Outras entidades do mesmo tipo/cluster. Ex.: "Outras magias de fogo: Bola de Fogo, Muralha de Fogo"

⚠️ LIMITAÇÃO: [o que NÃO está nos documentos fornecidos, se houver]

EXEMPLOS DE RESPOSTAS CORRETAS:

{few_shot_examples}

Agora responda à pergunta do usuário seguindo EXATAMENTE o formato acima (📜, 🎲, 📊, 📖, ⚠️).

Se a pergunta não puder ser respondida pelos documentos:
"Não consta nos livros oficiais disponíveis: [lista dos livros indexados]"
""".strip().format(few_shot_examples=few_shot)


STRUCTURED_SYSTEM_PROMPT = _build_structured_system_prompt()


@dataclass
class GenerationMetrics:
    citacao_presente: bool
    fonte_citada: bool
    formula_presente: bool
    confidence_score: float


def _has_required_blocks(text: str) -> bool:
    """True se a resposta contém os blocos obrigatórios 📜, 🎲 e 📖 (para regenerar até 3x)."""
    return (
        "📜" in text and ("REGRA LITERAL" in text or '"' in text)
        and "🎲" in text and "EXPLICAÇÃO" in text
        and "📖" in text and ("FONTE" in text or "página" in text)
    )


def _validate_response(text: str, had_numeric_context: bool) -> GenerationMetrics:
    """Valida se a resposta segue o formato exigido e calcula métricas simples."""
    citacao_presente = "📜 REGRA LITERAL:" in text and '"' in text
    fonte_citada = "📖 FONTE PRIMÁRIA:" in text and "página" in text

    formula_presente = False
    if "📊 FÓRMULA/MECÂNICA" in text and had_numeric_context:
        # Procura dados (1d6, 2d10) ou expressões numéricas simples
        import re

        dice_pat = re.search(r"\d+d\d+", text)
        math_pat = re.search(r"\d+\s*[\+\-\*\/]\s*\d+", text)
        formula_presente = bool(dice_pat or math_pat)

    # Confiança simples baseada na quantidade de chunks recuperados vs k
    k = retrieval_config.k or 1
    confidence_score = 0.0  # será preenchido pelo chamador com base nos chunks

    return GenerationMetrics(
        citacao_presente=citacao_presente,
        fonte_citada=fonte_citada,
        formula_presente=formula_presente,
        confidence_score=confidence_score,
    )


def _log_response(
    question: str,
    answer: str,
    metrics: GenerationMetrics,
    chunks: List[RetrievedChunk],
) -> None:
    """Salva log estruturado em logs/respostas/respostas.jsonl."""
    try:
        log_dir = Path("logs") / "respostas"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "respostas.jsonl"

        payload: Dict[str, object] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "question": question,
            "answer": answer,
            "metrics": asdict(metrics),
            "chunks": [
                {
                    "book_title": c.metadata.get("book_title"),
                    "source": c.metadata.get("source"),
                    "page": c.metadata.get("page"),
                    "section": c.metadata.get("section"),
                    "section_title": c.metadata.get("section_title"),
                }
                for c in chunks
            ],
        }

        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:  # logging não deve quebrar o fluxo
        logger.exception("Falha ao salvar log de resposta estruturada: %s", e)


def _get_knowledge_enrichment(question: str) -> str:
    """Se a pergunta mencionar entidade conhecida, retorna texto para RELAÇÕES e SIMILARES."""
    try:
        from src.knowledge.base import (
            get_entity_cluster,
            get_cluster_entities,
            get_relations_for_entity,
            load_entities,
            load_properties,
            load_taxonomy,
        )
    except Exception:
        return ""
    entities = load_entities()
    if not entities:
        return ""
    q_lower = question.strip().lower()
    entity_name = None
    for name in entities:
        if name.lower() == q_lower or q_lower in name.lower() or name.lower() in q_lower:
            entity_name = name
            break
    if not entity_name:
        return ""
    lines = []
    relations = get_relations_for_entity(entity_name)
    if relations:
        parts = [f"{entity_name}"]
        for r in relations[:5]:
            rel, target = r.get("relation", ""), (r.get("target") or "").strip()
            if rel == "is_a" and target:
                parts.append(f"é {target}")
            elif rel == "element" and target:
                parts.append(f"elemento: {target}")
            elif rel == "cost_pm" and target:
                parts.append(f"custo: {target} PM")
        if len(parts) > 1:
            lines.append("RELAÇÕES: " + " | ".join(parts))
    props = load_properties().get(entity_name, {}).get("properties", {})
    if props:
        parts = [f"{k}={v}" for k, v in list(props.items())[:5] if v is not None]
        if parts:
            lines.append("Propriedades: " + ", ".join(parts))
    cid = get_entity_cluster(entity_name)
    if cid:
        taxonomy = load_taxonomy()
        similars = [e for e in get_cluster_entities(cid, taxonomy) if e != entity_name][:5]
        if similars:
            lines.append("SIMILARES (mesmo cluster): " + ", ".join(similars))
    if not lines:
        return ""
    return "Informações do grafo de conhecimento (use para 🔗 RELAÇÕES e 👥 SIMILARES se aplicável):\n" + "\n".join(lines)


def _call_llm_structured(question: str, chunks: List[RetrievedChunk]) -> str:
    """Chama o LLM com o system prompt estruturado e o contexto formatado."""
    llm = get_chat_llm()
    context_str = format_context(chunks)
    enrichment = _get_knowledge_enrichment(question)
    if enrichment:
        context_str = context_str + "\n\n" + enrichment

    user_content = (
        f"Pergunta do jogador: {question}\n\n"
        f"Contexto (trechos dos livros 3D&T):\n---\n{context_str}\n---\n\n"
        "Siga ESTRITAMENTE o formato exigido no system prompt."
    )

    messages = [
        SystemMessage(content=STRUCTURED_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = llm.invoke(messages)
    return getattr(response, "content", str(response))


def generate_structured_answer(
    question: str,
    max_retries: int = 3,
    k: int | None = None,
) -> Tuple[QAResult, GenerationMetrics]:
    """
    Gera uma resposta estruturada (formato 3D&T) usando o pipeline de RAG.

    - Usa `retrieve_relevant_chunks` para buscar contexto.
    - Tenta até `max_retries` vezes fazer o LLM obedecer ao formato.
    - Se não conseguir, retorna mensagem de falha estruturada.
    """
    chunks = retrieve_relevant_chunks(question, k=k)

    if not chunks:
        msg = (
            "Não encontrei trechos relevantes nos livros indexados. "
            "Verifique se o índice foi construído e se há PDFs no diretório configurado."
        )
        metrics = GenerationMetrics(
            citacao_presente=False,
            fonte_citada=False,
            formula_presente=False,
            confidence_score=0.0,
        )
        qa = QAResult(answer=msg, sources=[])
        _log_response(question, qa.answer, metrics, [])
        return qa, metrics

    # Proxy simples de confiança: proporção de chunks retornados em relação a k
    k_effective = k or retrieval_config.k or 1
    conf = min(1.0, len(chunks) / float(k_effective))

    last_answer = ""
    last_metrics: GenerationMetrics | None = None

    # Heurística: se o contexto tem números, esperamos fórmula/mecânica
    had_numeric_context = any(any(ch.isdigit() for ch in c.content) for c in chunks)

    for attempt in range(1, max_retries + 1):
        logger.info("Gerando resposta estruturada (tentativa %d)...", attempt)
        answer = _call_llm_structured(question, chunks)
        metrics = _validate_response(answer, had_numeric_context)
        metrics.confidence_score = conf

        last_answer = answer
        last_metrics = metrics

        if _has_required_blocks(answer) and metrics.citacao_presente and metrics.fonte_citada:
            qa = QAResult(
                answer=answer,
                sources=[c.metadata for c in chunks],
            )
            _log_response(question, answer, metrics, chunks)
            return qa, metrics

        # Regenerar: falta 📜, 🎲 ou 📖 (max 3x)
        question = (
            question
            + "\n\nATENÇÃO: sua resposta anterior NÃO contém todos os blocos obrigatórios: "
              "📜 REGRA LITERAL (com citação entre aspas), 🎲 EXPLICAÇÃO, 📖 FONTE PRIMÁRIA (com página). "
              "Repita a resposta com EXATAMENTE esses blocos."
        )

    # Se chegou aqui, não conseguiu resposta estruturada válida
    fallback_msg = "Não foi possível extrair resposta estruturada."
    qa = QAResult(answer=fallback_msg, sources=[c.metadata for c in chunks])
    # Garante métricas finais
    if last_metrics is None:
        last_metrics = GenerationMetrics(
            citacao_presente=False,
            fonte_citada=False,
            formula_presente=False,
            confidence_score=conf,
        )
    _log_response(question, last_answer or fallback_msg, last_metrics, chunks)
    return qa, last_metrics

