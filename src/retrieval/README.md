## `src/retrieval` – busca semântica + reranking

Aqui mora a lógica de **como encontrar os melhores trechos** nos livros.

- **Ponto único**: use `pipeline.py` → `retrieve_relevant_chunks(query)`.
- **Reranking (cross-encoder)**: `reranker.py` + `RERANKING_ENABLED` no `.env`.
- **Expansão de query (3D&T)**: `query_expansion.py` + `QUERY_EXPANSION_ENABLED`.

Arquivos principais:
- `retriever.py` – retriever Chroma (busca por vetores).
- `reranker.py` – **re-ranking com Cross-Encoder** (avalia relevância real query↔chunk).
- `query_expansion.py` – gera variações da pergunta com termos do domínio 3D&T.
- `pipeline.py` – orquestra: expansão → busca (semântica + opcional BM25) → rerank → top-k.

---

### TÉCNICA 1: Re-ranking com Cross-Encoder (Prioridade Máxima)

**Problema:** O retrieval semântico devolve textos "parecidos" (ex.: asas) mas não os "certos". Ex.: "Fênix" → Solar (asas), Pégaso (asas), em vez da magia de fogo.

**Solução:** Um **cross-encoder** (ex.: `ms-marco-MiniLM-L-6-v2`) julga a relevância real entre (query, documento), não só similaridade de vetor.

- **Antes:** "Fênix" → Solar (asas) = 0,85 similaridade ❌  
- **Depois:** Cross-encoder → chunk "Magia de fogo / Fênix" = 0,92 relevância ✅  

**Fluxo no pipeline:** buscar `candidate_k` (ex.: 20) candidatos → rerank com cross-encoder → devolver top `k` (ex.: 5). Config: `RETRIEVAL_CANDIDATE_K`, `RETRIEVAL_K`, `RERANKING_ENABLED`.

---

### TÉCNICA 2: Query Expansion com termos 3D&T

**Problema:** O usuário busca "Invocação da Fênix", mas o livro usa "Ave Fênix", "Magias Elementais de Fogo" ou está em seção "Conjuração".

**Solução:** Gerar 2–3 variações da query com termos do domínio (sinônimos 3D&T em `query_expansion.py`).

- **Exemplo:** "Invocação da Fênix" → também buscar "Fênix magia elemental fogo", "ave Fênix conjuração renascimento chamas".
- **Outros:** "Mortos-vivos" → "mortos-vivos necromancia criaturas mortas"; "Insano Megalomaníaco" → "Insano Megalomaníaco criatura bestiário".

Config: `QUERY_EXPANSION_ENABLED=true`. Novos termos podem ser adicionados em `DOMAIN_3DET` em `query_expansion.py`.

---

### Por que aumentar o `candidate_k` ajuda?

- **candidate_k pequeno:** poucos candidatos entram no rerank; o chunk certo pode ficar de fora.
- **candidate_k maior (ex.: 20):** mais recall na primeira etapa; o cross-encoder escolhe os **realmente** relevantes no top-k final.

Use `RETRIEVAL_CANDIDATE_K=20` (ou mais) e `RETRIEVAL_K=5` ou `6` no `.env` para o fluxo "retrieve 20 → rerank → top 5".
