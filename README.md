## Projeto RAG 3D&T + Idle RPG

Projeto híbrido com duas frentes:

- **Backend RAG em Python** para responder perguntas sobre os livros de 3D&T usando ingestão de PDFs, embeddings, ChromaDB, retrieval híbrido e reranker.
- **Frontend Idle RPG em React + TypeScript** com bestiário, ficha de personagem, combate e dados estruturados do universo 3D&T.

Este repositório foi organizado para servir tanto como base de desenvolvimento quanto como portfólio técnico para vagas de **ML/IA/RAG**, **Backend Python** e **Full Stack**.

## Stack

- **Backend:** Python, Streamlit, FastAPI, LangChain, ChromaDB, sentence-transformers, BM25, SQLite
- **Frontend:** React 19, TypeScript, Vite, Zustand, Tailwind CSS
- **IA aplicada:** embeddings locais/fine-tuned, retrieval híbrido, reranker cross-encoder, reindexação por domínio

## Estrutura do repositório

- `src/` — backend Python: ingestão, embeddings, vector store, retrieval, geração, avaliação
- `app/` — interface Streamlit para o assistente RAG
- `scripts/` — build do índice, reindexação por domínio e utilitários
- `frontend/` — aplicação React do jogo idle
- `docs/` — documentação técnica e materiais de estudo
- `.env.example` — referência segura de configuração local e de deploy

## Links de portfólio

- **Frontend do jogo:** `adicione-aqui-o-link-do-vercel-ou-netlify`
- **Assistente RAG (Streamlit):** `adicione-aqui-o-link-do-streamlit`
- **Repositório GitHub:** `adicione-aqui-o-link-do-repo-publico`

## Rodando localmente

### Backend RAG

1. Copie `.env.example` para `.env`.
2. Ajuste `SOURCE_PDF_DIR` para a pasta dos PDFs ou use `data/raw`.
3. Escolha o provedor de LLM:
   - local: `LLM_PROVIDER="ollama"`
   - deploy/nuvem: `LLM_PROVIDER="openai"`
4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Construa o índice:

```bash
python scripts/build_index.py
```

6. Suba o chat:

```bash
streamlit run app/main.py
```

7. Teste uma pergunta pelo terminal:

```bash
python scripts/test_query.py "Sua pergunta"
```

### Frontend

```bash
cd frontend
npm install
npm run build
npm run dev
```

O chat público fica no app Streamlit. O frontend publicado no Vercel fica focado no jogo.

## Deploy recomendado

### Frontend

Publicar o `frontend/` em **Vercel** ou **Netlify**:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`

Como a aplicação usa `BrowserRouter`, este repositório já inclui configuração para fallback de rotas no deploy estático.

### Backend RAG

Publicar o chat em **Streamlit Community Cloud** ou **Railway**:

- Entry point recomendado: `streamlit_app.py`
- Dependências: `requirements.txt`
- Variáveis de ambiente: baseadas em `.env.example`
- Provedor recomendado em nuvem: `openai`

Importante:

- não publique PDFs brutos;
- não suba `data/chroma/`, `models/` ou caches locais;
- para deploy público, use um índice já preparado ou mova o armazenamento para um serviço externo.

## O que não vai para o Git

O `.gitignore` da raiz protege os principais artefatos locais:

- `.env`
- `data/raw/`
- `data/chroma/`
- `data/embedding_cache/`
- `data/processed/`
- `models/`
- `frontend/node_modules/`
- `frontend/dist/`

## Documentação útil

- `docs/CURSO_RAG_ML_PORTFOLIO.md`
- `docs/CURSO_RAG_ML_PORTFOLIO_EXTENSO.md`
- `docs/GIT_E_DEPLOY.md`
- `docs/STREAMLIT_DEPLOY.md`

## Observações práticas

- Se o backend estiver configurado com Ollama e você receber erro de conexão, troque para OpenAI em deploy ou rode `ollama serve` localmente.
- Se uma resposta estiver ruim, aumente `RETRIEVAL_K` e mantenha `RERANKING_ENABLED="true"`.
- Se o objetivo for portfólio rápido, publique o frontend primeiro e depois suba a demo do RAG.

