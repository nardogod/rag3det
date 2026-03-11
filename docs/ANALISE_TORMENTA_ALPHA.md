# Análise: 3DT Alpha Tormenta Alpha

Livro de cenário e regras que adapta o mundo de **Tormenta/Arton** ao sistema **3D&T Alpha** (estilo anime/games). Publicado pela Jambô (2016), 192 páginas.

---

## 1. Do que se trata

**Tormenta Alpha** é um suplemento de cenário que:

- **Une Tormenta e 3D&T Alpha** — Arton em estilo exagerado, veloz e colorido (anime/games)
- **Escala de poder ampliada** — heróis podem enfrentar avatares, Lordes da Tormenta e deuses
- **Tipos de campanha** — Heroica, Épica, Titânica e Divina
- **Vantagens regionais** — bônus por origem (Reinado, Liga, Império de Tauron, etc.)
- **Patronos** — organizações que oferecem benefícios por 1 PM (ajuda em teste, item, aliado temporário)
- **Geografia de Arton** — reinos, lugares para conhecer/evitar, lore

---

## 2. Estrutura do livro (capítulos)

| Cap. | Título | Conteúdo principal |
|------|--------|--------------------|
| **1** | Um Mundo de Heróis | Criação de personagens, vantagens regionais, patronos, geografia (Reinado, Deheon, Hongari, Khubar, Namalkah, Pondsmânia, Portsmouth, etc.) |
| **2** | Um Mundo de Problemas | Guia do Mestre — mestrar, preparar sessões, desafios |
| **3** | A Campanha Heroica | Campanha de nível inicial, escalas Ningen, lugares e missões |
| **4** | A Campanha Épica | Escala Sugoi, Protetorado do Reino, missões de alto nível |
| **5** | (Deuses/Avatares) | Panteão, avatares, superkits divinos |
| **6** | (Torneio/Emissários) | Torneio de Keenn, emissários, fichas de NPCs |

---

## 3. Conteúdo extraível

### 3.1 Vantagens regionais
- **Estrutura:** nome, reino, efeito básico, efeito +1 ponto, patrono
- **Exemplos:** Aventureiro Nato (Deheon), Esperteza (Ahlen), Cavaleiro Nato (Bielefeld), Olhos Especiais (Collen), Patriota (Hongari), Tatuagens Místicas (Khubar), Irmão Equestre (Namalkah), Conhecimento de Fadas (Pondsmânia), Faro para Magos (Portsmouth)
- **Uso:** complementar `vantagens_turbinado_canonico.json` ou criar `vantagens_tormenta_alpha.json`

### 3.2 Patronos
- **Estrutura:** organização, exigências, benefícios (lista de ajudas por 1 PM)
- **Exemplos:** reino de Deheon, Ahlen, Hongari, Khubar, Namalkah, Pondsmânia, Portsmouth, Protetorado do Reino
- **Uso:** nova entidade `patronos` para RAG — "Quais benefícios o Patrono de Hongari oferece?"

### 3.3 Geografia / lugares
- **Estrutura:** reino, capital, lugares para conhecer, lugares para evitar
- **Uso:** `lugares_arton.json` — suporte a narrativa, exploração, encontros

### 3.4 Fichas de NPCs
- **Exemplos:** Orontes (Swashbuckler), Emissário do Torneio de Keenn (Guerreiro Arauto)
- **Formato:** F/H/R/A/PdF, PVs, PMs, Kits, Vantagens, Desvantagens
- **Uso:** integrar ao gerador de NPCs ou inventário de personagens pré-prontos

### 3.5 Tipos de campanha e escalas
- Heroica (Ningen), Épica (Sugoi), Titânica, Divina
- **Uso:** regras para balanceamento de encontros e desafios

### 3.6 Superkits (ex.: Avatar)
- Exigências, funções, poderes especiais
- **Uso:** complementar kits ou vantagens únicas

---

## 4. Como utilizar no projeto

### Opção A — Extração modular
1. **Vantagens regionais** — regex/heurística para blocos "Vantagem regional: X"
2. **Patronos** — blocos "Patrono: X" + lista de benefícios
3. **Lugares** — "Lugares para conhecer:", "Lugares para evitar:"
4. **NPCs** — padrão F/H/R/A, PdF, PVs, PMs, Kits

### Opção B — Ingestão completa
- Rodar `extrair_monstros_agressivo.py` — já processa todos os PDFs (inclui Tormenta Alpha)
- Criar `extrair_tormenta_alpha.py` — extrator específico para vantagens regionais, patronos e lugares

### Opção C — RAG direto
- Ingerir o PDF como chunks no Chroma (já feito se estiver em SOURCE_PDF_DIR)
- O Mestre Autônomo pode usar o conteúdo via busca semântica

---

## 5. Integração com dados existentes

| Dado existente | Tormenta Alpha complementa |
|----------------|----------------------------|
| `vantagens_turbinado_canonico.json` | Vantagens regionais (novas) |
| `kits_canonico.json` | Superkits (Avatar, etc.) |
| `mestre_canonico.json` | Guia do Mestre (Cap. 2) |
| `personagem_canonico.json` | Regras de criação para Arton |
| Monstros | Demônios da Tormenta já no Bestiário; cenário amplia contexto |

---

## 6. Prioridade sugerida

1. **Alta** — Incluir PDF no pipeline de ingestão (já em SOURCE_PDF_DIR) para RAG
2. **Média** — Extrair vantagens regionais e patronos para buscas estruturadas
3. **Baixa** — Extrair lugares e NPCs para enriquecer cenários

---

## 7. Observações

- O livro **depende do Manual 3D&T Alpha** (não repete regras básicas)
- **Manual da Magia (Tormenta Alpha)** é suplemento separado (110+ magias, 310 itens)
- Demônios da Tormenta, áreas de Tormenta e criaturas relacionadas já aparecem no **Bestiário Alpha**
