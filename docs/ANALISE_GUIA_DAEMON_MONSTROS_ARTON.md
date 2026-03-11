# Análise: Guia de Monstros de Arton (Daemon Editora)

Livro de bestiário para **3D&T / Tormenta**, publicado pela **Daemon Editora** (2001–2006). 130 páginas, **mais de 300 espécies** de monstros e criaturas para Arton.

---

## 1. Do que se trata

O **Guia de Monstros de Arton** é um bestiário clássico que:

- Cobre criaturas de **fantasia medieval** no cenário Arton
- Usa o sistema **3D&T** (F, H, R, A, PdF) com atributos adicionais (CON, FR, DEX, AG, INT, WLL, CAR, PE)
- Inclui ataques, habilidades especiais e descrições de combate
- Complementa o Bestiário Alpha e o Manual dos Monstros

---

## 2. Estrutura das entradas

Cada monstro segue um formato próprio da Daemon:

1. **Nome** (ex.: Abelha-Gigante, Água-Viva)
2. **Citação** (frase de personagem)
3. **Atributos:** CON, FR, DEX, AG, INT, WLL, CAR, PE
4. **Ataques:** nome, chance, dano (ex.: Mordida 40/0 dano 1d6, Ferrão 80/0 dano 1d3+Veneno)
5. **Stats 3D&T:** `F2-3, H 1, R2, A 3, PdF0, Levitação`
6. **Descrição** (aparência, comportamento, combate)

---

## 3. Extrator dedicado (implementado)

**Código específico para este livro:** `src/ingestion/daemon_extractor_dedicado.py` + `src/ingestion/extrair_habilidades_daemon.py`

A **descrição neste livro é parte crucial** para tabulação e documentação. O extrator:

- Captura o **bloco completo** de cada monstro (nome → citação → CON/#Ataques → F/H/R/A/PdF → descrição)
- Corta no **nome do próximo monstro** para evitar mistura de entradas (ex.: ataques do DRAGÃO DO VÁCUO no bloco do DRAGÃO MARINHO)
- Aplica **normalização OCR** para ataques (ex.: `ivford.ida` → Mordida, `c:auda` → Cauda)
- Extrai habilidades de combate (Mordida, Garras, Cauda, Imunidades, etc.) do bloco completo

Foi criado `scripts/extrair_daemon_guia.py`, que:

1. Localiza o PDF do Guia Daemon em SOURCE_PDF_DIR
2. Busca o padrão `F X, H X, R X, A X, PdF X` (com variações de OCR)
3. **Padrões expandidos:** aceita "A" renderizado como `1\`, `r\`, `J\` (artefato de PDF); H com múltiplos valores `H0/1/3/4` (usa o primeiro)
4. Associa cada bloco ao nome do monstro na linha anterior
5. Converte para o formato unificado (caracteristicas F/H/R/A/PdF, descricao, etc.)
6. Salva em `data/processed/monstros/monstros_daemon_extraidos.json`
7. **Mescla automaticamente** ao `monstros_extraidos.json` (ecossistema principal)

**Executar:** `python scripts/extrair_daemon_guia.py` — extrai ~154 monstros do Guia Daemon.

### Fallback quando stats estão garbled (OCR)

- **`src/ingestion/daemon_stats_fallback.py`** — quando o bloco F/H/R/A/PdF está ilegível:
  1. **Parser da descrição** — extrai F, H, R, A, PdF mencionados no texto (ex.: "têm H3", "A4")
  2. **Cross-reference com bestiário** — se o monstro existe no Bestiário Alpha, usa esses stats
  3. **Mescla** — prioridade: bloco > descrição > bestiário (apenas campos faltantes)
- Ignora CON, FR, DEX, INT, WLL, CAR, PER — só converte F/H/R/A/PdF.

---

## 4. Índice (exemplos)

Abelha-Gigante, Água-Viva, Ameba-Gigante, Anões, Aparições, Aranhas-Gigantes, Arraia, Asa-Assassina, Asa-Negra, Asflor, Assassino da Savana, Assustador, Avatares, Baleias, Banshee, Basilisco, Beijo-de-Tenebra, Besouros, Brownies, Bruxas, Canários-do-Sono, Caoceronte, Carniceiros, Carrasco de Lena, Cavalos, Centauro, Centopéia-Gigante, Ceratops, Cocatriz, Colosso da Tormenta, Composognato, Corcel do Deserto, Corcel das Trevas, Couatl, Crocodilos, Demônios, Devoradores, Diabo-de-Keenn, Dimmak, Dinonico, Dionys, Dragões, Dríade, Duplo, Elefantes, Elementais, Elfos, Enfermeiras, Entes, Esfinge, Esqueletos, Familiares, Fantasma, Fênix, Feras-Caçus, Fil-Gikin, Fofo, Fogo-Fátuo, Formigas-Hiena, Fungi, Gafanhoto-Tigre, Gambá, Gárgula, Gênios, Ghoul, Gigantes, Gnolls, Goblinóides, Golens, Golfinho, Gondo, Górgon, Grama Carnívora, Grandes Felinos, Grandes Símios, Grifo, Guerreiro da Luz, Halflings, Harpia, Hidra, Hipogrifo, Homens-Escorpião, Homens-Lagarto, Homens-Morcego, Homens-Serpente, Homúnculo, Horror dos Túmulos, Ictiossauro, Incubador, Kaatar-nirav, Kanatur, Katrak, Killbone, Kobolds, Kraken, Leão-de-Keenn, Lesma-Carnívora, Licantropos, Lich, Lobo-das-Cavernas, Mago-Fantasma, Manticora, Mortos-Vivos, Múmia, Naga, Neblina-Fantasma, Neblina-Vampírica, Necrodracos, Nereida Abissal, Ninfa, Observadores, Ogres, Ores, Pantera-do-Vidro, Pássaros Arco-Íris, Pássaros do Caos, Pégaso, Peixe-Couraca, Peixe-Gancho, Peixe-Recife, Planador, Povo-Dinossauro, Povo-Sapo, Predador dos Sonhos, Predador-Toupeira, Protocraco, Pteranodonte, Pteros, Pudim Negro, Quelicerossauros, Quelonte, Quimera, Random, Ratazanas, Serpentes Venenosas, Siba Gigante, Sharks, Shimav, Shinobi, Soldados-Mortos, Sprites, Tahab-krar, Tai-Kanatur, Tasloi, Tatu-Aranha, Tentáculo, Terizinossauro, Tigre-de-Hyninn, Toscos, T-Rex, Triceratops, Trilobitas, Trobos, Trogloditas, Troll, Ursos, Unicórnio, Vampiro, Varano de Krah, Velociraptor, Velocis, entre outros.

---

## 5. Uso no projeto

| Ação | Status |
|------|--------|
| PDF em SOURCE_PDF_DIR | ✅ Detectado e processado |
| Extração de monstros | ❌ Formato incompatível com extrator atual |
| Ingestão RAG (chunks) | ⏳ Depende do pipeline de indexação |

O livro está disponível para consulta manual e pode ser incluído no pipeline de ingestão de PDFs para RAG (busca semântica), mesmo que a extração estruturada de monstros exija adaptação do script.
