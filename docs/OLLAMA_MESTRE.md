# Usar Ollama como LLM no Mestre Autonomo

Para a **narracao do mestre** ser gerada pelo Ollama (em vez de so regras fixas):

## 1. Instalar e subir o Ollama

- Instale: [ollama.com](https://ollama.com)
- No terminal, rode:
  ```bash
  ollama serve
  ```
- Baixe um modelo (ex. em portugues ou bilíngue):
  ```bash
  ollama pull llama3.1
  ```
  Ou outro: `ollama pull gemma3:4b`, `ollama pull mistral`, etc.

## 2. Configurar o projeto

No `.env` na raiz do projeto:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
```

(O `OLLAMA_BASE_URL` so precisa mudar se o Ollama estiver em outra maquina/porta.)

O nome em `OLLAMA_MODEL` deve ser exatamente o que aparece em `ollama list`.

## 3. No app (Streamlit)

1. Abra a **sidebar** e em **"Narracao do Mestre"** escolha **"LLM (Ollama: llama3.1)"** (ou o modelo que configurou).
2. Clique em **"Testar conexao Ollama"** para ver se o Ollama esta acessivel.
3. Crie a campanha ou continue jogando. Cada resposta do mestre sera reescrita pelo modelo (narracao + opcoes).

Se o Ollama nao estiver rodando ou o modelo nao existir, o app volta a usar a narracao do **Sistema** (regras e cenas preparadas) naquela acao.

## 4. Regras 3D&T usadas pelo Mestre

O mestre usa o modulo `regras_3dt.py`. As regras do manual sao o guia mestre.

- **Classe de Dificuldade**: Facil=3, Normal=4, Dificil=5, Muito Dificil=6
- **Atributos**: Forca, Habilidade, Resistencia, Armadura (nomes completos para o usuario)
- **Testes**: 1d6 + modificador vs Classe de Dificuldade
- **Termos legiveis**: Pontos de Vida, Pontos de Magia, Fator de Ataque, Fator de Defesa

A saida ao usuario usa sempre terminologia legivel; a logica interna mantem as siglas (F/H/R/A).
