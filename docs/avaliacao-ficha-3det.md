# Avaliação da Ficha de Personagem — 3D&T Turbinado

## Resumo executivo

A ficha atual está **parcialmente alinhada** ao Manual 3D&T Turbinado (Defensores de Tóquio 3ª Ed., p. 144). O que funciona bem: pontuação, características (F, H, R, A, PdF), caminhos da magia, vantagens/desvantagens, raças e custos. O que precisa de ajuste para ficar jogável segundo o 3D&T: **cálculo automático de PV e PM** a partir de Resistência e das vantagens Pontos de Vida Extras / Pontos de Magia Extras.

---

## 1. O que está correto

### 1.1 Pontuação e custos
- **PONTUACAO_BASE** por nível: pessoa_comum (4), novato (5), lutador (7), campeão (10), lenda (12) — conforme o manual.
- **MAX_CARAC_FOCUS** por nível — limites de características e Focus corretos.
- **custoCaracteristicas**, **custoCaminhosMagia**, **custoVantagens**, **custoRaca** — lógica correta.
- **pontosDesvantagens** — desvantagens dão pontos extras corretamente.
- **custoRaca** — raças com custo negativo (Morto-Vivo -2, Goblin -2, Meio-Orc -1) dão pontos extras corretamente.

### 1.2 Características (F, H, R, A, PdF)
- Estrutura correta.
- Modificadores raciais aplicados via `aplicarModificadoresRaca`.
- Validação de limites por nível.

### 1.3 Caminhos da Magia
- Seis caminhos (Água, Ar, Fogo, Luz, Terra, Trevas).
- Focus limitado pelo nível.

### 1.4 Vantagens, desvantagens e raças
- Dependências entre vantagens/desvantagens tratadas.
- Pacotes raciais com vantagens, desvantagens e modificadores.
- Tipos de dano (Força, PdF) configuráveis.

---

## 2. O que precisa mudar

### 2.1 PV e PM — regra do 3D&T Turbinado

No 3D&T Turbinado, **PV e PM base** são derivados da **Resistência (R)**:

| Fórmula base | Fonte |
|--------------|-------|
| **PV base = 5 × R** | monstros.json (ex.: Drogadora R2 → 10 PVs, 10 PMs) |
| **PM base = 5 × R** | monstros.json (ex.: Pégaso R4 → "R4×5=20 PMs") |

**Mínimo sugerido:** 5 PV e 5 PM quando R = 0 (personagem muito frágil).

**Vantagens que modificam:**
- **Pontos de Vida Extras** — adiciona PV (custo em pontos; cada nível adiciona +5 PV).
- **Pontos de Magia Extras** — adiciona PM (custo em pontos; cada nível adiciona +5 PM).

**Exemplo (monstros.json):**
- Devitorimm (R1): base 5 PV, 5 PM. Com "Pontos de Vida Extras" → 15 PVs totais (+10).
- Drogadora (R2): 10 PVs, 10 PMs (sem extras).

### 2.2 Implementação atual (problema)

Hoje a ficha trata PV e PM como **valores manuais** (1–30), com padrão 6/6:

```ts
// personagemStore.ts — pvMax/pmMax editáveis manualmente
pvMax: 6, pvAtual: 6, pmMax: 6, pmAtual: 6
```

Não há:
1. Cálculo automático a partir de R.
2. Vantagens "Pontos de Vida Extras" e "Pontos de Magia Extras" em `vantagens_turbinado.json`.
3. Integração dessas vantagens no cálculo de PV/PM.

### 2.3 Ajustes recomendados

#### A) Adicionar vantagens em `vantagens_turbinado.json`

