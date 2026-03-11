# Inventário de Itens Mágicos 3D&T

## Fontes (livros)

Os itens são extraídos de **todos os PDFs** disponíveis. Cada item mantém o campo `livro` com a origem:

| Livro | Estrutura típica |
|-------|------------------|
| **Manual da Magia** | Cap. Objetos Mágicos, Preço: T$ (Tibares) |
| **Alpha Manual da Magia** | Mesmo formato do Manual |
| **Alpha Manual dos Monstros** | Tesouros, Equipamento em descrições |
| **Outros** | PEs, Preço, Poção, Anel, etc. |

O mesmo item pode aparecer em vários livros (ex.: Poção do Amor no Manual e no Alpha); cada entrada tem `livro` explícito.

## Categorização (Manual da Magia)

O Manual da Magia (3dt-manual-da-magia-biblioteca-elfica.pdf) organiza itens a partir da **pg. 72** nas seguintes categorias:

### Estrutura de categorias

| Categoria | Tipo | Descrição |
|-----------|------|-----------|
| **Arma Especial** | conceito | Item mágico único com FA+1 e Habilidades Especiais |
| **Habilidade de Arma Especial** | poder | Afiada, Dançarina, Defensora, Profana, etc. |
| **Arma Elemental** | tipo | Água 1, Fogo 2, Terra 4 – magia Aumento de Dano |
| **Arma Nomeada** | item | Espada de Roubar Vidas, Adaga de Prata, etc. |
| **Armadura** | item | Armadura Celestial, Cota de Malha Élfica, etc. |
| **Habilidade de Armadura** | poder | Camuflagem, Fortificação, Resistência à Magia, etc. |
| **Escudo** | item | Escudo da Aniquilação, Escudo Bumerangue, etc. |
| **Material Especial** | material | Aço-Rubi, Adamante, Ferro de Ith, Mitral, etc. |
| **Cajado** | item | Cajado de Alterar o Tamanho, Cajado de Fogo, etc. |
| **Bastão** | item | Bastão da Absorção, Bastão das Maravilhas, etc. |
| **Anel** | item | Anel Arcano, Anel de Proteção, etc. |
| **Poção** | item | Poção do Amor, Poção da Genialidade, etc. |
| **Óleo** | item | Óleo Escorregadio |
| **Pomada** | item | Pomada de Pedra |
| **Ingrediente/Veneno** | item | Arsênico, Bruma de Insanidade, Poeira de Lich, etc. |
| **Bônus Genérico** | item | Força +1, Armadura +2, Resistência +3, etc. |
| **Item Diverso** | item | Botas, Amuletos, Mantos, Luvas, etc. |

### Scripts

```bash
# Extrair itens dos PDFs
python scripts/extrair_itens_magicos_agressivo.py

# Categorizar conforme taxonomia
python scripts/categorizar_itens_magicos.py

# Reindexar no Chroma para busca RAG
python scripts/reindexar_itens_magicos.py
```

### Arquivos gerados

| Arquivo | Descrição |
|---------|-----------|
| `data/processed/itens_magicos/itens_magicos_extraidos_agressivo.json` | Itens extraídos (nome, custo, efeito, **livro**) |
| `data/processed/itens_magicos/itens_magicos_categorizados.json` | Itens com campo `categoria` |
| `data/processed/itens_magicos/itens_por_categoria.txt` | Relatório por categoria |
| `data/processed/itens_magicos/taxonomia_manual_magia.json` | Taxonomia de categorias |

### Lógica por livro

- **Extração**: o script busca cada item do índice em **todos** os PDFs; quando encontra, grava com `livro` = nome do PDF.
- **Índice**: `extrair_indice_itens_magicos.py` varre todos os PDFs e detecta itens por padrões (Objetos Mágicos, Tesouro, PEs, Preço, etc.).
- **RAG**: o texto indexado inclui `Fonte: {livro}` para deixar a origem explícita nas respostas.
- **Qualidade OCR**: blocos com artefatos de OCR (ex.: `3dt-manual-revisado-ampliado-e-turbinado`) são rejeitados; o item pode ser encontrado em outro PDF.

### Amostra

```bash
python scripts/amostra_20_itens.py   # Gera amostra_20_itens.txt
```
