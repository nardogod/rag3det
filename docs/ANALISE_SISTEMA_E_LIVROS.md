# Análise Minuciosa do Sistema 3D&T e Livros

Análise comparativa do sistema, padrões, lacunas e recomendações. Inclui resumo do objetivo de cada livro.

---

## 1. Padrões Identificados

### 1.1 Pipeline de Inventários

| Padrão | Entidades | Fluxo |
|--------|-----------|-------|
| **Canônico** | mestre, personagem, regras_combate, pericias | `*_canonico.json` → `extrair_*` → `*_consolidado.json` → `reindexar_*` |
| **Extração PDF** | magias, itens_magicos, vantagens | `extrair_*_agressivo.py` → `*_extraidas.json` → `categorizar_*` (opcional) → `reindexar_*` |
| **Híbrido** | pericias | `pericias_canonico.json` como fallback; extração PDF quando canônico incompleto |

### 1.2 Estrutura de Dados por Tipo

| Tipo | Campos típicos | Exemplo |
|------|----------------|---------|
| **Regras** (mestre, regras_combate, personagem) | id, categoria, titulo, descricao, formula, modificadores, livro, pagina | Blocos estruturados |
| **Entidades** (magias, itens, vantagens) | nome, tipo, custo, efeito/descricao, livro, pagina | Lista de itens |
| **Schema** (ficha) | schema com campos (caracteristicas, caminhos_magia...) | Metadado especial |

### 1.3 Metadados Chroma

Todos os reindexadores usam `tipo`, `tipo_chunk` (nome/cabecalho/completo), `livro`, e campos específicos (custo, categoria, etc.).

---

## 2. Lacunas e Itens que Podem Ter Passado Despercebidos

### 2.1 Correções Aplicadas

- **regras_3dt.py**: `PdF` estava como "Pontos de Fé" → corrigido para "Poder de Fogo"; `FA` estava como "Fator de Ataque" → corrigido para "Força de Ataque".

### 2.2 Vantagens do Manual Turbinado / Manual do Aventureiro

- **Situação**: `extrair_vantagens_magia_agressivo.py` extrai apenas do **Manual da Magia** (Vantagens ligadas à magia).
- **Resolvido**: Criado `vantagens_turbinado_canonico.json` com Aceleração, Aliado, Anão, Elfo, Construto, etc. O `reindexar_vantagens.py` mescla turbinado + magia com prioridade de fontes.

### 2.3 Magias do Manual Turbinado Digital

- **Situação**: INVENTARIO_MAGIAS indica 0 magias do Manual 3D&T Turbinado Digital.
- **Contexto**: O Manual Turbinado é o livro base; magias básicas (Bola de Fogo, Invisibilidade, etc.) podem estar nele.
- **Recomendação**: Verificar se o Manual Turbinado tem capítulo de magias e incluir na extração.

### 2.4 Magias Não Encontradas (7)

- Brilho de Espírito, Chicote das Trevas, Comando de Khalmyr, Feras de Tenebra, Nevoeiro de Sszzaas, Pequenos Desejos, Ressurreição.
- **Status**: `magias_nao_encontradas_canonico.json` documenta as 7 magias com escola e status. Pequenos Desejos tem nota (Meio-Gênios). Busca em outros PDFs ou inserção manual ainda pendente.

### 2.5 Bestiário / Monstros

- **Situação**: Manual dos Monstros e Bestiário são usados para itens e magias. Estrutura definida em `INVENTARIO_MONSTROS.md` e `data/processed/monstros/schema_monstros.json`.
- **Pendente**: Extrator e dados (`monstros_extraidos.json`) ainda não implementados; extração de criaturas com F/H/R/A, PV, habilidades.

### 2.6 Kits de Personagem

- **Resolvido**: `kits_canonico.json` com 8 Kits (Arqueiro Arcano, Guerreiro Mágico, Magi-Ranger, Clérigo, Paladino, Druida, Xamã, Elementalista). `reindexar_vantagens.py` carrega Kits separadamente com `tipo: "kit"` e `tipo_chunk: kit_nome/kit_cabecalho/kit_completo`.