```json
{
  "nome": "Pontos de Vida Extras",
  "tipo": "vantagem",
  "unica": false,
  "custo": "1 ponto",
  "efeito": "Adiciona 5 PV ao total base (5×R). Pode ser comprada múltiplas vezes.",
  "livro": "Manual 3D&T Turbinado"
},
{
  "nome": "Pontos de Magia Extras",
  "tipo": "vantagem",
  "unica": false,
  "custo": "1 ponto",
  "efeito": "Adiciona 5 PM ao total base (5×R). Pode ser comprada múltiplas vezes.",
  "livro": "Manual 3D&T Turbinado"
}
```

*(Custos exatos devem ser conferidos no manual.)*

#### B) Calcular PV/PM em `construcaoPersonagem.ts`

```ts
/** PV base = 5 × R (mín. 5). +5 por cada "Pontos de Vida Extras". */
export function calcularPvMax(
  rEfetivo: number,
  vantagens: string[]
): number {
  const base = Math.max(5, 5 * rEfetivo);
  const extras = vantagens.filter(n => n === "Pontos de Vida Extras").length;
  return base + extras * 5;
}

/** PM base = 5 × R (mín. 5). +5 por cada "Pontos de Magia Extras". */
export function calcularPmMax(
  rEfetivo: number,
  vantagens: string[]
): number {
  const base = Math.max(5, 5 * rEfetivo);
  const extras = vantagens.filter(n => n === "Pontos de Magia Extras").length;
  return base + extras * 5;
}
```

#### C) Usar cálculo na ficha

- **pvMax** e **pmMax** passam a ser **calculados** a partir de R efetiva e vantagens.
- Manter **pvAtual** e **pmAtual** editáveis (marcação de dano/gasto).
- Opcional: permitir override manual (ex.: checkbox "Valores personalizados") para casos especiais.

#### D) Construto e Morto-Vivo

- **Construto:** não recupera PV por descanso (já em `racaPacote`).
- **Morto-Vivo:** regras específicas de cura (não cura com medicina; Cura para os Mortos).

Essas regras podem ficar em texto/efeitos; a lógica de cálculo de PV/PM base continua a mesma.

---

## 3. Outros pontos (menor prioridade)

### 3.1 Energia Extra
Vantagem que permite trocar PV ↔ PM ou recuperar PV gastando PM. Pode ser adicionada depois como efeito textual; não altera o cálculo de PV/PM máximos.

### 3.2 Recuperação
- Descanso: regras de recuperação de PV/PM (ex.: 1d por noite).
- Construto: só recupera PV com Perícia Máquinas (teste H+1 = 1 PV em meia hora).

Não é crítico para a ficha inicial; pode ser documentado ou implementado em uma fase posterior.

### 3.3 FA e FD (Força de Ataque / Força de Defesa)
- FA = F + H + 1d (corpo a corpo) ou PdF + H + 1d (à distância).
- FD = A + H + 1d.

Útil para combate, mas não essencial para a criação de personagem. Pode ser uma fase futura.

---

## 4. Checklist de implementação

| Item | Status | Prioridade |
|------|--------|------------|
| Cálculo PV base = 5×R (mín. 5) | Pendente | Alta |
| Cálculo PM base = 5×R (mín. 5) | Pendente | Alta |
| Vantagem "Pontos de Vida Extras" | Pendente | Alta |
| Vantagem "Pontos de Magia Extras" | Pendente | Alta |
| Integrar vantagens no cálculo de PV/PM | Pendente | Alta |
| pvAtual/pmAtual apenas para marcar dano/gasto | OK | — |
| Override manual (opcional) | Pendente | Baixa |

---

## 5. Conclusão

A ficha está bem estruturada para o 3D&T Turbinado em pontos, características, magia e raças. Para ficar jogável:

1. **Adicionar** as vantagens Pontos de Vida Extras e Pontos de Magia Extras.
2. **Calcular** PV e PM automaticamente com base em R e nessas vantagens.
3. **Usar** pvMax/pmMax calculados na ficha, mantendo pvAtual/pmAtual apenas para marcar dano/gasto.

Com isso, a ficha passa a ficar alinhada às regras do 3D&T Turbinado e pronta para uso em jogo.
