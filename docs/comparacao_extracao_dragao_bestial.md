# Comparação: Livro vs Extraído — Dragão Bestial

> O que você enviou está **exatamente** como no livro. Esta tabela compara com o que o extrator produziu.

---

## 1. O que está no livro (exatamente como você enviou)

| Seção | Conteúdo |
|-------|----------|
| **Citação** | *"Isso é profano. Uma das coisas mais cruéis que já vi. Gostei."* — Ocard, clérigo de Kallyadranoch |
| **Lore** | Sckhar, regente de Sckharshantallas; dragões como montaria/armas vivas; processo arcano; feras sem mente; cicatriz no olho esquerdo; alguns perdem asas; alguns perdem patas |
| **Cólera do Dragão** | 2 PMs = ataque adicional corpo-a-corpo; até F vezes/turno |
| **Modificações** | Perda de Telepatia, Aura de Pânico, Código de Honra, perícias, Arena, Riqueza, Forma Avatar, Presença Intimidante, Poder Inato; pode perder asas ou patas (H pela metade) |
| **Stat block** | Dragão Vermelho Adulto Bestial, 52S — F6 (corte), H6, R7, A7, PdF8 (fogo); 70 PVs, 35 PMs; Atroz, Dragão (Baforada); Patrono (Sckharshantallas) e Resistência à Magia; Insano (demente) |
| **Táticas** | Dragões bestiais não concebem táticas; aguardam ordens; gastam PMs com Baforada e Cólera |
| **Tesouro** | Clemência (Especial) — dobro de PEs |

---

## 2. O que foi extraído (monstros_extraidos.json)

| Campo | Valor extraído |
|-------|----------------|
| **nome** | Dragão Vermelho Adulto Bestial ✓ |
| **escala** | 52S ✓ |
| **caracteristicas** | F6, H6, R7, A7, PdF8 ✓ |
| **pv / pm** | 70 / 35 ✓ |
| **habilidades** | Atroz, Dragão (Baforada) ✓ |
| **taticas** | Dragões bestiais não são capazes de conceber táticas... ✓ |
| **tesouro** | Clemência (Especial)... ✓ |
| **descricao** | Começa em "Patrono (Sckharshantallas)..." — **falta o intro** |
| **habilidades_combate** | "s de ambas" (OCR truncou "Invulnerabilidades de ambas") |

### Descrição extraída (início)
```
Patrono (Sckharshantallas) e Resistência à Magia; Insano (demente). Atroz: criaturas atrozes...
Táticas Dragões bestiais não são capazes... Tesouro Clemência (Especial)...
Dragão Bicéfalo "Nem sempre duas cabeças pensam melhor do que uma."...
```

---

## 3. Lacunas (livro tem → extraído não tem)

| No livro | Extraído |
|----------|----------|
| Citação de Ocard | ❌ Ausente |
| Lore (Sckhar, Sckharshantallas, processo arcano, feras sem mente) | ❌ Ausente |
| Cicatriz no olho esquerdo, perda de asas/patas | ❌ Ausente |
| Cólera do Dragão (2 PMs = ataque extra; até F vezes/turno) | ❌ Ausente |
| Modificações (perda de Telepatia, Arena, etc.) | ❌ Ausente |
| Intro completo antes do stat block | ❌ Descrição começa no meio |
| Sem mistura com próximo monstro | ❌ Concatena com Dragão Bicéfalo |

---

## 4. Causa raiz

O extrator processava **cada página isoladamente**. O intro do Dragão Bestial está na **página 99** e o stat block na **página 100/101**. O `texto_antes` só via o início da página atual — não a página anterior.

Quando `descricao` ficava vazia, o fallback usava `bloco_apos[:2000]`, que incluía Táticas, Tesouro e o **próximo monstro** (Dragão Bicéfalo).

---

## 5. Correções implementadas

| Correção | Arquivo |
|----------|---------|
| Concatenação de páginas | `extrair_monstros_manual_completo()` em `extrair_monstros_manual_format.py` — extrai do texto completo em vez de página a página |
| Fallback sem próximo monstro | Quando `descricao` vazia, usa só Táticas+Tesouro (não `bloco_apos` que misturava com Dragão Bicéfalo) |
| Substituição no merge | `varredura_completa_monstros.py` — remove monstros antigos do Manual antes de mesclar, para que a nova extração substitua |

Após rodar `python scripts/varredura_completa_monstros.py`, a descrição do Dragão Bestial deve incluir citação, lore, Cólera e Modificações (se o PDF tiver o intro nas páginas anteriores ao stat block).

**Nota:** O Dragão Bestial tem override manual em `PILOTO_EXTRA` (extrair_monstros_modelo_enriquecido.py), então o `monstros_modelo_enriquecido.json` já exibe a descrição correta do livro. A correção do extrator beneficia outros monstros com intro em páginas anteriores.
