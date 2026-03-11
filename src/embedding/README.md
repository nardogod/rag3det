## `src/embedding` – modelos de embeddings

Aqui você controla **como o texto vira vetor numérico** (para busca semântica).

- **Se você quer trocar o modelo de embeddings (por outro multilíngue ou mais leve)**:
  - ajuste a variável `EMBEDDING_MODEL_NAME` no `.env` **ou**
  - altere a implementação em `embeddings.py`.
- **Se você quer centralizar a criação de embeddings para usar em outros módulos**:
  - use a função auxiliar em `pipeline.py` (por exemplo, `get_embedding_function()`).

Arquivos principais (que vamos criar):
- `embeddings.py` – wrapper em torno do `HuggingFaceEmbeddings`.
- `pipeline.py` – ponto de acesso simples para obter a função de embedding.

