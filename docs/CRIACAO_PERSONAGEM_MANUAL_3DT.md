# Criação de Personagem 3D&T — Mapeamento do Manual

Mapeamento dos capítulos do Manual 3D&T Turbinado para o sistema de criação de personagem.

---

## 1. Os Heróis (p. 8)

**O que cobre:** Conceito do personagem, papel do jogador, primeiros passos.

| Item | Implementado | Onde |
|------|--------------|------|
| Conceito (guerreiro, mago, etc.) | Parcial | Campo `historia` na ficha; sem seleção de conceito |
| Construção: Conceito → Ficha → Pontos | ✅ | `personagem_canonico.json`, `construcaoPersonagem.ts` |

**Necessário para criação:** Campo livre de conceito ou seleção de arquétipo (opcional).

---

## 2. Os Números (p. 14)

**O que cobre:** Características F, H, R, A, PdF; fórmulas; tabelas de referência.

| Item | Implementado | Onde |
|------|--------------|------|
| Características (F, H, R, A, PdF) | ✅ | `personagem.ts`, `FichaPersonagemPage.tsx` |
| Custo 1 pt = 1 Característica | ✅ | `construcaoPersonagem.ts` |
| Máximo por nível (1–5) | ✅ | `MAX_CARAC_FOCUS` |
| Fórmulas FA, FD | ✅ | `regras_combate_canonico.json` |
| Tabelas (levantar peso, etc.) | ✅ | `personagem_canonico.json` |

**Necessário para criação:** ✅ Completo.

---

## 3. Vantagens e Desvantagens (p. 22)

**O que cobre:** Vantagens e desvantagens comuns (não-únicas).

| Item | Implementado | Onde |
|------|--------------|------|
| Lista de vantagens | ✅ | `vantagens_turbinado.json` |
| Lista de desvantagens | ✅ | `vantagens_turbinado.json` |
| Custo em pontos | ✅ | `parseCusto()`, `construcaoPersonagem.ts` |
| Dependências (ex.: Fada exclui Resistência à Magia) | ✅ | `dependencias.ts` |
| Cálculo de pontos (base + desv − gastos) | ✅ | `pontosDisponiveis()` |

**Necessário para criação:** ✅ Completo. Revisar se há vantagens/desvantagens faltando nos livros.

---

## 4. Vantagens e Desvantagens Únicas (p. 40)

**O que cobre:** Raças e pacotes únicos (Anão, Elfo, Fada, Licantropo, etc.).

| Item | Implementado | Onde |
|------|--------------|------|
| Raças (tipo "unica") | ✅ | `vantagens_turbinado.json`, `racas` em `vantagens.ts` |
| Especificação Única (label, badge) | ✅ | `vantagens-desvantagens-unicas.mdc`, UI |
| Custo da raça | ✅ | `custoRaca()` |
| Uma Única por personagem | ✅ | Modal raça com `multiSelect={false}` |

**Raças incluídas:** Anão, Anfíbio, Centauro, Construto, Elfo, Fada, Goblin, Halfling, Meio-Dragão, Morto-Vivo, Brownie, Meio-Gênio, Sátiro, Dragonete, Grig, Pixie, Licantropo.

**Necessário para criação:** ✅ Completo.

---

## 5. Perícias (p. 50)

**O que cobre:** Animais, Arte, Ciência, Crime, Esporte, Idiomas, Investigação, Manipulação, Máquinas, Medicina, Sobrevivência; Especializações.

| Item | Implementado | Onde |
|------|--------------|------|
| Lista de perícias | ✅ | `pericias_canonico.json` |
| Custo (2 pts cada) | ✅ | `pericias_canonico.json` |
| Especializações | ✅ | `pericias_canonico.json` |
| **Seleção na ficha** | ❌ | **Falta:** `pericias` na `FichaPersonagem`, store, UI |
| Cálculo de pontos (perícias) | ❌ | **Falta:** incluir custo de perícias em `pontosDisponiveis` |

**Necessário para criação:** ❌ **Adicionar:** campo `pericias: string[]` e `especializacoes: string[]` na ficha; seção Perícias na UI; custo no cálculo de pontos.

---

## 6. Regras e Combate (p. 56)

**O que cobre:** Dados, turnos, testes, CD, iniciativa, FA, FD, dano.

| Item | Implementado | Onde |
|------|--------------|------|
| Regras gerais (dados, turno, testes) | ✅ | `regras_combate_canonico.json` |
| Classe de Dificuldade | ✅ | `regras_combate_canonico.json`, `master/regras_3dt.ts` |
| Fórmulas FA, FD | ✅ | `regras_combate_canonico.json` |
| Combate (iniciativa, dano) | ✅ | `regras_combate_canonico.json` |

