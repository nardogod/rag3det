# Inventário: Personagem, Características e Construção 3D&T

## Arquitetura e comunicação entre sistemas

O inventário **personagem** é a base numérica e de construção: define F, H, R, A, PdF (0–5), PVs/PMs por R, regras de compra e pontuação. As regras de combate usam essas Características; a Ficha (em mestre) é o formulário; pericias, vantagens e magias são compradas com pontos.

| Sistema | Relação |
|---------|---------|
| **Regras de Combate** | FA = H+F ou H+PdF; FD = H+A; F, H, A, PdF vêm das Características |
| **Mestre** | Ficha schema, Vigilância supervisiona Construção |
| **Perícias** | Compradas com pontos; 11 listadas |
| **Vantagens** | Compradas com pontos; limites por Pontuação |
| **Magia** | Focus, Caminhos; comprados com pontos |

Ver também: [INVENTARIO_REGRAS_COMBATE.md](INVENTARIO_REGRAS_COMBATE.md), [INVENTARIO_MESTRE.md](INVENTARIO_MESTRE.md), [INVENTARIO_PERICIAS.md](INVENTARIO_PERICIAS.md), [INVENTARIO_VANTAGENS_DESVANTAGENS_KITS.md](INVENTARIO_VANTAGENS_DESVANTAGENS_KITS.md), [INVENTARIO_MAGIAS.md](INVENTARIO_MAGIAS.md)

## Avaliação e categorização

| Categoria | Conteúdo | Páginas |
|-----------|----------|---------|
| **caracteristicas_base** | Conceito, 0–5, 1 ponto = 1 carac | 9, 15 |
| **caracteristicas** | F, H, R, A, PdF (0–5, tabelas) | 15 |
| **construcao** | Conceito, Ficha, fluxo | 9 |
| **pontuacao** | Pessoa Comum, Novato 5, Lutador 7, Campeão 10, Lenda 12 | 9 |
| **pv_pm** | Não compra; dependem de R | 9 |
| **sugestoes_testes** | Levantar peso, Arrombar, Equilíbrio, etc. | 15 |
| **dinheiro** | 1dx100 base, modificadores por V/D | 9 |

## Blocos extraídos (índice)

| ID | Título | Categoria |
|----|--------|-----------|
| caracteristicas_base | Características — Base (0–5, 1 pt = 1 carac) | caracteristicas_base |
| forca | Força (F0–F5, capacidade, dano) | caracteristicas |
| habilidade | Habilidade (H0–H5, FA, FD, testes) | caracteristicas |
| resistencia | Resistência (R0–R5, PVs, PMs) | caracteristicas |
| armadura | Armadura (A0–A5, FD) | caracteristicas |
| poder_fogo | Poder de Fogo (PdF0–PdF5, ataques distância) | caracteristicas |
| construcao_personagem | Construção do Personagem (conceito, Ficha) | construcao |
| pontuacao | A Pontuação (Novato 5, Lutador 7, etc.) | pontuacao |
| pv_pm | Pontos de Vida e Pontos de Magia | pv_pm |
| recuperacao_pv_pm | Recuperação de PVs e PMs com Repouso | pv_pm |
| vantagens_desvantagens | Vantagens e Desvantagens (resumo) | construcao |
| pericias_resumo | Perícias (resumo, 11 listadas) | construcao |
| magia_resumo | Magia (Focus, Caminhos) | construcao |
| pertences | Pertences Pessoais | construcao |
| sugestoes_testes | Sugestões de Testes (tabela) | sugestoes_testes |
| dinheiro_inicial | Dinheiro Inicial (1dx100, modificadores) | dinheiro |

## Organização dos dados

| Arquivo | Descrição |
|---------|-----------|
| `data/processed/personagem/personagem_canonico.json` | Dados canônicos |
| `data/processed/personagem/personagem_consolidado.json` | Saída do extrator |

## Scripts

| Script | Função |
|--------|--------|
| `scripts/extrair_personagem.py` | Carrega canônico, gera consolidado |
| `scripts/reindexar_personagem.py` | Chroma para RAG |

## Pipeline

```bash
python scripts/extrair_personagem.py
python scripts/reindexar_personagem.py
```

## Livro fonte

| Livro | Capítulo | Páginas |
|-------|----------|---------|
| **Manual 3D&T Turbinado Digital** | Os Números, Construção do Personagem, A Pontuação | 9, 15 |
