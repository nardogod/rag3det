# Inventário: Monstros e Criaturas 3D&T

## Visão geral

| Livro | Conteúdo | Status |
|-------|----------|--------|
| **Manual dos Monstros** | Criaturas com F/H/R/A, PV, habilidades | Estrutura definida; extração pendente |
| **Bestiário Alpha** | Catálogo de monstros; itens em descrições | Estrutura definida; extração pendente |

---

## Estrutura de dados proposta

```json
{
  "nome": "Goblin",
  "tipo": "humanóide",
  "caracteristicas": {"F": 0, "H": 1, "R": 0, "A": 0, "PdF": 0},
  "pv": "1d+1",
  "pm": "0",
  "habilidades": ["Visão Noturna", "Arena (cavernas)"],
  "tesouro": "1d10 moedas",
  "livro": "Manual dos Monstros",
  "pagina": 42
}
```

### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| nome | string | Nome da criatura |
| tipo | string | humanóide, besta, elemental, morto-vivo, etc. |
| caracteristicas | object | F, H, R, A, PdF |
| pv | string | Fórmula ou valor (ex.: "1d+1", "12") |
| pm | string | Pontos de Magia |
| habilidades | list | Vantagens, desvantagens, poderes especiais |
| tesouro | string | Descrição do tesouro típico |
| vulnerabilidades | list | Tipos de dano que causam efeito extra |
| fraqueza | string | Fraqueza específica (quando houver), ex.: "fogo", "magia" |
| descricao | string | **Texto completo do livro** — lore, ataques, habilidades, regras especiais (Paralisia, Má Fama, fórmulas FA/FD). Define personalidade e dificuldade do combate. |
| livro | string | Fonte |
| pagina | int | Página |
| **Campos enriquecidos** (piloto: Livro de Arton) | | |
| comportamento | string | Comportamento geral da criatura |
| altura_tamanho | string | Dimensões físicas |
| peso | string | Peso aproximado |
| habitat | string | Onde vive |
| comportamento_dia_noite | string | Atividade diurna ou noturna |
| comportamento_combate | string | Táticas e estratégias de combate |
| habilidades_extra | string | Habilidades além das mecânicas (habilidades) |
| **Campos de combate e movimento** | | |
| movimento | string/object | Velocidade em km/h, m/turno, km/dia (terra, vôo, etc.) |
| ataques_especificos | array | Lista de ataques com FA/FD, dano, ataques por turno |
| imunidades | list | Imunidades (veneno, doença, mente, etc.) |
| fraquezas | list | Fraquezas específicas (magia cura causa dano, etc.) |
| veneno_detalhado | object | Teste, efeito em falha/sucesso, duração |
| **Campos de lore e uso** | | |
| origem_criacao | string | Origem mágica ou divina (ex.: criação de Tenebra) |
| uso_cultural | string | Rito de passagem, montaria de X, etc. |
| vinculo_montaria | object | Ligação Natural, montaria para quem; efeitos |
| resistencia_controle | string | Não afetado por Controle/Esconjuro de Mortos-Vivos |
| necessidades | string | Come, bebe, descansa? (Corcel: nenhuma) |
| recuperacao_pv | string | Como recupera PVs (descanso, magia cura mortos) |
| fonte_referencia | string | Fonte: "criatura ancestral" (Livro de Arton) | ✅ Todo o Livro de Arton |

---

## Resumo: prioridade de implementação (modelo completo)

Modelo unificado com o que já tínhamos + novos campos, ordenado por prioridade.

### Campos base (já existentes na extração)

| Campo | Tipo | Status |
|-------|------|--------|
| nome | string | ✅ Implementado |
| tipo | string | ✅ Implementado |
| caracteristicas | object | ✅ Implementado |
| pv, pm | string | ✅ Implementado |
| habilidades | list | ✅ Implementado |
| tesouro | string | ✅ Implementado |
| vulnerabilidades | list | ✅ Implementado |
| fraqueza | string | ✅ Implementado |
| descricao | string | ✅ Implementado |
| livro, pagina | string, int | ✅ Implementado |
| habilidades_combate | array | ✅ Implementado |

### Prioridade ALTA — combate e movimento

| Campo | Tipo | Motivo | Status |
|-------|------|--------|--------|
| **ataques_especificos** | array | Essencial para combate e automação | ✅ Piloto (5 monstros) |
| **movimento** | string/object | Perseguição e deslocamento | ✅ Piloto (Unicórnio, Dragão Latão) |
| **imunidades** | list | Complementa vulnerabilidades; muitos monstros usam | ✅ Piloto (Dragão, Devorador) |
| **fraquezas** | list | Fraquezas específicas além de `fraqueza` | ✅ Piloto (Unicórnio) |

### Prioridade MÉDIA — enriquecimento (já tínhamos)

| Campo | Tipo | Motivo | Status |
|-------|------|--------|--------|
| **comportamento** | string | Comportamento geral | ✅ Implementado |
| **altura_tamanho** | string | Dimensões físicas | ✅ Implementado |
| **peso** | string | Peso aproximado | ✅ Implementado |
| **habitat** | string | Onde vive | ✅ Implementado |
| **comportamento_dia_noite** | string | Atividade diurna/noturna | ✅ Implementado |
| **comportamento_combate** | string | Táticas e estratégias | ✅ Implementado |
| **habilidades_extra** | string | Habilidades além das mecânicas | ✅ Implementado |

### Prioridade MÉDIA — lore e veneno

| Campo | Tipo | Motivo | Status |
|-------|------|--------|--------|
| **veneno_detalhado** | object | Muitos monstros usam veneno | ✅ Piloto (Centopéia-Gigante) |
| **origem_criacao** | string | Lore e encontros | ✅ Piloto (5 monstros) |
| **uso_cultural** | string | Narrativa e encontros | ✅ Piloto (Unicórnio) |

### Prioridade BAIXA — específicos

| Campo | Tipo | Motivo | Status |
|-------|------|--------|--------|
| **vinculo_montaria** | object | Montarias (Corcel, Unicórnio) | ✅ Piloto (Unicórnio) |
| **resistencia_controle** | string | Mortos-vivos | ✅ Piloto (Corcel das Trevas) |
| **necessidades** | string | Cenários de viagem | ✅ Piloto (Corcel das Trevas) |
| **recuperacao_pv** | string | Mortos-vivos, regeneração | ✅ Piloto (Corcel das Trevas) |

### Arquivo de referência

- **Modelo completo piloto:** `data/processed/monstros/monstros_modelo_enriquecido.json` (5 monstros)
- **Extração:** `python scripts/extrair_monstros_modelo_enriquecido.py`

---

## Plano de implementação

1. **Extrator**: Criar `extrair_monstros_*.py` que leia Manual dos Monstros e Bestiário
2. **Schema**: `data/processed/monstros/schema_monstros.json`
3. **Dados**: `data/processed/monstros/monstros_extraidos.json`
4. **Reindexador**: `reindexar_monstros.py` para Chroma
5. **Integração**: Gerador de encontros e Mestre Autônomo usam o inventário

---

## Diretório

```
data/processed/monstros/
  schema_monstros.json
  monstros_extraidos.json  (quando extrator existir)
  monstros_canonico.json   (fallback parcial, opcional)
```
