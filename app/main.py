"""
Interface de chat Streamlit para o RAG 3D&T.

Execute na raiz do projeto:
  streamlit run app/main.py

- Layout, textos e controles: tudo é configurado aqui.
- Se você quiser mudar o visual ou adicionar filtros, edite este arquivo.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Garante que o pacote `src` seja encontrado (raiz do projeto = diretório atual)
if Path.cwd() != Path(__file__).resolve().parents[1]:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from src.generation.qa_chain import answer_question
from src.evaluation.response_validator import validate_response
from src.evaluation.feedback_loop import save_feedback


st.set_page_config(
    page_title="Assistente 3D&T – RAG",
    page_icon="📖",
    layout="centered",
)

st.title("Assistente 3D&T")
st.caption("Perguntas sobre regras, magias, vantagens e monstros com base nos livros indexados.")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

enable_index_rebuild = os.getenv("ENABLE_INDEX_REBUILD", "true").lower() == "true"

# Sidebar: parâmetros e botão de rebuild
with st.sidebar:
    st.header("Configurações")
    k = st.slider("Quantidade de trechos (k)", min_value=2, max_value=15, value=6, step=1)
    debug_mode = st.checkbox("Modo debug (mostrar fontes e enviar feedback)", value=False)
    st.divider()
    st.subheader("Índice")
    if enable_index_rebuild:
        if st.button("Reconstruir índice a partir dos PDFs"):
            with st.spinner("Carregando PDFs, limpando texto e gerando chunks..."):
                try:
                    from src.ingestion.pipeline import run_ingestion
                    from src.vectorstore.chroma_store import (
                        build_or_update_vectorstore,
                    )

                    chunks = run_ingestion()
                    if not chunks:
                        st.warning("Nenhum PDF foi carregado. Verifique SOURCE_PDF_DIR no .env e se há arquivos .pdf no diretório.")
                    else:
                        with st.spinner("Gerando embeddings e salvando no Chroma..."):
                            build_or_update_vectorstore(chunks)
                        st.success(f"Índice reconstruído com {len(chunks)} chunks.")
                except Exception as e:
                    st.error(f"Erro ao reconstruir índice: {e}")
    else:
        st.caption("Reconstrução do índice desabilitada neste ambiente.")

# Histórico do chat
last_user_message = None
for idx, msg in enumerate(st.session_state["messages"]):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "user":
            last_user_message = msg["content"]
        if msg.get("sources"):
            with st.expander("Fontes consultadas"):
                for s in msg["sources"]:
                    book = s.get("book_title", "?")
                    section = s.get("section", "?")
                    page = s.get("page", "?")
                    st.text(f"{book} | {section} | pág. {page}")
        if msg["role"] == "assistant" and debug_mode:
            if st.button("Esta resposta está incorreta", key=f"bad_{idx}"):
                # Valida automaticamente e salva feedback negativo
                sources = msg.get("sources", [])
                validation = validate_response(msg["content"], [])
                save_feedback(
                    query=last_user_message or "",
                    response=msg["content"],
                    user_rating=-1,
                    chunks=sources,
                    rerank_scores=[],
                    validation=validation,
                )
                st.success("Feedback registrado. Obrigado!")

# Input do usuário
if prompt := st.chat_input("Sua pergunta sobre 3D&T"):
    st.session_state["messages"].append({"role": "user", "content": prompt, "sources": []})

    with st.chat_message("user"):
        st.markdown(prompt)

    reply_content = ""
    reply_sources: list = []

    with st.chat_message("assistant"):
        with st.spinner("Buscando nos livros e gerando resposta..."):
            try:
                result = answer_question(prompt, k=k)
                reply_content = result.answer
                reply_sources = result.sources
                st.markdown(reply_content)
                if reply_sources:
                    with st.expander("Fontes consultadas"):
                        for s in reply_sources:
                            book = s.get("book_title", "?")
                            section = s.get("section", "?")
                            page = s.get("page", "?")
                            st.text(f"{book} | {section} | pág. {page}")
            except Exception as e:
                reply_content = f"Erro: {e}"
                st.error(reply_content)

    st.session_state["messages"].append({
        "role": "assistant",
        "content": reply_content,
        "sources": reply_sources,
    })