### 2.7 Deuses e Clérigos

- **Situação**: SISTEMA_3DT_VISAO_GERAL e texto do Manual Turbinado indicam que "Deuses e Clérigos" foi movido para Manual do Aventureiro (Kits para clérigos, paladinos, druidas, xamãs).
- **Recomendação**: Se Kits do Aventureiro forem extraídos, incluir clérigo, paladino, druida, xamã, cultista.

### 2.8 Tabelas de Dificuldade (CD)

- **Resolvido**: Bloco `classe_dificuldade` em `regras_combate_canonico.json` com CD sugeridas (Fácil=3, Normal=4, Difícil=5, Muito Difícil=6).

### 2.9 Recuperação de PVs e PMs

- **Resolvido**: Bloco `recuperacao_pv_pm` em `personagem_canonico.json` com valores concretos: descanso curto (15–30 min) = 1 PV/h de R; descanso longo (1–2 h) = 1d PV/h de R; noite completa = todos PVs e PMs.

### 2.10 Ordem de Prioridade entre PDFs

- **Resolvido**: Política em `data/processed/politica_prioridade_fontes.json`. Ordem: Manual Turbinado > Manual do Aventureiro > Manual da Magia > Alpha. Aplicada em `reindexar_vantagens.py` (merge turbinado + magia). `livro_normalizado.py` usado em reindexar_vantagens, reindexar_magias e reindexar_itens para exibição consistente. Merge com prioridade para magias/itens (quando mesma entidade em vários PDFs) pode ser estendido nos extractors.

---

## 3. Inconsistências e Melhorias

### 3.1 Nomenclatura de Livros

- **Resolvido**: Módulo `src/utils/livro_normalizado.py` com `normalizar_livro()` para exibição uniforme. Mapeamento de PDFs e variações para nomes legíveis (ex.: `3dt-manual-da-magia-biblioteca-elfica.pdf` → "Manual da Magia").

### 3.2 SISTEMA_3DT_VISAO_GERAL

- **Resolvido**: SISTEMA_3DT_VISAO_GERAL lista todos os inventários: Mestre, Personagem, Regras de Combate, Poder de Gigante, Magias, Itens mágicos, Vantagens/Desvantagens/Kits, Perícias, Monstros.

### 3.3 Reindexadores sem Dados Canônicos

- **Vantagens**: Resolvido — `vantagens_turbinado_canonico.json` e `kits_canonico.json` como fallback; reindexar mescla turbinado + magia com prioridade.
- **Itens mágicos**: Pendente — ainda depende só de extração PDF; criar `itens_magicos_canonico.json` parcial como fallback (prioridade baixa).

---

## 4. Resumo do Objetivo de Cada Livro

| Livro | Objetivo |
|-------|----------|
| **Manual 3D&T Turbinado Digital** | Livro base: regras gerais, características, construção de personagem, combate, Mestre, aventuras. Versão "turbinada" com PMs, novo turno de combate, acertos críticos. |
| **Manual da Magia** | Suplemento de magia: novas Vantagens/Desvantagens/Kits mágicos, Objetos Mágicos (categorias), regras de Magia Extrema. |
| **Manual da Magia Alpha** | Versão Alpha do Manual da Magia: maior conjunto de magias (142), índice das 300 magias. |
| **Manual Revisado (Alpha)** | Revisão do manual base: 111 magias, atualizações de regras. |
| **Manual Revisado Ampliado e Turbinado** | Versão ampliada com formato "Exigências" em magias; OCR problemático. |
| **Manual dos Dragões** | Suplemento de dragões: magias de sopro e temáticas (17 magias). |
| **Manual dos Monstros** | Bestiário: criaturas, tesouros, equipamento em descrições; 1 magia. |
| **Manual Alpha (genérico)** | Versão Alpha do manual base; magias diversas. |
| **Bestiário Alpha** | Catálogo de monstros; itens mágicos em descrições. |
| **Manual do Aventureiro** | Kits de personagem (clérigo, paladino, druida, xamã, cultista, arqueiro arcano, etc.), Perícias, possivelmente Vantagens gerais. |
| **3D&T Defensores de Tóquio 3ª Edição** | Edição específica com Ficha de Personagem padronizada (pg 144). |
| **U.F.O.Team, Só Aventuras, Arcano Preview** | Suplementos citados; conteúdo específico a confirmar. |