**Necessário para criação:** Usado em jogo; não bloqueia criação. ✅ Referência disponível.

---

## 7. Magos e Magia (p. 72)

**O que cobre:** Caminhos (Água, Ar, Fogo, Luz, Terra, Trevas), Focus, magias.

| Item | Implementado | Onde |
|------|--------------|------|
| Caminhos de Magia | ✅ | `personagem.ts`, `CAMINHOS_MAGIA` |
| Focus por caminho | ✅ | `caminhosMagia` na ficha |
| Custo Focus (1 pt cada) | ✅ | `custoCaminhosMagia()` |
| Magias conhecidas | ✅ | `magiasConhecidas[]`, `magias.ts` |
| Dependências (Focus para magia) | ✅ | `dependencias.ts`, `magiasDisponiveis` |

**Necessário para criação:** ✅ Completo.

---

## 8. Objetos Mágicos (p. 114)

**O que cobre:** Itens mágicos, poções, armas especiais.

| Item | Implementado | Onde |
|------|--------------|------|
| Lista de itens mágicos | ✅ | `itens_magicos_canonico.json` |
| **Seleção na ficha** | Parcial | `dinheiroItens` (campo texto livre) |
| Custo em pontos | ❌ | Itens geralmente conquistados em campanha |

**Necessário para criação:** Opcional. Itens mágicos costumam ser obtidos em jogo. Campo `dinheiroItens` existe para anotações.

---

## 9. Poder de Gigante e Infinito (p. 120)

**O que cobre:** Regras para personagens muito poderosos, transformações épicas.

| Item | Implementado | Onde |
|------|--------------|------|
| Regras de alto nível | ❌ | Não extraído |
| Transformações | ❌ | — |

**Necessário para criação:** Não essencial para PJ recém-criado. Referência para campanhas avançadas.

---

## 10. O Mestre (p. 130)

**O que cobre:** Papel do Mestre, criação de aventuras, arbitragem.

| Item | Implementado | Onde |
|------|--------------|------|
| Guia do Mestre | ✅ | `mestre_canonico.json` |

**Necessário para criação:** Não bloqueia. Referência para Mestre.

---

## 11. Ficha de Personagem (p. 144)

**O que cobre:** Layout da ficha, campos obrigatórios.

| Campo da Ficha | Implementado | Onde |
|----------------|--------------|------|
| Nome | ✅ | `FichaPersonagemPage` |
| Nível de Pontuação | ✅ | pessoa_comum, novato, lutador, campeão, lenda |
| Raça (Única) | ✅ | |
| Características (F, H, R, A, PdF) | ✅ | |
| PV / PM | ✅ | |
| Vantagens | ✅ | |
| Desvantagens | ✅ | |
| Caminhos de Magia | ✅ | |
| Magias Conhecidas | ✅ | |
| **Perícias** | ❌ | **Falta** |
| **Especializações** | ❌ | **Falta** |
| História | ✅ | `historia` |
| Dinheiro/Itens | ✅ | `dinheiroItens` |
| Tipos de Dano | ✅ | `tiposDano` |

---

## Resumo: lacunas para criação completa

| Seção | Status | Ação |
|-------|--------|------|
| Os Heróis | Parcial | Opcional: conceito/arquétipo |
| Os Números | ✅ | — |
| Vantagens e Desvantagens | ✅ | — |
| Vantagens e Desvantagens Únicas | ✅ | — |
| **Perícias** | ❌ | **Adicionar seção na ficha + custo em pontos** |
| Regras e Combate | ✅ | — |
| Magos e Magia | ✅ | — |
| Objetos Mágicos | Parcial | Campo texto; itens em campanha |
| Poder de Gigante | ❌ | Opcional |
| O Mestre | ✅ | — |
| Ficha | Parcial | Falta Perícias e Especializações |

---

## Fluxo de criação (ordem sugerida)

1. **Nível de Pontuação** (Mestre define)
2. **Raça** (Vantagem Única — 0 a 4 pts)
3. **Características** (F, H, R, A, PdF — 1 pt cada)
4. **Caminhos de Magia** (Focus — 1 pt cada, se mago)
5. **Perícias** (2 pts cada) — **falta implementar**
6. **Especializações** (1 pt cada) — **falta implementar**
7. **Vantagens** (variável)
8. **Desvantagens** (dão pontos extras)
9. **Magias** (conforme Focus e dependências)
10. **PV/PM** (calculados por R)
11. **Dinheiro inicial** (1dx100 + modificadores)
12. **História, Itens** (texto livre)
