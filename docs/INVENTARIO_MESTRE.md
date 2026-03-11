# Inventário: O Mestre — Centro do Jogo 3D&T

## Princípio central

O **Mestre** é o grande centro de tudo no 3D&T. Toda a lógica do jogo passa por ele: regras, aventuras, desafios, arbitragem, criação de personagens. Nenhuma decisão existe sem o Mestre permitir. Este inventário consolida todas as regras e orientações sobre o Mestre em um ponto único.

## Avaliação das informações

A extração deve preservar:

1. **Papel e poder** (palavra final, pode contrariar regras, inventar regras)
2. **Deveres** (conhecer regras, ensinar o jogo, inventar aventuras)
3. **Segredo** (rolagens em segredo, quando e por quê)
4. **Em Nome da Diversão** (não joga contra, justo como juiz)
5. **Definir mundo** (gênero, cenário, preferências do grupo)
6. **Vigilância** (acompanhar criação de personagens)
7. **Restrições** (Vantagens e Desvantagens por cenário)
8. **Aventuras e Campanhas** (partidas, Pontos de Experiência)
9. **Ficha de Personagem** (estrutura canônica dos campos)

## Categorização proposta

| Categoria | Conteúdo |
|-----------|----------|
| **papel_mestre** | O que é o Mestre, poder supremo |
| **deveres** | Conhecer regras, ensinar, inventar aventuras |
| **segredo** | Rolagens em segredo, mistério |
| **em_nome_da_diversao** | Justiça, não jogar contra, bom senso |
| **definir_mundo** | Cenário, gênero, preferências |
| **vigilancia** | Supervisão da criação de personagens |
| **restricoes** | Critérios para Vantagens e Desvantagens |
| **aventuras_campanhas** | Aventuras, campanhas, PEs |
| **ficha_personagem** | Schema da Ficha de Personagem |
| **sobre_jogo** | Sobre o 3D&T, O que é RPG, Como se Joga |

Ver também: [INVENTARIO_PERSONAGEM.md](INVENTARIO_PERSONAGEM.md) (Construção, Vigilância)

## Organização dos dados

| Arquivo | Descrição |
|---------|-----------|
| `data/processed/mestre/mestre_canonico.json` | Regras do Mestre + schema da Ficha |
| `data/processed/mestre/mestre_consolidado.json` | Saída do extrator |

## Scripts

| Script | Função |
|--------|--------|
| `scripts/extrair_mestre.py` | Carrega canônico, gera consolidado |
| `scripts/reindexar_mestre.py` | Chroma para RAG |

## Blocos extraídos (índice)

| ID | Título | Categoria |
|----|--------|-----------|
| papel_mestre | O Mestre — Papel e Poder | papel_mestre |
| deveres_mestre | Deveres do Mestre | deveres |
| segredo | Rolagens em Segredo | segredo |
| em_nome_da_diversao | Em Nome da Diversão | em_nome_da_diversao |
| definir_mundo | Definir o Mundo da Aventura | definir_mundo |
| vigilancia | Vigilância na Criação de Personagens | vigilancia |
| restricoes | Restrições — Vantagens e Desvantagens | restricoes |
| aventuras_campanhas | Aventuras e Campanhas | aventuras_campanhas |
| ficha_personagem | Ficha de Personagem | ficha_personagem |

## Pipeline

```bash
python scripts/extrair_mestre.py
python scripts/reindexar_mestre.py
```

## Livro fonte

| Livro | Capítulo | Páginas |
|-------|----------|---------|
| **Manual 3D&T Turbinado Digital** | Que Jogo é Este?, O que é RPG, Como se Joga | 5–6 |
| **Manual 3D&T Turbinado Digital** | O Mestre, Aventuras e Campanhas | ~113+ |
| **3D&T Defensores de Tóquio 3ª Edição** | Ficha de Personagem | 144 |
