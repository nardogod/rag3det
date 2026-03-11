## `scripts` – utilitários de linha de comando

Scripts simples para rodar tarefas comuns sem abrir a interface Streamlit.

- **Se você quer (re)construir o índice a partir dos PDFs**: use `build_index.py`.
- **Se você quer testar rapidamente uma pergunta no terminal**: use `test_query.py`.

Arquivos principais (execute na raiz do projeto):
- `build_index.py` – roda ingestão + criação do índice Chroma: `python scripts/build_index.py`
- `test_query.py` – envia uma pergunta ao RAG e imprime resposta + fontes: `python scripts/test_query.py "Sua pergunta"`

