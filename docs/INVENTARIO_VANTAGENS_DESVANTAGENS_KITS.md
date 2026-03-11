# Inventário: Vantagens, Desvantagens e Kits 3D&T

## Visão geral

| Livro | Conteúdo | Páginas típicas |
|-------|----------|-----------------|
| **Manual da Magia** | Vantagens/Desvantagens ligadas à magia | ~95+ |
| **Manual 3D&T Turbinado / Manual do Aventureiro** | Lista geral + Únicas | ~23, 41+ |

---

## Fase 1: Manual da Magia (3dt-manual-da-magia-biblioteca-elfica.pdf)

### Contexto (do próprio livro)

> O MANUAL DA MAGIA 3D&T é um livro específico para os usuários de magia. Este capítulo destina-se a desenvolver e apresentar uma lista de **novas Vantagens, Desvantagens e Kits de Personagem** ligados aos elementos mágicos.
>
> Além disso, aproveitamos para explicar as mudanças em algumas regras para o caso de se usar **regras de Magia Extrema**.

### Estrutura esperada (Manual da Magia)

| Tipo | Exemplos | Campos típicos |
|------|----------|----------------|
| **Vantagem** | Arquimago, Elementalista, Familiar, Magia Irresistível | Nome, Custo (pontos), Regras (Magia Extrema?), Efeito |
| **Desvantagem** | (a extrair) | Nome, Custo (negativo), Efeito |
| **Kit** | Elementalista (Água, Ar, Fogo, Terra, Espírito) | Nome, Custo, Poderes incluídos |

### Exemplos do Manual da Magia (pg. 95)

| Nome | Tipo | Custo | Nota |
|------|------|-------|------|
| Arquimago | Vantagem | (especial) | Apenas NPCs |
| Elementalista | Vantagem | 2 pts/elemento | Magia Extrema |
| Familiar | Vantagem | 2 pontos | PMs Extras x1, lista de animais |
| Magia Irresistível | Vantagem | 1–3 pontos | Redutor em Resistência |

---

## Fase 2: Manual 3D&T Turbinado Digital / Manual do Aventureiro

### Contexto

> Vantagens são diversos poderes extras que um personagem pode ter. Desvantagens são coisas ruins que atrapalham — mas dão pontos para gastar.
>
> **Únicas**: cada personagem pode possuir apenas uma (Anão, Elfo, Paladino...). Trazem um "pacote" de outras V/D incluídas.

### Estrutura esperada

| Tipo | Exemplos | Campos típicos |
|------|----------|----------------|
| **Vantagem** | Aceleração, Adaptador, Aliado, Aparência Inofensiva | Nome, Custo, Efeito, Gasta PM? |
| **Desvantagem** | (a extrair) | Nome, Custo (negativo), Efeito |
| **Única** | Anão, Anfíbio, Centauro, Construto | Nome, Custo, Pacote incluído |

### Exemplos (pg. 23, 41)

| Nome | Tipo | Custo | Nota |
|------|------|-------|------|
| Aceleração | Vantagem | 1 ponto | H+1 perseguição, 1 PM em combate |
| Adaptador | Vantagem | 1 ponto | Mudar tipo de dano |
| Aliado | Vantagem | 1+ pontos | NPC companheiro |
| Aparência Inofensiva | Vantagem | 1 ponto | Ataque extra surpresa |
| Anão | Única | 2 pontos | Infravisão, Resistência à Magia, +1 Resistência |
| Anfíbio | Única | 0 pontos | Água, Radar, Ambiente Especial |
| Centauro | Única | 2 pontos | Modelo Especial, 2 ataques patas |
| Construto | Única | 0 pontos | Sem PV por descanso, imune veneno/mente |

---

## Plano de implementação

### Etapa 1: Extração do índice (Manual da Magia)

1. Identificar páginas do capítulo "NOVAS VANTAGENS E DESVANTAGENS" (~95)
2. Padrões para extrair nomes:
   - `Nome (X pontos)` ou `Nome (especial)`
   - `Nome (X ponto cada)` 
   - Linhas que começam com nome em negrito/caps
3. Separar Vantagens vs Desvantagens (por seção ou palavra-chave)

### Etapa 2: Extração de blocos (Manual da Magia)