---

## 5. Prioridades de Implementação

| Prioridade | Item | Status |
|------------|------|--------|
| Alta | Vantagens do Manual Turbinado (Aceleração, Aliado, Anão, Elfo...) | Feito — `vantagens_turbinado_canonico.json` |
| Alta | Corrigir regras_3dt (PdF, FA) | Feito |
| Alta | Política de prioridade entre PDFs | Feito — `politica_prioridade_fontes.json`, `livro_normalizado.py` |
| Média | Bloco CD (Classe de Dificuldade) no canônico | Feito — `regras_combate_canonico.json` |
| Média | Recuperação PVs/PMs no canônico | Feito — `personagem_canonico.json` |
| Média | Atualizar SISTEMA_3DT_VISAO_GERAL | Feito |
| Média | Kits como entidade separada | Feito — `kits_canonico.json`, reindexar com tipo kit |
| Média | Nomenclatura de livros | Feito — `livro_normalizado.py` |
| Baixa | Inventário de monstros/criaturas (extrator + dados) | Pendente — schema definido |
| Baixa | 7 magias não encontradas (busca/inserção) | Pendente — canônico documenta |
| Baixa | itens_magicos_canonico.json fallback | Pendente |

---

## 6. Arquivos Relacionados

- [docs/INVENTARIO_MESTRE.md](INVENTARIO_MESTRE.md)
- [docs/INVENTARIO_PERSONAGEM.md](INVENTARIO_PERSONAGEM.md)
- [docs/INVENTARIO_REGRAS_COMBATE.md](INVENTARIO_REGRAS_COMBATE.md)
- [docs/INVENTARIO_MAGIAS.md](INVENTARIO_MAGIAS.md)
- [docs/INVENTARIO_VANTAGENS_DESVANTAGENS_KITS.md](INVENTARIO_VANTAGENS_DESVANTAGENS_KITS.md)
- [docs/INVENTARIO_ITENS_MAGICOS.md](INVENTARIO_ITENS_MAGICOS.md)
- [docs/INVENTARIO_PERICIAS.md](INVENTARIO_PERICIAS.md)
- [docs/INVENTARIO_MONSTROS.md](INVENTARIO_MONSTROS.md)
- [docs/INVENTARIO_PODER_GIGANTE.md](INVENTARIO_PODER_GIGANTE.md)
- [docs/SISTEMA_3DT_VISAO_GERAL.md](SISTEMA_3DT_VISAO_GERAL.md)

---

## 7. Revisão Completa — Status por Livro e Inventário

| Livro / Inventário | Dados | Reindexador | Status |
|--------------------|-------|-------------|--------|
| **Manual 3D&T Turbinado** | personagem, regras_combate, mestre, vantagens_turbinado | extrair_*, reindexar_* | OK |
| **Manual da Magia** | magias, itens_magicos, vantagens_magia, kits | extrair_*_agressivo, reindexar_* | OK |
| **Manual do Aventureiro** | Kits (clérigo, paladino, druida) em kits_canonico | reindexar_vantagens | OK |
| **Manual Alpha / Revisado** | magias (142+111) | extrair_magias_agressivo | OK |
| **Manual dos Monstros** | itens em descrições; 1 magia | extração parcial | OK |
| **Bestiário Alpha** | itens em descrições | extração parcial | OK |
| **Manual dos Dragões** | 17 magias | extrair_magias_agressivo | OK |
| **Monstros (F/H/R/A, PV)** | schema definido | — | Pendente extrator |
| **7 magias não encontradas** | magias_nao_encontradas_canonico | reindexar_magias | Documentadas; busca pendente |
