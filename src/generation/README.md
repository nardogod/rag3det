## `src/generation` – camada de geração com LLM

Tudo que controla **como o modelo responde** (prompts, provedores de LLM, chain de QA) está aqui.

- **Se você quer mudar prompts, estilo de resposta ou quão restrito o sistema é**: veja `prompts.py`.
- **Se você quer trocar entre Ollama/OpenAI ou mudar nome do modelo**: veja `llm_provider.py` e as variáveis no `.env`.
- **Se você quer o “cérebro” que recebe a pergunta e devolve a resposta final**: veja `qa_chain.py`.

Arquivos principais (que vamos criar):
- `llm_provider.py` – escolhe e configura o LLM (Ollama ou OpenAI).
- `prompts.py` – textos de system prompt e templates de usuário.
- `qa_chain.py` – monta a cadeia RAG (retrieval + geração de resposta).

