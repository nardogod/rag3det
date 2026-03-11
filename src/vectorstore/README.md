## `src/vectorstore` – armazenamento vetorial (ChromaDB)

Nesta pasta está o código que **salva e carrega o índice vetorial** usado na busca.

- **Se você quiser apagar e recriar o índice**: mexa aqui (ou use o script `scripts/build_index.py`).
- **Se você quiser trocar parâmetros do Chroma (nome da collection, etc.)**: altere `chroma_store.py`.

Arquivos principais (que vamos criar):
- `chroma_store.py` – cria/carrega o `Chroma` e oferece funções como:
  - `build_or_update_vectorstore(documents)` – indexa novos documentos.
  - `get_vectorstore()` – carrega o índice já persistido em `data/chroma`.

