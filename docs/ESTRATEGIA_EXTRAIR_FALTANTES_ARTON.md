# Estratégia: Extrair ~126 Criaturas Faltantes do Livro de Arton

O Guia de Monstros de Arton tem **mais de 300 espécies**; a extração atual captura **~174**. Faltam ~126 criaturas.

## Diagnóstico

| Causa provável | Descrição |
|----------------|-----------|
| **Formato alternativo** | Bloco CON/FR/DEX/AGI sem F/H/R/A/PdF explícito |
| **Subvariantes** | "SOLDADO X", "XAMÃ X" dentro de blocos pais |
| **OCR degradado** | F/H/R/A/PdF ilegível (ex.: `1\` em vez de `A`) |
| **Agrupamentos** | Criatura descrita em seção genérica (ex.: "Grandes Felinos") |
| **Índice vs extração** | Nomes no índice que não geram match no texto |

---

## Estratégias de Extração

### Estratégia 1: Padrão CON/FR/DEX (daemon_con_format)
**Arquivo:** `src/ingestion/daemon_extractor_con_format.py`

O livro usa `CON X-Y, FR X-Y, DEX X-Y, AGI X-Y, INT X-Y, WILL X-Y, CAR X-Y, PER X-Y` antes de `#Ataques`. Converter para F/H/R/A/PdF:
- CON → R (Resistência)
- FR → F (Força)
- DEX → H (Habilidade)
- AGI → A (Armadura)

**Quando usar:** Blocos com CON/FR/DEX mas sem F/H/R/A/PdF detectável.

---

### Estratégia 2: Busca por Nome (daemon_por_indice)
**Arquivo:** `src/ingestion/daemon_extractor_por_indice.py`

1. Carregar índice de criaturas (docs/ANALISE ou índice do PDF)
2. Para cada nome **não** extraído, buscar no texto
3. Extrair bloco (nome → citação → descrição) mesmo sem stats
4. Usar `daemon_stats_fallback` (bestiário + parser de descrição) para F/H/R/A/PdF

**Quando usar:** Criaturas no índice que não têm bloco F/H/R/A/PdF.

---

### Estratégia 3: Padrões Relaxados (daemon_patterns_relaxed)
**Arquivo:** `src/ingestion/daemon_extractor_patterns_relaxed.py`

Ampliar regex para:
- `F?`, `H?`, `R?`, `A?`, `PdF?` com mais variações OCR
- `F\s*\d` sem vírgula obrigatória
- Blocos em linhas separadas (F2\nH1\nR3...)

**Quando usar:** Stats presentes mas em formato atípico.

---

### Estratégia 4: Subvariantes (daemon_subvariantes)
**Arquivo:** `src/ingestion/daemon_extractor_subvariantes.py`

Detectar padrões como:
- `SOLDADO HOBGOBLIN`, `ARQUEIRO HOBGOBLIN`, `XAMÃ GOBLIN`
- `CAPITÃO BUGBEAR`, `SARGENTO HOBGOBLIN`

Extrair como entradas separadas quando aparecem em blocos pais (ex.: Goblinóides, Hobgoblins).

**Quando usar:** Seções que agrupam variantes (Goblinóides, Gigantes, etc.).

---

### Estratégia 5: Orquestrador (scripts/extrair_faltantes_arton.py)
**Arquivo:** `scripts/extrair_faltantes_arton.py`

1. Rodar `identificar_faltantes_arton.py` → lista de nomes faltantes
2. Rodar extrator principal (daemon_extractor_dedicado)
3. Rodar estratégias 1–4 em sequência
4. Mesclar resultados (evitar duplicatas por nome)
5. Aplicar modelo enriquecido

---

## Fluxo Recomendado

```
1. python scripts/identificar_faltantes_arton.py     # Gera lista de faltantes
2. python scripts/extrair_faltantes_arton.py        # Executa todas as estratégias
3. python scripts/varredura_completa_monstros.py   # Aplica modelo enriquecido
```

---

## Índice de Referência (criaturas esperadas)

Fonte: `docs/ANALISE_GUIA_DAEMON_MONSTROS_ARTON.md` (seção 4)

Abelha-Gigante, Água-Viva, Ameba-Gigante, Anões, Aparições, Aranhas-Gigantes, Arraia, Asa-Assassina, Asa-Negra, Asflor, Assassino da Savana, Assustador, Avatares, Baleias, Banshee, Basilisco, Beijo-de-Tenebra, Besouros, Brownies, Bruxas, Canários-do-Sono, Caoceronte, Carniceiros, Carrasco de Lena, Cavalos, Centauro, Centopéia-Gigante, Ceratops, Cocatriz, Colosso da Tormenta, Composognato, Corcel do Deserto, Corcel das Trevas, Couatl, Crocodilos, Demônios, Devoradores, Diabo-de-Keenn, Dimmak, Dinonico, Dionys, Dragões, Dríade, Duplo, Elefantes, Elementais, Elfos, Enfermeiras, Entes, Esfinge, Esqueletos, Familiares, Fantasma, Fênix, Feras-Caçus, Fil-Gikin, Fofo, Fogo-Fátuo, Formigas-Hiena, Fungi, Gafanhoto-Tigre, Gambá, Gárgula, Gênios, Ghoul, Gigantes, Gnolls, Goblinóides, Golens, Golfinho, Gondo, Górgon, Grama Carnívora, Grandes Felinos, Grandes Símios, Grifo, Guerreiro da Luz, Halflings, Harpia, Hidra, Hipogrifo, Homens-Escorpião, Homens-Lagarto, Homens-Morcego, Homens-Serpente, Homúnculo, Horror dos Túmulos, Ictiossauro, Incubador, Kaatar-nirav, Kanatur, Katrak, Killbone, Kobolds, Kraken, Leão-de-Keenn, Lesma-Carnívora, Licantropos, Lich, Lobo-das-Cavernas, Mago-Fantasma, Manticora, Mortos-Vivos, Múmia, Naga, Neblina-Fantasma, Neblina-Vampírica, Necrodracos, Nereida Abissal, Ninfa, Observadores, Ogres, Ores, Pantera-do-Vidro, Pássaros Arco-Íris, Pássaros do Caos, Pégaso, Peixe-Couraca, Peixe-Gancho, Peixe-Recife, Planador, Povo-Dinossauro, Povo-Sapo, Predador dos Sonhos, Predador-Toupeira, Protocraco, Pteranodonte, Pteros, Pudim Negro, Quelicerossauros, Quelonte, Quimera, Random, Ratazanas, Serpentes Venenosas, Siba Gigante, Sharks, Shimav, Shinobi, Soldados-Mortos, Sprites, Tahab-krar, Tai-Kanatur, Tasloi, Tatu-Aranha, Tentáculo, Terizinossauro, Tigre-de-Hyninn, Toscos, T-Rex, Triceratops, Trilobitas, Trobos, Trogloditas, Troll, Ursos, Unicórnio, Vampiro, Varano de Krah, Velociraptor, Velocis, entre outros.
