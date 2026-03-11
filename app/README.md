## `app` – interface Streamlit (chat)

Aqui fica a **interface web de chat** que você vai usar para conversar com o assistente 3D&T.

- **Se você quer mudar o layout da tela, textos, cores, etc.**: edite `main.py`.
- **Se você quer adicionar mais controles (filtros por livro, sliders de parâmetros)**: também é em `main.py`.

Arquivo principal:
- `main.py` – app Streamlit que permite digitar perguntas, chama a pipeline RAG e mostra respostas + fontes.

**Como rodar** (a partir da raiz do projeto):
```bash
streamlit run app/main.py
```

