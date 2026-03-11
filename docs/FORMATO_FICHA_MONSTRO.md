# Formato padrão de ficha de monstro

Ao exibir dados de monstros do modelo enriquecido, usar **sempre** esta tabela, com **todos** os campos, mesmo vazios ou não aplicáveis. Campos sem dado: `—`.

## Ordem dos campos

| Campo | Mapeamento JSON | Exemplo vazio |
|-------|-----------------|---------------|
| **Nome** | `nome` | — |
| **Características** | `caracteristicas` (F, H, R, A, PdF) | F3, H2, R4, A1, PdF2 |
| **PV / PM** | `pv`, `pm` | variável / 0 |
| **Comportamento** | `comportamento` | — |
| **Tamanho** | `altura_tamanho` | — |
| **Peso** | `peso` | — |
| **Habitat** | `habitat` | — |
| **Comportamento dia/noite** | `comportamento_dia_noite` | — |
| **Combate** | `comportamento_combate` | — |
| **Ataques** | `ataques_especificos` | — |
| **Imunidades** | `imunidades` | — |
| **Fraquezas** | `fraquezas` | — |
| **Habilidades** | `habilidades` + `habilidades_extra` | — |
| **Movimento** | `movimento` | — |
| **Origem criação** | `origem_criacao` | — |
| **Uso cultural** | `uso_cultural` | — |
| **Vínculo montaria** | `vinculo_montaria` | — |
| **Veneno** | `veneno_detalhado` | — |
| **Resistência controle** | `resistencia_controle` | — |
| **Necessidades** | `necessidades` | — |
| **Recuperação** | `recuperacao_pv` | — |
| **Fonte** | `fonte_referencia` | criatura ancestral |

## Exemplo (Demônios da Lama)

| Campo | Valor |
|-------|-------|
| **Nome** | Demônios da Lama |
| **Características** | F3, H2, R4, A1, PdF2 |
| **PV / PM** | variável / 0 |
| **Comportamento** | Surgem em pântanos/lamaçais onde criatura mágica (ex.: dragão) morreu. Ficam imersos na lama, difíceis de detectar ou ferir. |
| **Tamanho** | Humanóide grande (2,5–3 m) |
| **Peso** | — |
| **Habitat** | Pântanos e lamaçais |
| **Comportamento dia/noite** | — |
| **Combate** | Lentos: 1 ataque/turno; nunca vencem iniciativa nem se esquivam. Bolas de lama (contusão ou Paralisia). Ataque com Força: vítima faz Teste de Força ou fica presa; 2 falhas seguidas = sugada e sufoca |
| **Ataques** | Corpo a corpo (Força); Bolas de lama (contusão + Paralisia) |
| **Imunidades** | Armas cortantes e perfurantes (mágicas ou não) |
| **Fraquezas** | — |
| **Habilidades** | Paralisia; Invulnerabilidade (cortante, perfurante); Amalgamação (+F+1, R+1, PdF+1 por demônio extra); reforma em 1d horas |
| **Movimento** | — |
| **Origem criação** | — |
| **Uso cultural** | — |
| **Vínculo montaria** | — |
| **Veneno** | — |
| **Resistência controle** | — |
| **Necessidades** | — |
| **Recuperação** | Dissolvem na lama e podem se reformar em 1d horas; não são destruídos de forma definitiva |
| **Fonte** | criatura ancestral (Livro de Arton) |

## Uso no sistema

- **`formatar_ficha_monstro_tabela()`** em `src/utils/formatar_monstro.py` — gera a tabela completa.
- **`scripts/sample_monstros.py`** — exibe 6 monstros aleatórios neste formato.
- **`scripts/reindexar_monstros.py`** — indexa monstros no Chroma usando este formato (RAG).

## Regras

1. **Sempre** mostrar todos os campos na ordem acima.
2. Campo vazio ou `null`: usar `—`.
3. Listas vazias `[]`: usar `—`.
4. `ataques_especificos`: resumir em texto (ex.: "Corpo a corpo (Força); Bolas de lama (contusão + Paralisia)").
5. `habilidades`: juntar `habilidades` e `habilidades_extra` em um único texto.
