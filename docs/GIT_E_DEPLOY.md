# Git e Deploy

Guia prático para transformar este projeto em um repositório público de portfólio e publicar suas duas partes: frontend do jogo e backend RAG.

## 1. Git local

Na raiz do projeto:

```bash
git init
git add .
git status
```

Antes do primeiro commit, confirme que estes itens **não** apareceram no `git status`:

- `.env`
- `data/raw/`
- `data/chroma/`
- `data/embedding_cache/`
- `data/processed/`
- `models/`
- `frontend/node_modules/`
- `frontend/dist/`

Se estiver tudo certo:

```bash
git commit -m "Prepare repository for portfolio and deployment"
```

## 2. GitHub

### Opção com GitHub CLI

```bash
gh repo create nome-do-repo --public --source . --remote origin --push
```

### Opção manual

1. Crie um repositório vazio no GitHub.
2. Na raiz do projeto:

```bash
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git branch -M main
git push -u origin main
```

## 3. Deploy do frontend

O frontend é a parte mais simples de publicar e deve ser o primeiro link do portfólio.

### Vercel

1. Importe o repositório no Vercel.
2. Configure:
   - Root directory: `frontend`
   - Install command: `npm install`
   - Build command: `npm run build`
   - Output directory: `dist`
3. Publique.

Este repositório já inclui `frontend/vercel.json` para fallback de rotas SPA.

### Netlify

1. Importe o repositório no Netlify.
2. Configure:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `dist`
3. Publique.

Este repositório já inclui `frontend/public/_redirects` para fallback de rotas SPA.

## 4. Deploy do backend RAG

### O que o backend precisa

O backend atual depende de:

- `requirements.txt`
- `app/main.py`
- variáveis de ambiente
- índice vetorial disponível para leitura
- um provedor de LLM remoto para deploy público

### Variáveis recomendadas para deploy

Use algo nesta linha:

```env
SOURCE_PDF_DIR=data/raw
CHROMA_DB_DIR=data/chroma
LLM_PROVIDER=openai
OPENAI_API_KEY=sua-chave
OPENAI_MODEL_NAME=gpt-4.1-mini
ENABLE_INDEX_REBUILD=false
RETRIEVAL_K=6
RETRIEVAL_CANDIDATE_K=20
RERANKING_ENABLED=true
QUERY_EXPANSION_ENABLED=true
```

### Streamlit Community Cloud

Boa opção para demo pública simples.

1. Conecte o repositório.
2. Escolha `app/main.py` como arquivo principal.
3. Adicione as variáveis de ambiente.
4. Publique.

Use Streamlit Cloud se você tiver uma estratégia para o índice já pronto. Como este projeto usa Chroma local, o caminho mais simples é publicar uma demo com um índice leve e já preparado.

### Railway

Melhor opção se você quiser uma demo mais próxima do projeto real.

1. Conecte o repositório no Railway.
2. Configure o start command:

```bash
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

3. Adicione as variáveis de ambiente.
4. Se precisar persistência do índice e do feedback, use volume montado para `data/`.

## 5. Estratégia recomendada para dados e índice

Para um portfólio público, use esta ordem:

1. Publique o frontend.
2. Publique o backend RAG com LLM remoto.
3. Não suba PDFs brutos, modelos locais ou caches.
4. Se o índice local estiver muito grande, prefira:
   - uma demo menor com índice enxuto, ou
   - migrar o vector store para um serviço gerenciado depois.

## 6. O que atualizar depois da publicação

Depois que os links existirem, atualize o `README.md`:

- `Frontend do jogo`
- `Assistente RAG`
- `Repositório GitHub`

## 7. Ordem prática de execução

1. Validar build do frontend.
2. Fazer `git init`.
3. Subir para GitHub.
4. Publicar frontend no Vercel.
5. Configurar backend com OpenAI.
6. Publicar backend no Streamlit Cloud ou Railway.
7. Colocar os links no `README.md` e no currículo.
