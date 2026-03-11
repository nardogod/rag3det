## `src/ingestion` – ingestão dos livros 3D&T

Tudo que controla **como os PDFs viram texto e chunks** mora aqui.

- **Se você quer mudar de onde vêm os PDFs**: olhe `src/config.py` (variável `paths.source_pdf_dir`).
- **Se você quer ajustar limpeza de texto (tirar cabeçalho/rodapé, espaços, etc.)**: mexa em `text_cleaning.py`.
- **Se você quer mudar o tamanho dos chunks ou a forma de quebrar por seções/tabelas**: mexa em `chunking.py`.
- **Se você quer rodar a ingestão completa (carregar + limpar + chunkar)**: veja `pipeline.py` (`run_ingestion()`).

Arquivos principais:
- `pdf_loader.py` – carrega PDFs e gera `Document`s com metadados. Se pypdf falhar, tenta PyMuPDF (fallback opcional).
- `text_cleaning.py` – limpa o texto bruto dos PDFs.
- `chunking.py` – divide o texto em chunks “inteligentes”.
- `pipeline.py` – orquestra tudo em uma função só.

**Um PDF deu erro (ex.: "Unexpected end of stream")?** Veja [PDF_TROUBLESHOOTING.md](PDF_TROUBLESHOOTING.md) para entender o motivo e como corrigir.
