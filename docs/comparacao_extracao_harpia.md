# Comparação: Livro vs Extraído — Harpia

> Conteúdo do **Manual dos Monstros 3D&T Alpha** (fornecido pelo usuário) vs extração atual.

---

## 1. O que está no livro (Manual dos Monstros)

| Seção | Conteúdo |
|-------|----------|
| **Citação** | *"Você ouviu esse grito? Não entro ali nem morta!"* — Dellana, caçadora de monstros |
| **Descrição física** | Tronco e cabeça de mulher, garras no lugar dos pés, asas de pássaro. Cabelos emaranhado sujo; penas marrons cobertas de cascas secas de sangue. Olhos negros, expressões ameaçadoras. Vozes estridentes, enervam e amedrontam. |
| **Lore** | Nunca vistos machos; acredita-se fracos para voar, confinados em cavernas secretas, servindo apenas para reprodução. Incrivelmente sádicas, adoram causar sofrimento. Alvos preferidos: filhotes de todas as espécies, especialmente humanoides inteligentes. |
| **Grito Aterrorizante** | 3 PMs por alvo. Teste de R: falha = Pânico por 1d+1 turnos; sucesso = abalada e indefesa por 1d turnos. Não é efeito mágico. Surdos ou imunes a medo não são afetados. |
| **Stat block** | Harpia, 8N — F2 (corte), H3, R2, A1, PdF2 (perfuração ou sônico); 10 PVs, 10 PMs; Sentidos Especiais (infravisão, faro e visão aguçados) e Voo; Insana (homicida), Má Fama, Modelo Especial e Monstruosa. |
| **Táticas** | Atacam em grupos de 1d indivíduos. Grito Aterrorizante no primeiro turno. Voam em torno, rasantes, garras. Outro grito quando efeito acaba, até sem PMs. Se inimigo forte: flechas com pés, à distância. Lutam até o fim. |
| **Pena Profana** | 1 PE: pena marrom malcheirosa; poção transforma braços em asas (voar 1 dia; impede segurar objetos). Maldição: insanidade -1; quebra Códigos de Honra. Uma pena = 2 doses. |
| **Olho de Harpia** | 8 PEs: olhos petrificados (carvão); canalizador mágico; metade dos PMs para magias de dano direto (não cumulativo). |

---

## 2. O que foi extraído (antes da correção)

| Campo | Extraído (Bestiário Alpha) | Livro (Manual dos Monstros) | Status |
|-------|---------------------------|-------------------------------|--------|
| **Fonte** | Bestiário Alpha | Manual dos Monstros | ❌ Fonte errada |
| **Canto / Dominação** | Canto 1d+96, Dominação Total | — | ❌ Bestiário tem; Manual não |
| **Grito Aterrorizante** | — | 3 PMs, Pânico, R | ❌ Ausente |
| **escala** | — | 8N | ❌ Ausente |
| **caracteristicas** | F2-3, H3-5, R2-3, A1, PdF2-3 | F2, H3, R2, A1, PdF2 | ⚠️ Diferente |
| **pv / pm** | variável / 0 | 10 / 10 | ❌ Errado |
| **descricao** | Canto, Dominação Total | Citação, física, lore, Grito | ❌ Conteúdo errado |
| **taticas** | Canto à distância, investidas | Grito 1º turno, rasantes, flechas | ❌ Errado |
| **tesouro** | — | Pena Profana, Olho de Harpia | ❌ Ausente |
| **habilidades** | Canto, Dominação, Levitação | Sentidos Especiais, Voo, Insana, Má Fama, etc. | ❌ Errado |

---

## 3. Conclusão

A Harpia no `monstros_extraidos.json` vem do **Bestiário Alpha**, que tem mecânicas diferentes (Canto, Dominação Total). O **Manual dos Monstros** descreve outra versão: Grito Aterrorizante, 8N, 10 PVs/10 PMs, Pena Profana, Olho de Harpia.

**Correção aplicada:** PILOTO_EXTRA atualizado com o conteúdo do Manual dos Monstros. O `monstros_modelo_enriquecido.json` agora exibe a Harpia correta (Grito Aterrorizante, 8N, 10/10, táticas, tesouro).

---

## 4. Fluxo de avaliação

Para garantir consistência no futuro:

```bash
# 1. Extrair (já feito pela varredura)
python scripts/varredura_completa_monstros.py

# 2. Avaliar e comparar
python scripts/avaliar_extracao_monstro.py Harpia --referencia data/referencia_monstros/harpia.json --saida docs/avaliacao_harpia.md

# 3. Preencher: atualizar PILOTO_EXTRA em extrair_monstros_modelo_enriquecido.py com os dados da referência
# 4. Reaplicar e sincronizar
python scripts/extrair_monstros_modelo_enriquecido.py
python scripts/sync_monstros_frontend.py
```

Referências do livro ficam em `data/referencia_monstros/` para comparação.
