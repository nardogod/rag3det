# Curso: RAG, Pipeline de Dados e Avaliação para Portfólio ML/IA

**Público:** Quem quer desenvolver (ou já desenvolveu) um projeto RAG e usar como portfólio para vagas de ML/IA/RAG, usando Cursor (ou outra IA) como copiloto.  
**Objetivo:** Ter os conhecimentos necessários para entender, explicar e evoluir um sistema como o deste repositório — e conseguir vagas nessas áreas.

---

## Índice

1. [Pré-requisitos: o que você precisa saber](#1-pré-requisitos-o-que-você-precisa-saber)
2. [Ingestão de PDFs](#2-ingestão-de-pdfs)
3. [Chunking](#3-chunking)
4. [Embeddings: locais e fine-tuned](#4-embeddings-locais-e-fine-tuned)
5. [Banco vetorial (ChromaDB)](#5-banco-vetorial-chromadb)
6. [Retrieval híbrido (vetorial + BM25)](#6-retrieval-híbrido-vetorial--bm25)
7. [Reranker (cross-encoder)](#7-reranker-cross-encoder)
8. [Reindexação por domínio e documentos estruturados](#8-reindexação-por-domínio-e-documentos-estruturados)
9. [Pipeline de extração e enriquecimento a partir de PDFs](#9-pipeline-de-extração-e-enriquecimento-a-partir-de-pdfs)
10. [Avaliação e feedback de respostas](#10-avaliação-e-feedback-de-respostas)
11. [Como estudar com Cursor/IA](#11-como-estudar-com-cursoria)
12. [Checklist para vagas ML/IA/RAG](#12-checklist-para-vagas-mlia-rag)

---

## 1. Pré-requisitos: o que você precisa saber

Para tocar e evoluir um projeto RAG como este (e falar com segurança em entrevistas), você não precisa ser expert em tudo, mas precisa de uma base clara.

| Tema | Nível mínimo | Por quê |
|------|----------------|--------|
| **Python** | Intermediário: funções, classes, tipos, `pathlib`, `dataclasses`, `typing` | Todo o backend é Python; configs e tipos estão em todo lugar. |
| **Ambiente** | `.env`, `pip`, `venv`, variáveis de ambiente | O projeto usa `SOURCE_PDF_DIR`, `CHROMA_DB_DIR`, `EMBEDDING_MODEL`, etc. |
| **Conceitos de ML/IA** | Noção de embedding (vetor que representa texto), similaridade (ex.: cosseno), “busca semântica” vs “busca por palavra” | Explicar RAG, retrieval e reranker em entrevista. |
| **RAG** | Saber o fluxo: pergunta → buscar trechos relevantes → montar contexto → LLM gera resposta | É o core do produto. |
| **Git** | Básico: clone, commit, branch, push | Repositório como portfólio. |

**Opcional mas útil:** noção de sentence transformers (modelos que transformam texto em vetor), LangChain (abstrações de documentos, embeddings, vector stores), e SQLite (para armazenar feedback).

**Dica:** Não tente estudar tudo antes. Use o curso por tema; quando encontrar um termo que não domina, pause e pesquise (ou peça ao Cursor: “explique embedding em uma frase” / “o que é BM25?”).

---

## 2. Ingestão de PDFs

**O que é:** Carregar PDFs do disco e transformá-los em uma lista de “documentos” (página a página ou por bloco) com metadados (livro, página, seção). É a entrada do pipeline RAG.

**No projeto:**
- **Onde:** `src/ingestion/pdf_loader.py` (carrega PDFs), `src/ingestion/pipeline.py` (orquestra: load → process → chunks).
- **Como:** Uso de `PyPDFLoader` ou `PyMuPDFLoader` (LangChain); falhas em PDFs malformados são ignoradas com log; metadados padronizados: `source`, `page`, `book_title`, `content_type`.
- **Config:** Diretório dos PDFs vem de `paths.source_pdf_dir` (env `SOURCE_PDF_DIR` ou `data/raw`).

**Conceitos para mercado:**
- Document loader: qualquer código que lê fonte (PDF, HTML, API) e produz “documentos” com `page_content` + `metadata`.
- Metadados ricos (livro, página, seção) ajudam no retrieval e na citação (“conforme Manual, p. 42”).

**O que você deve conseguir:**
- Explicar: “Os PDFs são carregados por loader, cada página vira um Document com metadados; depois passam por limpeza e chunking.”
- Saber onde alterar o diretório de PDFs e onde adicionar um novo loader (ex.: outro tipo de arquivo).

---

## 3. Chunking

**O que é:** Quebrar textos longos em pedaços (chunks) de tamanho controlado, com sobreposição (overlap) para não cortar frases no meio. Chunks são a unidade que será embedada e guardada no banco vetorial.

**No projeto:**
- **Onde:** `src/ingestion/chunking.py`, `src/ingestion/document_processor.py` (chama chunking após limpeza).
- **Como:** `RecursiveCharacterTextSplitter` (LangChain) com `chunk_size` e `chunk_overlap` vindos de config (`chunking_config`); separadores `["\n\n", "\n", ". ", " ", ""]`. Pré-processamento para não cortar tabelas no meio (linhas com `|` ou `;` agrupadas).
- **Config:** `CHUNK_SIZE` e `CHUNK_OVERLAP` (ex.: 1000 e 200) em `.env` ou `config/settings.yaml`.

**Conceitos para mercado:**
- Chunk size: trade-off entre contexto (chunks grandes) e precisão (chunks menores).
- Overlap: reduz perda de informação nas fronteiras; aumenta redundância e custo de embedding.
- Chunking “consciente” de estrutura (tabelas, seções) evita quebras ruins.

**O que você deve conseguir:**
- Dizer: “Usamos RecursiveCharacterTextSplitter com tamanho e overlap configuráveis; tabelas são pré-processadas para não serem cortadas.”
- Ajustar `chunk_size`/`chunk_overlap` e entender o efeito no recall e no custo.

---

## 4. Embeddings: locais e fine-tuned

**O que é:** Transformar texto em vetor numérico (embedding). Busca “semântica” é busca por similaridade entre vetores (ex.: cosseno). Modelo “local” roda na sua máquina; “fine-tuned” é treinado no seu domínio (ex.: 3D&T) para melhorar relevância.

**No projeto:**
- **Onde:** `src/embedding/local_embeddings.py` (carrega modelo fine-tuned ou fallback), `src/embedding/pipeline.py` (ponto de acesso com cache em disco), `src/embedding/cached_embeddings.py` (evita recomputar). Fine-tuning: `src/ml/training/finetune_embeddings.py`, geração de dataset: `generate_embedding_dataset*.py`.
- **Como:** Prioridade: modelo em caminho local (ex.: `models/embeddings/3dt_finetuned/`); se não existir, usa modelo HuggingFace (ex.: `paraphrase-multilingual-mpnet-base-v2`). Normalização L2 nos vetores. Cache de embeddings em disco por `model_id`.
- **Config:** `EMBEDDING_MODEL`, `EMBEDDING_FALLBACK`, `EMBEDDING_MODEL_NAME` em `.env`/config.

**Conceitos para mercado:**
- Embedding: representação densa do texto; modelos “bi-encoder” (query e documento embedados separadamente).
- Fine-tuning: treino com pares/triplas (anchor, positive, negative) e loss de ranking (ex.: MultipleNegativesRankingLoss) para o domínio.
- Normalização L2: vetores com norma 1; similaridade cosseno = produto interno.

**O que você deve conseguir:**
- Explicar: “Usamos modelo de embeddings local ou fine-tuned para o domínio; há cache em disco e fallback para modelo genérico.”
- Saber onde trocar modelo e onde está o script de fine-tuning (e que tipo de dataset ele espera).

---

## 5. Banco vetorial (ChromaDB)

**O que é:** Banco que guarda vetores e permite busca por similaridade (k-NN). Você adiciona documentos já embedados; na query, embeda a pergunta e busca os k mais próximos.

**No projeto:**
- **Onde:** `src/vectorstore/chroma_store.py`.
- **Como:** Chroma persistente em diretório (`paths.chroma_dir`). Duas collections: `3det_rag` (embedding fine-tuned) e `3det_rag_baseline` (genérico) para A/B. `build_or_update_vectorstore(documents)` recria o índice; `get_vectorstore()` carrega o existente. Ao trocar dimensão do embedding (ex.: 768 vs 384), a collection é deletada e recriada.
- **Config:** `CHROMA_DB_DIR` (default: `data/chroma`).

**Conceitos para mercado:**
- Vector store: armazenamento + busca por similaridade; Chroma, Pinecone, Weaviate, etc.
- Collection: namespace de vetores; cada uma com uma dimensão fixa (definida pelo modelo de embedding).

**O que você deve conseguir:**
- Dizer: “O Chroma guarda os chunks embedados; temos uma collection principal e uma baseline para comparação; o build substitui a collection quando necessário.”
- Saber onde fica o diretório do Chroma e o que fazer ao trocar de modelo de embedding.

---

## 6. Retrieval híbrido (vetorial + BM25)

**O que é:** Combinar busca semântica (vetorial) com busca léxica (por termos). BM25 é um modelo clássico de ranking por palavras; ajuda em nomes próprios, siglas e termos exatos que o embedding pode “suavizar” demais.

**No projeto:**
- **Onde:** `src/retrieval/pipeline.py` (orquestra semântico + BM25, fusão de scores, opcionalmente query expansion e reranker).
- **Como:** Para cada variante de query (se query expansion ativo): (1) busca vetorial no Chroma com `candidate_k`; (2) BM25 sobre todos os documentos do Chroma (corpus tokenizado, `rank_bm25.BM25Okapi`). Scores semânticos normalizados (distância → similaridade); BM25 normalizado (min-max). Fusão: `w_sem * norm_sem + w_bm25 * norm_bm25`. Lista fusionada é depois cortada e passada ao reranker (se ativo).
- **Config:** `RETRIEVAL_K`, `CANDIDATE_K`, `HYBRID_ENABLED`, `QUERY_EXPANSION_ENABLED`, `RERANKING_ENABLED`, pesos semântico/BM25 em config.

**Conceitos para mercado:**
- Hybrid search: combinar vetorial + léxico (BM25, TF-IDF) para melhor recall e robustez.
- Query expansion: gerar variantes da pergunta (ex.: sinônimos, termos do domínio) para buscar mais; resultados são agregados e deduplicados.
- Reciprocal Rank Fusion (ou fusão por score normalizado) é comum para juntar rankings.

**O que você deve conseguir:**
- Explicar: “Fazemos busca vetorial e BM25, normalizamos os scores, combinamos com pesos e opcionalmente expandimos a query; o resultado vai para o reranker.”
- Saber onde ativar/desativar híbrido e expansion e onde ajustar os pesos.

---

## 7. Reranker (cross-encoder)

**O que é:** Um modelo que recebe (pergunta, trecho) e devolve um score de relevância. Usado depois da busca inicial para reordenar os top-N candidatos e melhorar precisão.

**No projeto:**
- **Onde:** `src/retrieval/reranker.py`.
- **Como:** Cross-encoder (ex.: `cross-encoder/ms-marco-MiniLM-L-6-v2`) via `sentence_transformers.CrossEncoder`. Recebe lista de pares (query, doc); retorna scores; ordena e devolve top_k. Suporte a modelo fine-tuned em `models/reranker/3dt_finetuned`. Extração de “frase-chave” da pergunta (ex.: “O que é X?” → “X”) para melhorar o par.
- **Config:** Habilitado por `RERANKING_ENABLED`; modelo padrão e path do fine-tuned no código/config.

**Conceitos para mercado:**
- Cross-encoder: um único modelo que vê query e documento juntos; mais preciso que bi-encoder, mas só pode ser aplicado a um conjunto pequeno de candidatos (por custo).
- Pipeline típico: retriever (vetorial + BM25) traz muitos candidatos; reranker refina os top 20–50.

**O que você deve conseguir:**
- Dizer: “Depois da busca híbrida, um cross-encoder reranka os candidatos; usamos modelo leve local e opcionalmente um modelo fine-tuned para o domínio.”
- Saber onde o reranker é chamado no pipeline e como ligar/desligar.

---

## 8. Reindexação por domínio e documentos estruturados

**O que é:** Além do índice “geral” (PDFs → chunks), criar documentos estruturados por domínio (monstros, magias, itens, etc.), formatados em texto padronizado (ex.: ficha em tabela), e adicioná-los ao mesmo Chroma (ou a uma collection dedicada). Isso melhora respostas para perguntas sobre entidades específicas.

**No projeto:**
- **Onde:** Scripts `scripts/reindexar_monstros.py`, `reindexar_magias.py`, `reindexar_itens_magicos.py`, `reindexar_vantagens.py`, etc. Formato de ficha: `src/utils/formatar_monstro.py` (`formatar_ficha_monstro_tabela`); regra de formato em `.cursor/rules/formato-ficha-monstro.mdc`.
- **Como:** Carregar JSON de domínio (ex.: `data/processed/monstros/monstros_modelo_enriquecido.json`); para cada item, gerar texto completo (ficha tabelada, descrição); criar um ou mais `Document` com metadados (`tipo`, `nome`, `livro`, `tipo_chunk`); usar `get_vectorstore().add_documents(docs)`. Não substitui o índice geral; adiciona documentos.
- **Padrão:** 1) Fonte de dados (JSON/TSV); 2) Função de formatação (entidade → texto); 3) Metadados consistentes; 4) Script que chama `add_documents`.

**Conceitos para mercado:**
- Documentos estruturados: entidades (monstro, magia, item) viram texto padronizado (tabela, campos fixos), ótimo para RAG e para citação.
- Reindexação por domínio: pipelines separados por tipo de entidade; permitem atualizar só um domínio sem reprocessar tudo.

**O que você deve conseguir:**
- Explicar: “Além do índice dos PDFs, temos scripts que carregam JSON de monstros/magias/itens, formatam em ficha e adicionam ao Chroma com metadados de tipo; assim o RAG encontra entidades específicas.”
- Ser capaz de criar um novo `reindexar_*.py` para outro domínio (ex.: perícias) seguindo o mesmo padrão.

---

## 9. Pipeline de extração e enriquecimento a partir de PDFs

**O que é:** Extrair entidades estruturadas (ex.: monstros com nome, atributos, habilidades) a partir dos PDFs, enriquecer com descrições ou campos adicionais, e salvar em JSON. Esse JSON alimenta a reindexação por domínio e pode alimentar outras aplicações (ex.: frontend do jogo).

**No projeto:**
- **Onde:** Ingestão/extração: `src/ingestion/` (extratores de monstros, magias, tabelas); scripts: `scripts/extrair_monstros_modelo_enriquecido.py`, `enriquecer_todos_monstros.py`, `varredura_completa_monstros.py`; dados: `data/processed/monstros/` (monstros_extraidos.json, monstros_canonico.json, monstros_modelo_enriquecido.json); formatação: `src/utils/formatar_monstro.py`, `normalizar_ocr.py`.
- **Como:** Extração pode ser por regras (regex, padrões de tabela), por modelo (LLM) ou híbrido. Enriquecimento: preencher campos faltantes (ex.: descrição) a partir de outro processamento ou manual (complemento/PILOTO_EXTRA). Pipeline: PDF/páginas → extrator → JSON bruto → enriquecimento → JSON canônico/enriquecido → usado por reindexar_* e pelo frontend (ex.: copy-monstros).
- **Conceitos:** ETL para domínio de jogo/RPG; qualidade de dados (normalização de livro, siglas, OCR); “fonte única” (um JSON) para RAG e UI.

**Conceitos para mercado:**
- Pipeline de dados: extrair → limpar → normalizar → enriquecer → publicar (para RAG, API, app).
- Enriquecimento: adicionar campos ou texto (descrição, resumo) para melhorar retrieval e exibição.

**O que você deve conseguir:**
- Explicar: “Temos um pipeline que extrai monstros (e outros) dos PDFs, enriquece com descrições e normaliza; o resultado vira JSON que alimenta o reindexador e o frontend.”
- Saber a diferença entre “extraídos”, “canônico” e “enriquecido” no projeto e onde está cada etapa.

---

## 10. Avaliação e feedback de respostas

**O que é:** Ter como medir se a resposta do RAG está boa (validação automática por regras) e guardar feedback do usuário (certo/errado) para análise e melhoria do sistema.

**No projeto:**
- **Onde:** `src/evaluation/response_validator.py` (regras sobre a resposta), `src/evaluation/feedback_loop.py` (persistência em SQLite).
- **Como:** Validação: verificar se há citação entre aspas, se a “fonte primária” bate com os chunks usados, se números mencionados aparecem em citações, e se não há linguagem vaga (“eu acho que”, “provavelmente”). Feedback: usuário marca “resposta incorreta”; o sistema valida e salva em `data/feedback.db` (query, resposta, rating, chunks, scores, flags de validação). Função `analyze_feedback()` para listar queries com baixa satisfação.
- **Uso:** Na UI (ex.: Streamlit), botão “Esta resposta está incorreta” chama `validate_response` e `save_feedback`.

**Conceitos para mercado:**
- Avaliação de RAG: métricas de retrieval (recall, MRR), de geração (faithfulness, relevância) e regras de negócio (citação obrigatória, fonte válida).
- Feedback loop: armazenar avaliação do usuário para treinar reranker/embeddings ou para priorizar correções.

**O que você deve conseguir:**
- Explicar: “Validamos a resposta com regras (citação, fonte, números ancorados, sem hedge) e persistimos feedback negativo em SQLite para análise.”
- Saber onde estão as regras de validação e onde o feedback é salvo e como analisar (ex.: queries com mais thumbs down).

---

## 11. Como estudar com Cursor/IA

- **Por tema:** Abra o `CURSO_RAG_ML_PORTFOLIO.md` e, para cada seção, abra os arquivos indicados no “Onde”. Peça ao Cursor: “Explique o fluxo deste arquivo em 3 frases” ou “Onde o chunk_size é usado?”.
- **Rastrear um fluxo:** Comece por “usuário pergunta no chat” → `qa_chain.answer_question` → `retrieve_relevant_chunks` → pipeline (vetorial, BM25, rerank) → `format_context` → LLM. Peça: “Mostre a chamada de retrieve em qa_chain”.
- **Criar um reindexar:** Copie `reindexar_monstros.py`, troque o JSON de entrada e a função de formatação; peça ao Cursor para adaptar metadados e nome do script.
- **Entrevista:** Treine falar em voz alta: “Meu RAG faz ingestão de PDFs, chunking com overlap, embeddings locais ou fine-tuned, Chroma, retrieval híbrido com BM25 e reranker; tenho reindexação por domínio e feedback em SQLite.”

---

## 12. Checklist para vagas ML/IA/RAG

Use este checklist para saber se você consegue falar sobre o projeto com segurança:

- [ ] **Ingestão:** Explicar de onde vêm os PDFs e como viram documentos com metadados.
- [ ] **Chunking:** Dizer tamanho/overlap e por que existe pré-processamento de tabelas.
- [ ] **Embeddings:** Diferenciar modelo local, fine-tuned e fallback; mencionar cache.
- [ ] **Chroma:** Explicar collections (principal vs baseline) e quando o índice é recriado.
- [ ] **Retrieval:** Descrever busca vetorial + BM25, fusão de scores e query expansion.
- [ ] **Reranker:** Dizer o que é cross-encoder e em que momento entra no pipeline.
- [ ] **Reindexação por domínio:** Dar exemplo (monstros) e dizer formato de documento e metadados.
- [ ] **Pipeline de dados:** Descrever extração → enriquecimento → JSON → reindexar e frontend.
- [ ] **Avaliação/feedback:** Citar regras de validação e onde o feedback é armazenado e analisado.

Se você conseguir cobrir todos os itens em uma conversa de 5–10 minutos, está bem preparado para usar este projeto como portfólio em vagas de ML/IA/RAG.

---

*Curso baseado na implementação real do repositório (ingestion, embedding, vectorstore, retrieval, evaluation, scripts de reindexação e extração).*
