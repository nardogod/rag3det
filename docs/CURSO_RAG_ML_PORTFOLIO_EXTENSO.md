# Curso: RAG, Pipeline de Dados e Avaliação para Portfólio ML/IA — Versão Extensa

**Público:** Quem quer desenvolver um projeto RAG e usar como portfólio para vagas de ML/IA/RAG, usando Cursor (ou outra IA) como copiloto.  
**Objetivo:** Dominar os conceitos, a implementação e a narrativa para entrevistas; conseguir evoluir o sistema com autonomia.

---

## Índice

1. [Pré-requisitos e conhecimentos base](#1-pré-requisitos-e-conhecimentos-base)
2. [Visão geral do pipeline RAG (fluxo completo)](#2-visão-geral-do-pipeline-rag-fluxo-completo)
3. [Configuração do projeto (.env e YAML)](#3-configuração-do-projeto-env-e-yaml)
4. [Ingestão de PDFs](#4-ingestão-de-pdfs)
5. [Chunking](#5-chunking)
6. [Embeddings: locais e fine-tuned](#6-embeddings-locais-e-fine-tuned)
7. [Banco vetorial (ChromaDB)](#7-banco-vetorial-chromadb)
8. [Retrieval híbrido (vetorial + BM25) e query expansion](#8-retrieval-híbrido-vetorial--bm25-e-query-expansion)
9. [Reranker (cross-encoder)](#9-reranker-cross-encoder)
10. [Reindexação por domínio e documentos estruturados](#10-reindexação-por-domínio-e-documentos-estruturados)
11. [Pipeline de extração e enriquecimento a partir de PDFs](#11-pipeline-de-extração-e-enriquecimento-a-partir-de-pdfs)
12. [Avaliação e feedback de respostas](#12-avaliação-e-feedback-de-respostas)
13. [Fluxo completo: da pergunta à resposta (QA chain)](#13-fluxo-completo-da-pergunta-à-resposta-qa-chain)
14. [Como estudar com Cursor/IA e preparar entrevistas](#14-como-estudar-com-cursoria-e-preparar-entrevistas)
15. [Checklist e perguntas típicas de entrevista](#15-checklist-e-perguntas-típicas-de-entrevista)
16. [Próximos passos e exercícios](#16-próximos-passos-e-exercícios)

---

## 1. Pré-requisitos e conhecimentos base

### 1.1 O que você precisa saber

| Tema | Nível mínimo | Por quê |
|------|----------------|--------|
| **Python** | Intermediário: funções, classes, tipos, `pathlib`, `dataclasses`, `typing`, `Optional`, list/dict comprehensions | Todo o backend é Python; configs e tipos estão em todo lugar. |
| **Ambiente** | `.env`, `pip`, `venv`, variáveis de ambiente (`os.getenv`) | O projeto usa `SOURCE_PDF_DIR`, `CHROMA_DB_DIR`, `EMBEDDING_MODEL`, etc. |
| **Conceitos de ML/IA** | Embedding (vetor que representa texto), similaridade (cosseno), diferença entre “busca semântica” e “busca por palavra” | Explicar RAG, retrieval e reranker em entrevista. |
| **RAG** | Fluxo: pergunta → buscar trechos relevantes → montar contexto → LLM gera resposta usando só o contexto | É o core do produto. |
| **Git** | Básico: clone, commit, branch, push, README | Repositório como portfólio. |

### 1.2 Conceitos que vale aprofundar (para entrevistas)

- **Embedding:** Representação densa do texto em um vetor de N dimensões (ex.: 384 ou 768). Textos semânticamente próximos têm vetores próximos (menor distância ou maior cosseno).
- **Bi-encoder vs cross-encoder:** Bi-encoder: query e documento são embedados separadamente; a similaridade é calculada entre os vetores (rápido, escala bem). Cross-encoder: o par (query, documento) entra junto no modelo e sai um score (mais preciso, mas custoso — usamos só em poucos candidatos).
- **BM25:** Modelo probabilístico de ranking por termos; penaliza documentos longos e favorece termos raros; não entende sinônimos, mas é ótimo para nomes próprios e siglas.
- **Recall vs precisão (em RAG):** Recall: quantos dos trechos realmente relevantes foram recuperados. Precisão: dos recuperados, quantos são relevantes. O retriever prioriza recall (trazer muitos candidatos); o reranker melhora precisão nos top-K.

### 1.3 Opcional mas útil

- Noção de **sentence-transformers** (modelos que transformam texto em vetor).
- **LangChain:** abstrações `Document`, `Embeddings`, `VectorStore`; não é obrigatório decorar, mas saber que “Document tem page_content e metadata” ajuda.
- **SQLite:** para armazenar feedback (tabela, INSERT, SELECT).

---

## 2. Visão geral do pipeline RAG (fluxo completo)

Do ponto de vista de “uma pergunta do usuário”, o fluxo é:

```
[Pergunta] 
    → (opcional) Query expansion (variantes da pergunta)
    → Busca vetorial no Chroma (top candidate_k)
    → Busca BM25 no corpus (top candidate_k) — se híbrido ativo
    → Fusão de scores (pesos semântico + BM25)
    → Reranker (cross-encoder) nos candidatos fusionados → top k
    → Montagem do contexto (format_context)
    → LLM (system prompt + user prompt com contexto)
    → Pós-processamento (expandir siglas)
    → [Resposta] + fontes
```

Do ponto de vista de **construção do índice** (offline):

```
[PDFs em data/raw ou SOURCE_PDF_DIR]
    → Load PDFs (página a página → Document com metadata)
    → Limpeza (text_cleaning)
    → Chunking (RecursiveCharacterTextSplitter, preservar tabelas)
    → (opcional) NER / enriquecimento de metadados
    → Embedding de cada chunk (com cache em disco)
    → Chroma: from_documents() → índice persistido
```

**Reindexação por domínio** (em paralelo ou depois):

```
[JSON de domínio, ex.: monstros_modelo_enriquecido.json]
    → Para cada item: formatar em texto (ex.: ficha tabela)
    → Criar Document(s) com metadata (tipo, nome, livro)
    → get_vectorstore().add_documents(docs)  # adiciona ao mesmo Chroma
```

Arquivos-chave para seguir esse fluxo no código: `src/generation/qa_chain.py` (pergunta → resposta), `src/retrieval/pipeline.py` (retrieve), `src/ingestion/pipeline.py` (ingestão), `scripts/build_index.py` (build do índice), `scripts/reindexar_monstros.py` (exemplo de reindexação).

---

## 3. Configuração do projeto (.env e YAML)

Toda a configuração que importa para o RAG está centralizada em `src/config.py`. A prioridade é: **variável de ambiente > config/settings.yaml > valor padrão**.

### 3.1 Caminhos (Paths)

| Variável | Uso |
|----------|-----|
| `SOURCE_PDF_DIR` | Diretório dos PDFs (default: `data/raw`) |
| `CHROMA_DB_DIR` | Onde o Chroma persiste o índice (default: `data/chroma`) |

### 3.2 Embeddings (EmbeddingConfig)

| Variável | Uso |
|----------|-----|
| `EMBEDDING_MODEL` | Caminho do modelo fine-tuned (ex.: `models/embeddings/3dt_finetuned`) — se existir, tem prioridade |
| `EMBEDDING_MODEL_NAME` | Nome do modelo HuggingFace quando não há fine-tuned |
| `EMBEDDING_FALLBACK` | Modelo usado quando o fine-tuned não existe ou falha |

### 3.3 Chunking (ChunkingConfig)

| Variável | Uso |
|----------|-----|
| `CHUNK_SIZE` | Tamanho máximo do chunk em caracteres (default: 1000) |
| `CHUNK_OVERLAP` | Sobreposição entre chunks (default: 200) |

### 3.4 Retrieval (RetrievalConfig)

| Variável | Uso |
|----------|-----|
| `RETRIEVAL_K` | Número final de trechos enviados ao LLM (default: 6) |
| `RETRIEVAL_CANDIDATE_K` ou `CANDIDATE_K` | Candidatos na primeira etapa, antes do rerank (default: 20) |
| `HYBRID_SEMANTIC_WEIGHT` | Peso do score vetorial na fusão (default: 0.7) |
| `HYBRID_BM25_WEIGHT` | Peso do BM25 na fusão (default: 0.3) |
| `HYBRID_ENABLED` | Ativar busca híbrida (true/false) |
| `QUERY_EXPANSION_ENABLED` | Ativar expansão de query (true/false) |
| `RERANKING_ENABLED` | Ativar reranker cross-encoder (true/false) |

### 3.5 Onde alterar

- Para teste rápido: crie um `.env` na raiz e defina só o que quiser sobrescrever.
- Para documentar defaults versionados: use `config/settings.yaml` com estrutura tipo `chunking.chunk_size`, `retrieval.top_k`, etc. O código usa `_get_setting("chunking.chunk_size", 1000)`.

---

## 4. Ingestão de PDFs

### 4.1 O que é

Carregar PDFs do disco e transformá-los em uma lista de **Document** (LangChain): cada documento tem `page_content` (texto da página) e `metadata` (livro, página, etc.). É a entrada do pipeline; sem ingestão, não há chunks para embedar.

### 4.2 Onde está no projeto

- **`src/ingestion/pdf_loader.py`:**
  - `load_pdfs_from_source_dir(source_dir=None)`: lista todos os `.pdf` em `paths.source_pdf_dir` (ou no diretório passado), carrega com `PyPDFLoader`; se falhar (PDF malformado), tenta `PyMuPDFLoader`. Cada página vira um `Document`. Metadados são enriquecidos em `_enrich_metadata`: `source`, `page`, `book_title`, `content_type`, `section` (placeholder).
- **`src/ingestion/pipeline.py`:**
  - `run_ingestion(source_dir=None)`: garante diretórios, chama `load_pdfs_from_source_dir`, passa os documentos ao `DocumentProcessor` (limpeza + chunking) e retorna a lista de chunks.

### 4.3 Detalhes de implementação

- **Normalização do nome do livro:** `_normalize_book_title_from_path(pdf_path)`: o stem do arquivo (ex.: `3det_alpha_magias`) vira “3det alpha magias” para exibição.
- **Tratamento de erro:** PDFs que falham com ambos os loaders são ignorados com log; o restante segue. Assim um PDF corrompido não derruba o build.
- **Ordem:** PDFs são listados com `rglob("*.pdf")` e ordenados; a ordem influencia a ordem dos chunks no índice (útil para reprodutibilidade).

### 4.4 Conceitos para mercado

- **Document loader:** Abstração que lê uma fonte (PDF, HTML, API, Notion) e produz uma lista de `Document`. Em outros projetos você pode ter loaders para Confluence, Slack, etc.
- **Metadados ricos:** Livro, página e seção permitem citação (“conforme Manual dos Monstros, p. 42”) e filtros no retrieval (ex.: buscar só em “Magias”).

### 4.5 O que você deve conseguir

- Explicar: “Os PDFs são carregados por um loader (PyPDF ou PyMuPDF como fallback), cada página vira um Document com book_title, page e source; depois passam por limpeza e chunking.”
- Saber onde alterar o diretório de PDFs (`SOURCE_PDF_DIR` ou `paths.source_pdf_dir`) e onde adicionar um novo loader (em `pdf_loader.py`, e eventualmente em `run_ingestion` se a fonte for outra).

---

## 5. Chunking

### 5.1 O que é

Quebrar textos longos em **chunks** de tamanho controlado, com **overlap** (sobreposição) para evitar cortar frases ou parágrafos no meio. O chunk é a unidade que será embedada e armazenada no banco vetorial; a pergunta do usuário será comparada a esses chunks.

### 5.2 Onde está no projeto

- **`src/ingestion/chunking.py`:**
  - `chunk_documents(documents)`: para cada documento, pré-processa o texto com `_preprocess_tables` (agrupa linhas que parecem tabela para não cortar no meio), aplica `RecursiveCharacterTextSplitter` com `chunk_size` e `chunk_overlap` de `chunking_config`, separadores `["\n\n", "\n", ". ", " ", ""]`. Para cada chunk gerado, infere uma `section` (ex.: “Magias”, “Vantagens”) com `_infer_section_from_chunk` e anexa ao metadata.
  - Heurística de tabela: linhas com `|` ou com pelo menos 2 `;` são consideradas tabela; blocos de linhas do mesmo “tipo” (tabela vs não-tabela) são mantidos juntos antes de splitar.
- **`src/ingestion/document_processor.py`:**
  - `DocumentProcessor.process(documents)`: chama `clean_documents` (text_cleaning) e depois `chunk_documents`; padroniza `section_title` nos metadados.

### 5.3 Limpeza de texto (pré-chunking)

- **`src/ingestion/text_cleaning.py`:**
  - Junta palavras quebradas por hífen no fim da linha (ex.: “magia-\nelemental” → “magiaelemental”).
  - Normaliza múltiplos espaços e trim de linhas.
  - Único ponto central para adicionar regras de limpeza específicas do domínio.

### 5.4 Parâmetros e efeito

- **chunk_size (ex.: 1000):** Chunks maiores dão mais contexto ao LLM por trecho, mas podem misturar assuntos e reduzir precisão do retrieval; chunks menores são mais focados, mas pode faltar contexto.
- **chunk_overlap (ex.: 200):** Reduz perda de informação nas fronteiras; aumenta redundância e número de vetores (mais custo de embedding e armazenamento).

### 5.5 Conceitos para mercado

- **RecursiveCharacterTextSplitter:** Tenta quebrar primeiro por `\n\n`, depois `\n`, depois `. `, etc., respeitando o tamanho máximo; é o splitter mais usado em RAG.
- **Chunking consciente de estrutura:** Tabelas, listas e seções podem ser preservadas (pré-processamento ou splitters por cabeçalho) para não cortar no meio.

### 5.6 O que você deve conseguir

- Dizer: “Usamos RecursiveCharacterTextSplitter com tamanho e overlap configuráveis; há pré-processamento para não cortar tabelas no meio e inferência de seção por chunk.”
- Ajustar `CHUNK_SIZE`/`CHUNK_OVERLAP` e explicar o trade-off recall/custo.

---

## 6. Embeddings: locais e fine-tuned

### 6.1 O que é

**Embedding** é a transformação de texto em um vetor numérico. A “busca semântica” compara o vetor da pergunta com os vetores dos chunks (ex.: similaridade de cosseno). Modelo **local** roda na sua máquina (sentence-transformers); **fine-tuned** é treinado no seu domínio (ex.: 3D&T) para que termos do jogo fiquem mais próximos semanticamente.

### 6.2 Onde está no projeto

- **`src/embedding/local_embeddings.py`:**
  - Resolve o modelo: primeiro tenta o caminho em `embedding_config.embedding_model` (ex.: `models/embeddings/3dt_finetuned/`); se existir `config_sentence_transformers.json` ali, usa esse modelo. Senão, usa `embedding_config.model_name` ou `embedding_fallback`.
  - **NormalizedEmbeddings:** wrapper que aplica normalização L2 aos vetores (norma 1), para que similaridade cosseno = produto interno.
- **`src/embedding/pipeline.py`:**
  - `get_embedding_function()`: retorna o embedding com cache em disco (CachedEmbeddings). `get_embedding_function_baseline()`: retorna o fallback (para índice A/B).
- **`src/embedding/cached_embeddings.py`:**
  - **CachedEmbeddings:** chave de cache = hash do texto + model_id; armazenamento em `data/embedding_cache` com shelve (um arquivo por modelo). Na primeira vez que um texto aparece, chama o modelo; nas próximas, lê do disco. Trocar modelo = novo prefixo = novo cache.

### 6.3 Fine-tuning (resumo do que o projeto faz)

- **`src/ml/training/finetune_embeddings.py`:**
  - Dataset: triplas (anchor, positive, negative) em JSONL em `data/training/train_triples.jsonl` e `val_triples.jsonl`.
  - Treino: pares (anchor, positive) com **MultipleNegativesRankingLoss** (os negativos vêm in-batch). Módulo **Normalize** é adicionado ao modelo para L2. Até 5 epochs com early stopping (patience 2). Modelo base: `paraphrase-multilingual-MiniLM-L12-v2` (ou fallback menor se OOM).
  - Saída: modelo salvo em `models/embeddings/3dt_finetuned_v2/` (ou caminho configurável).
- **Geração de dataset:** scripts `generate_embedding_dataset.py` / `generate_embedding_dataset_v2.py` produzem as triplas a partir de queries e chunks relevantes/irrelevantes.

### 6.4 Conceitos para mercado

- **Bi-encoder:** Query e documento são embedados separadamente; a similaridade é calculada entre os vetores. Escala bem para milhões de documentos.
- **Fine-tuning para domínio:** Com triplas (pergunta, positivo, negativo), o modelo aprende a puxar para perto o positivo e afastar o negativo; em domínios com jargão (RPG, jurídico, médico) isso melhora muito o recall.
- **Normalização L2:** Vetores com norma 1; distância euclidiana e cosseno ficam ligadas; muitos vector stores assumem vetores normalizados.

### 6.5 O que você deve conseguir

- Explicar: “Usamos modelo de embeddings local ou fine-tuned para o domínio; há cache em disco por texto e model_id, e fallback para modelo genérico. O fine-tuning usa triplas e MultipleNegativesRankingLoss.”
- Saber onde trocar modelo (config) e onde está o script de fine-tuning e que formato de triplas ele espera.

---

## 7. Banco vetorial (ChromaDB)

### 7.1 O que é

Banco que armazena vetores e permite **busca por similaridade** (k-NN). Você adiciona documentos já embedados; na query, o sistema embeda a pergunta e busca os k vetores mais próximos (ex.: por distância L2 ou cosseno).

### 7.2 Onde está no projeto

- **`src/vectorstore/chroma_store.py`:**
  - **Collections:** `3det_rag` (embedding principal/fine-tuned) e `3det_rag_baseline` (embedding genérico) para A/B test.
  - **build_or_update_vectorstore(documents, use_baseline=False):** Remove a collection existente (para evitar erro de dimensão ao trocar de modelo), cria nova com `Chroma.from_documents(documents, embedding=..., persist_directory=..., collection_name=...)`.
  - **get_vectorstore(use_baseline=False):** Carrega o Chroma existente (persist_directory + collection_name + embedding function). Não recria.
  - **get_all_documents(vectorstore=None):** Retorna todos os documentos da collection (usado pelo BM25: o corpus do BM25 é todo o texto no Chroma).

### 7.3 Por que deletar a collection ao trocar de modelo

Chroma (e a maioria dos vector stores) exige que todos os vetores da mesma collection tenham a **mesma dimensão**. Se você treinar um novo modelo com dimensão diferente (ex.: 384 → 768), a collection antiga não serve; por isso o build deleta e recria.

### 7.4 Conceitos para mercado

- **Vector store:** Armazenamento + índice k-NN; Chroma, Pinecone, Weaviate, Qdrant, etc.
- **Collection:** Namespace de vetores; cada uma tem dimensão fixa e pode ter seu próprio embedding function.

### 7.5 O que você deve conseguir

- Dizer: “O Chroma persiste em disco; temos duas collections, uma para embedding principal e uma baseline. O build recria a collection para aceitar nova dimensão; o get só carrega. O BM25 usa get_all_documents para ter o corpus em memória.”

---

## 8. Retrieval híbrido (vetorial + BM25) e query expansion

### 8.1 O que é

**Híbrido:** combinar busca **semântica** (vetorial) com busca **léxica** (BM25). A vetorial captura sinônimos e conceitos; o BM25 ajuda em nomes próprios, siglas e termos exatos. **Query expansion:** gerar variantes da pergunta (ex.: frase-chave, termos do domínio) e buscar com todas; depois agregar e deduplicar resultados.

### 8.2 Onde está no projeto

- **`src/retrieval/pipeline.py`:**
  - **retrieve_relevant_chunks(query, k, use_baseline):** Lê config (k, candidate_k, hybrid_enabled, query_expansion_enabled, reranking_enabled). Se query expansion ativo, chama `expand_query_variants(query)` e obtém até 3 variantes. Para cada variante: (1) `vectorstore.similarity_search_with_score(q, k=candidate_k)`; (2) se híbrido, BM25 sobre `get_all_documents()` com `rank_bm25.BM25Okapi`, top candidate_k. Scores semânticos: distância → similaridade com `1/(1+distance)`. BM25 e semântico são normalizados (min-max 0–1). Fusão: `w_sem * norm_sem + w_bm25 * norm_bm25`. Ordena por score combinado, pega top `candidate_k * 2` e passa ao reranker (se ativo) que devolve top k; senão, devolve top k da fusão. Retorna lista de `RetrievedChunk` (content, metadata, score).
- **`src/retrieval/query_expansion.py`:**
  - **expand_query_variants(query):** Até 3 variantes. Primeira: query original. Segunda: frase-chave (ex.: “O que é Invocação da Fênix?” → “Invocação da Fênix”) via `_key_phrase_from_query` (remove prefixos como “o que é”, “como funciona”). Terceira: expansão de domínio do dicionário `DOMAIN_3DET` (ex.: “fênix” → “Fênix magia elemental fogo”) ou fallback “regra de {key}”. Deduplica por texto em minúsculas.

### 8.3 Detalhes de implementação

- **Deduplicação:** Cada documento é identificado por uma chave estável (hash de content + source + page). Ao agregar resultados de várias variantes, o mesmo chunk não entra duas vezes; o melhor score (semântico ou BM25) é mantido.
- **Pesos:** Default 0.7 semântico e 0.3 BM25; em domínios com muitos nomes próprios, aumentar BM25 pode ajudar.

### 8.4 Conceitos para mercado

- **Hybrid search:** Sempre que há glossário, siglas ou nomes exatos, híbrido melhora recall.
- **Query expansion:** Aumenta recall (mais variantes = mais chance de acertar o trecho); pode reduzir um pouco a precisão, por isso o reranker depois refina.
- **Reciprocal Rank Fusion (RRF):** Outra forma de juntar rankings (por posição em vez de score); aqui o projeto usa fusão por score normalizado.

### 8.5 O que você deve conseguir

- Explicar: “Fazemos busca vetorial e BM25, normalizamos os scores, combinamos com pesos configuráveis; opcionalmente expandimos a query em até 3 variantes e agregamos resultados; a lista fusionada vai para o reranker.”
- Saber onde ativar/desativar híbrido e query expansion (config) e onde ajustar pesos.

---

## 9. Reranker (cross-encoder)

### 9.1 O que é

Modelo que recebe o par **(query, documento)** e devolve um **score de relevância**. Não escala para milhões de documentos (seria preciso rodar o modelo para cada par), então é usado **depois** do retriever: o retriever traz dezenas de candidatos; o reranker reordena e devolve os top-k.

### 9.2 Onde está no projeto

- **`src/retrieval/reranker.py`:**
  - **CrossEncoderReranker:** Usa `sentence_transformers.CrossEncoder` (modelo padrão: `cross-encoder/ms-marco-MiniLM-L-6-v2`). Se existir modelo fine-tuned em `models/reranker/3dt_finetuned`, carrega esse. Recebe lista de pares (query, doc); o modelo devolve scores; ordena por score decrescente e devolve top_k.
  - **Frase-chave:** Para melhorar o par (query, doc), extrai a “frase-chave” da pergunta (ex.: “O que é Invocação da Fênix?” → “Invocação da Fênix”) e usa em lógica interna (key phrase) para montar o par, quando aplicável.
  - **rerank_results_with_scores(query, candidates, top_k):** Função chamada pelo pipeline; retorna lista de (Document, score).

### 9.3 Conceitos para mercado

- **Cross-encoder:** Vê query e documento juntos; pode capturar nuances que o bi-encoder perde; custo O(n) em número de candidatos, então n deve ser limitado (ex.: 20–50).
- **Pipeline em dois estágios:** Retriever (rápido, recall) → Reranker (lento, precisão nos top).

### 9.4 O que você deve conseguir

- Dizer: “Depois da busca híbrida, um cross-encoder reranka os candidatos; usamos modelo leve local e opcionalmente um fine-tuned para o domínio. O reranker é ligado/desligado por RERANKING_ENABLED.”

---

## 10. Reindexação por domínio e documentos estruturados

### 10.1 O que é

Além do índice “geral” (PDFs → chunks), criar **documentos estruturados** por domínio (monstros, magias, itens, vantagens, etc.): cada entidade vira um texto padronizado (ex.: ficha em tabela Markdown) e é adicionado ao Chroma com metadados (`tipo`, `nome`, `livro`). Assim o RAG encontra respostas sobre “Dragão do Ar” ou “Invocação da Fênix” mesmo quando o livro está em prosa; a ficha é um resumo denso e completo.

### 10.2 Onde está no projeto

- **Scripts:** `scripts/reindexar_monstros.py`, `reindexar_magias.py`, `reindexar_itens_magicos.py`, `reindexar_vantagens.py`, `reindexar_personagem.py`, `reindexar_mestre.py`, `reindexar_regras_combate.py`, `reindexar_pericias.py`.
- **Formato de ficha (monstros):** `src/utils/formatar_monstro.py` — `formatar_ficha_monstro_tabela(monstro, incluir_descricao)` produz uma tabela Markdown com campos na ordem definida em `.cursor/rules/formato-ficha-monstro.mdc`: Nome, Características, PV/PM, Escala, Comportamento, Tamanho, Peso, Habitat, Combate, Ataques, Imunidades, Fraquezas, Habilidades, Movimento, Táticas, Tesouro, Fonte, Descrição (opcional). Campos vazios viram “—”.
- **Exemplo de fluxo (monstros):** `reindexar_monstros.py` carrega `data/processed/monstros/monstros_modelo_enriquecido.json` (ou extraídos/canônico), aplica complemento manual se existir, normaliza livro e gera `texto_completo` com `formatar_ficha_monstro_tabela` + `expandir_siglas_3dt`. Para cada monstro cria 2 Documents: um com só o nome (tipo_chunk: monstro_nome) e outro com o texto completo (tipo_chunk: monstro_completo). Metadados: `tipo`, `nome`, `tipo_criatura`, `livro`. Chama `get_vectorstore().add_documents(docs)` — **não** substitui o índice, só adiciona.

### 10.3 Padrão para criar um novo reindexar

1. Fonte de dados: JSON ou TSV em `data/processed/<domínio>/`.
2. Função de formatação: entidade → string (tabela ou texto estruturado).
3. Metadados consistentes: pelo menos `tipo`, `nome`, `livro` (ou equivalente).
4. Script: carregar dados, para cada item criar `Document(page_content=..., metadata=...)`, chamar `get_vectorstore().add_documents(docs)`.

### 10.4 Conceitos para mercado

- **Documentos estruturados:** Entidades viram texto padronizado; melhor para RAG e citação do que prosa longa.
- **Reindexação por domínio:** Permite atualizar só monstros (ou só magias) sem reprocessar todos os PDFs; útil em pipelines de dados que evoluem por fonte.

### 10.5 O que você deve conseguir

- Explicar: “Além do índice dos PDFs, temos scripts que carregam JSON por domínio, formatam em ficha e adicionam ao Chroma com metadados; assim o RAG encontra entidades específicas com texto rico.”
- Ser capaz de criar um novo `reindexar_*.py` seguindo o padrão (ex.: perícias).

---

## 11. Pipeline de extração e enriquecimento a partir de PDFs

### 11.1 O que é

**Extrair** entidades estruturadas (monstros, magias, itens) a partir dos PDFs (por regras, regex, ou modelo) e **enriquecer** com campos adicionais (descrição, táticas, tesouro). O resultado é JSON que alimenta a reindexação RAG e outras aplicações (ex.: frontend do jogo).

### 11.2 Onde está no projeto

- **Extração:** `src/ingestion/` — vários extratores (monstros, magias, tabelas); scripts como `extrair_monstros_modelo_enriquecido.py` orquestram extração e enriquecimento.
- **Dados:** `data/processed/monstros/`: `monstros_extraidos.json`, `monstros_canonico.json`, `monstros_modelo_enriquecido.json`, `monstros_canonico_complemento.json`, `piloto_extra_manual.json`. O “enriquecido” é a versão que junta extração + enriquecimento (descrição, etc.) e é usada pelo reindexador e pelo frontend (via copy-monstros).
- **Formatação e normalização:** `src/utils/formatar_monstro.py`, `normalizar_ocr.py`, `livro_normalizado.py`, `expandir_siglas_3dt.py`.
- **Scripts:** `enriquecer_todos_monstros.py`, `varredura_completa_monstros.py`, `sync_monstros_frontend.py`; no frontend, `npm run copy-monstros` copia `monstros_modelo_enriquecido.json` para `frontend/src/data/monstros.json`.

### 11.3 Conceitos para mercado

- **ETL para domínio:** Extrair → limpar → normalizar → enriquecer → publicar (para RAG, API, app).
- **Fonte única:** Um JSON (ou um banco) é a verdade para RAG e UI; evita divergência.
- **Enriquecimento:** Adicionar descrição, resumo ou campos derivados melhora retrieval e UX.

### 11.4 O que você deve conseguir

- Explicar: “Temos um pipeline que extrai monstros (e outros) dos PDFs, enriquece com descrições e normaliza; o resultado vira JSON que alimenta o reindexador e o frontend via script de cópia.”
- Diferenciar “extraídos”, “canônico” e “enriquecido” no projeto e onde está cada etapa.

---

## 12. Avaliação e feedback de respostas

### 12.1 O que é

**Validação automática:** regras que verificam se a resposta do RAG está aderente ao contexto (citação, fonte, números ancorados, sem linguagem vaga). **Feedback do usuário:** persistir quando o usuário marca “resposta incorreta” (ou similar) para análise e melhoria (treino de reranker/embeddings, priorização de correções).

### 12.2 Onde está no projeto

- **`src/evaluation/response_validator.py`:**
  - **validate_response(answer, chunks):** Retorna `ValidationResult` com flags e lista de regras violadas.
  - **Regra 1:** Deve haver pelo menos uma citação entre aspas duplas (`REGRA_1_SEM_CITACAO`).
  - **Regra 2:** Se houver linha “📖 FONTE PRIMÁRIA: …”, o texto deve bater com algum `book_title` dos chunks (`REGRA_2_FONTE_INVALIDA`).
  - **Regra 3:** Se a resposta mencionar números, ao menos um número deve aparecer dentro de alguma citação (`REGRA_3_NUMEROS_FORA_DA_CITACAO`).
  - **Regra 4:** Não pode conter “eu acho que”, “provavelmente”, “talvez” (`REGRA_4_HEDGE_LANGUAGE`).
  - `needs_review = True` se alguma regra for violada.
- **`src/evaluation/feedback_loop.py`:**
  - **save_feedback(query, response, user_rating, chunks, rerank_scores, validation):** Persiste em SQLite (`data/feedback.db`). Tabela: timestamp, query, response, user_rating (+1/0/-1), chunks_used (JSON), rerank_scores (JSON), validation_flags (JSON).
  - **analyze_feedback():** Retorna queries com baixa satisfação (avg_rating < 0) e total de entradas; útil para priorizar melhorias.

### 12.3 Uso na UI

No Streamlit, no modo debug há um botão “Esta resposta está incorreta” que chama `validate_response` e `save_feedback` com rating negativo, permitindo coletar casos problemáticos.

### 12.4 Conceitos para mercado

- **Avaliação de RAG:** Retrieval (recall@k, MRR), geração (faithfulness, relevância) e regras de negócio (citação obrigatória, fonte válida).
- **Feedback loop:** Dados de usuário podem alimentar fine-tuning de reranker/embeddings ou listas de “queries difíceis” para testes regressivos.

### 12.5 O que você deve conseguir

- Explicar: “Validamos a resposta com quatro regras (citação, fonte, números ancorados, sem hedge) e persistimos feedback em SQLite; temos função para analisar queries com baixa satisfação.”
- Saber onde estão as regras e onde o feedback é salvo e como consultar (analyze_feedback ou SQL direto).

---

## 13. Fluxo completo: da pergunta à resposta (QA chain)

### 13.1 Orquestração

- **`src/generation/qa_chain.py`:**
  - **answer_question(question, k=None):** Ponto de entrada usado pelo Streamlit e pela API.
  - Passos: (1) `retrieve_relevant_chunks(query=question, k=k)`; (2) se vazio, retorna mensagem de “não encontrei” e fontes vazias; (3) `format_context(chunks)` monta o bloco de contexto com [Livro | seção | pág. X] e expande siglas; (4) monta `user_message` com `USER_TEMPLATE` (pergunta + contexto); (5) chama o LLM com `SYSTEM_PROMPT` e a user message; (6) pós-processa a resposta com `expandir_siglas_3dt`; (7) retorna `QAResult(answer=..., sources=[metadata dos chunks])`.

### 13.2 Prompts

- **`src/generation/prompts.py`:**
  - **SYSTEM_PROMPT:** Define o assistente (3D&T), regras (só contexto, não inventar, citar livro/página, formato de atributos, etc.).
  - **USER_TEMPLATE:** “Pergunta do jogador: {question}\n\nTrechos relevantes:\n---\n{context}\n---\nResponda baseando-se somente no contexto acima.”
  - **format_context(chunks):** Numera os trechos, formata [Livro | seção | pág.], expande siglas no conteúdo.

### 13.3 Resumo em uma frase

“A pergunta passa pelo retrieval (expansion → vetorial + BM25 → fusão → reranker), o contexto é formatado e enviado ao LLM com um system prompt restritivo; a resposta é pós-processada e devolvida com as fontes.”

---

## 14. Como estudar com Cursor/IA e preparar entrevistas

- **Por tema:** Abra este curso e, para cada seção, abra os arquivos indicados. Peça ao Cursor: “Explique o fluxo deste arquivo em 3 frases” ou “Onde o chunk_size é usado?”.
- **Rastrear um fluxo:** Comece por “usuário pergunta no chat” → `qa_chain.answer_question` → `retrieve_relevant_chunks` → pipeline (vetorial, BM25, rerank) → `format_context` → LLM. Peça: “Mostre a chamada de retrieve em qa_chain”.
- **Criar um reindexar:** Copie `reindexar_monstros.py`, troque o JSON de entrada e a função de formatação; peça ao Cursor para adaptar metadados e nome do script.
- **Entrevista:** Treine em voz alta: “Meu RAG faz ingestão de PDFs, chunking com overlap e preservação de tabelas, embeddings locais ou fine-tuned com cache em disco, Chroma com duas collections, retrieval híbrido com BM25 e query expansion, reranker cross-encoder, reindexação por domínio com documentos estruturados (ex.: fichas de monstros), e avaliação/feedback em SQLite.”

---

## 15. Checklist e perguntas típicas de entrevista

### 15.1 Checklist de domínio

- [ ] **Ingestão:** Explicar de onde vêm os PDFs, qual loader, como são os metadados e onde alterar o diretório.
- [ ] **Chunking:** Dizer tamanho/overlap, separadores, pré-processamento de tabelas e inferência de seção.
- [ ] **Embeddings:** Diferenciar modelo local, fine-tuned e fallback; mencionar cache em disco e normalização L2.
- [ ] **Chroma:** Explicar as duas collections (principal vs baseline), build vs get, e por que a collection é recriada ao trocar de modelo.
- [ ] **Retrieval:** Descrever busca vetorial + BM25, normalização, fusão de scores, query expansion e deduplicação.
- [ ] **Reranker:** Dizer o que é cross-encoder, em que momento entra no pipeline e como ligar/desligar.
- [ ] **Reindexação por domínio:** Dar exemplo (monstros), formato de documento (ficha tabela), metadados e que é add_documents (não substitui o índice).
- [ ] **Pipeline de dados:** Descrever extração → enriquecimento → JSON → reindexar e frontend (copy-monstros).
- [ ] **Avaliação/feedback:** Citar as quatro regras de validação e onde o feedback é armazenado (SQLite) e analisado (analyze_feedback).

### 15.2 Perguntas típicas de entrevista

- **“Como funciona o retrieval no seu projeto?”** — Busca vetorial no Chroma + BM25 no corpus completo; normalizamos os scores e combinamos com pesos; opcionalmente expandimos a query em variantes e agregamos; depois um cross-encoder reranka os candidatos e devolvemos o top-k.
- **“Por que usar BM25 além do vetorial?”** — Para nomes próprios, siglas e termos exatos que o embedding pode “suavizar”; o híbrido melhora o recall nesses casos.
- **“O que é reranker e por que não usar só o retriever?”** — O reranker é um cross-encoder que vê (query, doc) junto e dá um score mais preciso; não escala para todo o corpus, então usamos só nos candidatos que o retriever trouxe.
- **“Como você avalia se a resposta do RAG está boa?”** — Regras automáticas (citação, fonte, números ancorados, sem hedge) e feedback do usuário persistido em SQLite para análise e melhoria.
- **“Como você adiciona novos tipos de conteúdo (ex.: perícias)?”** — Criar um JSON de domínio, uma função que formata cada item em texto (ex.: tabela), e um script que gera Documents com metadados e chama add_documents no Chroma (padrão reindexar_*).

---

## 16. Próximos passos e exercícios

- **Exercício 1:** Aumentar `RETRIEVAL_K` para 10 e `CANDIDATE_K` para 30; rodar algumas perguntas e observar se as respostas melhoram ou pioram (e o tempo).
- **Exercício 2:** Desligar o reranker (`RERANKING_ENABLED=false`) e comparar qualidade e latência com o reranker ligado.
- **Exercício 3:** Criar `scripts/reindexar_pericias.py` (ou outro domínio que você tenha em JSON): carregar o JSON, formatar cada item em texto, criar Documents com metadata `tipo=pericia`, chamar `get_vectorstore().add_documents(docs)`.
- **Exercício 4:** Adicionar uma nova regra em `response_validator.py` (ex.: “resposta não pode ter mais de 500 palavras”) e garantir que o botão “resposta incorreta” no Streamlit ainda salve o validation completo.
- **Exercício 5:** Consultar `analyze_feedback()` após marcar algumas respostas como incorretas e listar as queries com baixa satisfação; escolher uma e pensar em como melhorar (mais variantes na query expansion? mais peso BM25? novo trecho no reindexar?).

Se você conseguir cobrir o checklist e responder às perguntas típicas em 5–10 minutos de conversa, está bem preparado para usar este projeto como portfólio em vagas de ML/IA/RAG.

---

*Curso extenso baseado na implementação real do repositório (ingestion, embedding, vectorstore, retrieval, reranker, evaluation, reindexação e extração).*