1. Para cada nome do índice, localizar bloco completo
2. Campos a extrair:
   - `nome`, `tipo` (vantagem/desvantagem/kit)
   - `custo` (pontos, ou "especial")
   - `efeito` (texto descritivo)
   - `regras_especiais` (Magia Extrema, etc.)
   - `livro`, `pagina`

### Etapa 3: Taxonomia e categorização

1. Criar `data/processed/vantagens_desvantagens/taxonomia_manual_magia.json`
2. Categorias sugeridas:
   - `vantagem_magia` (Arquimago, Familiar, Magia Irresistível)
   - `vantagem_elemental` (Elementalista por elemento)
   - `desvantagem_magia`
   - `kit_elementalista`

### Etapa 4: Repetir para Manual Turbinado/Aventureiro

1. Índice das listas gerais (pg. 23) e Únicas (pg. 41)
2. Mesma estrutura de dados, campo `livro` distinto
3. Unificar ou manter separado por livro (a definir)

### Etapa 5: Reindexação no Chroma

1. Adicionar `tipo_chunk`: `vantagem_nome`, `vantagem_completo`, etc.
2. Metadados: `livro`, `tipo` (vantagem/desvantagem/kit), `custo`, `unica` (bool)

---

## Estrutura de dados proposta

```json
{
  "nome": "Familiar",
  "tipo": "vantagem",
  "custo": "2 pontos",
  "livro": "3dt-manual-da-magia-biblioteca-elfica.pdf",
  "pagina": 95,
  "efeito": "Você tem um pequeno animal mágico...",
  "regras_especiais": "Magia Extrema",
  "lista_animais": ["Camaleão", "Corvo", "Gato", "Cão/Lobo", "Macaco", "Sapo", "Serpente"]
}
```

---

## Scripts (Fase 1 - Manual da Magia)

| Script | Função |
|--------|--------|
| `scripts/extrair_indice_vantagens_magia.py` | Índice do Manual da Magia |
| `scripts/extrair_vantagens_magia_agressivo.py` | Busca e extrai blocos |
| `scripts/categorizar_vantagens.py` | Aplica taxonomia |
| `scripts/reindexar_vantagens.py` | Chroma para RAG |

### Pipeline

```bash
python scripts/extrair_indice_vantagens_magia.py
python scripts/extrair_vantagens_magia_agressivo.py
python scripts/categorizar_vantagens.py
python scripts/reindexar_vantagens.py
```

### Arquivos gerados

| Arquivo | Descrição |
|---------|-----------|
| `data/processed/vantagens_desvantagens/indice_vantagens_magia.txt` | Índice (nome \| custo) |
| `data/processed/vantagens_desvantagens/vantagens_magia_extraidas.json` | Extraídos |
| `data/processed/vantagens_desvantagens/vantagens_magia_categorizadas.json` | Com categoria |
| `data/processed/vantagens_desvantagens/efeitos_em_pericias.json` | Bônus/redutores em Perícias |
| `data/processed/vantagens_desvantagens/vantagens_por_categoria.txt` | Relatório |

### Efeitos em Perícias

O Mestre pode aplicar bônus/redutores em testes de Perícias conforme Vantagens e Desvantagens. Exemplos em `efeitos_em_pericias.json`:
- Aparência Inofensiva: +1 Lábia/Sedução; –2 Interrogatório/Intimidação
- Genialidade: +2 em todas as Perícias
- Inculto: –3 em todas, exceto Animais, Esportes, Sobrevivência

---

## Pendências

- [x] Filtrar blocos com qualidade OCR ruim (implementado em `extrair_itens_magicos_agressivo.py`)
- [x] Definir ordem de prioridade entre PDFs quando mesmo item em vários livros (ver `politica_prioridade_fontes.json` e `src/utils/livro_normalizado.py`)

## Política de Prioridade entre Fontes

Quando o mesmo item (vantagem, magia, etc.) aparece em vários livros, usa-se a fonte com maior prioridade. Ordem definida em `data/processed/politica_prioridade_fontes.json`:

1. Manual 3D&T Turbinado
2. Manual do Aventureiro
3. Manual da Magia
4. Alpha / outros

O `reindexar_vantagens.py` mescla `vantagens_turbinado_canonico.json` + `vantagens_magia_*`, aplicando essa prioridade.
