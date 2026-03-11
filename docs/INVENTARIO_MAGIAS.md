# Inventário do Livro de Magias 3D&T Alpha

## Resumo (Extrator Agressivo)

| Métrica | Valor |
|---------|-------|
| **Nomes no índice** | 296 |
| **Magias com descrição** | **289** (97,6%) |
| **Magias não encontradas** | 7 |

```bash
python scripts/extrair_magias_agressivo.py
```

### Fontes por livro (magias extraídas)

| Livro | Magias |
|-------|--------|
| Manual da Magia Alpha | 142 |
| Manual Revisado | 111 |
| Manual da Magia (3dt-manual) | 12 |
| Manual Revisado Ampliado e Turbinado | 6 |
| Manual dos Dragões | 17 |
| Manual 3D&T Turbinado Digital | 0 |
| Manual dos Monstros | 1 |


### Extrator dual (PyMuPDF + pdfplumber)

O Manual Revisado Ampliado usa layout/OCR diferente. O extrator:
- Usa **pdfplumber** para esse PDF (melhor extração de texto)
- Aceita **Exigências** além de Escola
- Tolerância a typos OCR (Exlgênclas, Custa, Culto, etc.)
- Busca múltiplas ocorrências do nome e escolhe a com maior confiança

### Scripts auxiliares

- `python scripts/check_descricoes.py` – Gera `magias_com_fonte.txt` (magia \| livro)
- `python scripts/listar_nao_encontradas_com_fonte.py` – Gera `magias_nao_encontradas_com_fonte.txt`
- `python scripts/reindexar_magias.py` – Adiciona magias ao Chroma para busca

### Pipeline em 3 Camadas (alternativo)

1. **Camada 1 – Índice**: Extrai os ~300 nomes do PDF (págs. 29–32) → `data/processed/indice_magias_3dt.txt`
2. **Camada 2 – Delimitador**: Extrai blocos completos (Nome + Escola + Custo + Alcance + Duração)
3. **Camada 3 – Validação**: Cruzamento índice × extração → `data/processed/magias/magias_3dt_completo.json`

```bash
python scripts/extrair_todas_magias_3dt.py
```

## Fontes (PDFs em SOURCE_PDF_DIR)

- `3dt-alpha-manual-da-magia-biblioteca-elfica.pdf`
- `3dt-alpha-manual-revisado-biblioteca-elfica.pdf`
- `3dt-manual-da-magia-biblioteca-elfica.pdf`
- `3dt-manual-revisado-ampliado-e-turbinado-biblioteca-elfica.pdf` (6 extraídas com extrator dual pdfplumber + padrões Exigências)
- `3dt-alpha-manual-dos-dragoes-biblioteca-elfica.pdf`
- `3dt-alpha-manual-dos-monstros.pdf`
- `Cópia de 3D&T - Manual 3D&T Turbinado Digital .pdf`
- (+ Bestiário, Manual do Aventureiro, Arcano preview)

## Lista das 300 Magias (índice)

- ○ **Abençoar Arma** (MM, pg. 07)
- ○ **Abençoar Água** (MM, pg. 07)
- ○ **Acalmar Animais** (MM, pg. 07)
- ○ **Acordar** (M3D&T, pg. 81)
- ✓ **Aderência** (MM, pg. 07)
- ✓ **Afetar Fogueiras** (MM, pg. 07)
- ✓ **Agilidade** (MM, pg. 07)
- ○ **Alarme!** (MM, pg. 08)
- ✓ **Ação Aleatória** (MM, pg. 07)
- ○ **Barreira de Lâminas** (MM, pg. 10)
- ○ **Barreira de Vento** (M3D&T, pg. 84)
- ○ **Barreira Mística** (M3D&T, pg. 84)
- ○ **Bola de Fogo** (M3D&T, pg. 84)
- ✓ **Bola de Fogo de Questor** (MM, pg. 11)
- ○ **Bola de Lama** (M3D&T, pg. 84)
- ○ **Bola de Vento** (M3D&T, pg. 85)
- ○ **Bolas Explosivas** (M3D&T, pg. 85)
- ○ **Bênção** (MM, pg. 11)
- ✓ **Corpo de Ferro** (MM, pg. 14)
- ✓ **Corpo Elemental** (MM, pg. 89)
- ○ **Criar Pântano** (M3D&T, pg. 89)
- ○ **Criar Água** (MM, pg. 16)
- ○ **Criação de Dragão-Esqueleto** (MM, pg. 15)
- ○ **Criação de Dragão-Zumbi** (MM, pg. 15)
- ✓ **Criação de Frutas e Vegetais** (MM, pg. 15)
- ✓ **Criação de Mortos-Vivos** (MM, pg. 15)
- ○ **Crânio Voador de Vladislav, O** (M3D&T, pg. 89)
- ○ **Esconjuro de Mortos-Vivos** (M3D&T, pg. 94)
- ○ **Escudo da Fé** (MM, pg. 17)
- ✓ **Escudo de Mana** (MM, pg. 17)
- ✓ **Escudo Elemental** (MM, pg. 17)
- ○ **Escuridão** (M3D&T, pg. 94)
- ○ **Explosão** (M3D&T, pg. 94)
- ○ **Fada Servil** (M3D&T, pg. 94)
- ○ **Falar com Animais** (MM, pg. 17)
- ○ **Falar com Plantas** (MM, pg. 17)
- ○ **Invisibilidade** (M3D&T, pg. 98)
- ○ **Invisibilidade Superior** (M3D&T, pg. 98)
- ○ **Invocação da Fênix** (MM, pg. 20)
- ○ **Invocação de Aliado Extra-Planar** (MM, pg. 20)
- ○ **Invocação do Dragão** (M3D&T, pg. 98)
- ○ **Invocação do Elemental** (M3D&T, pg. 99)
- ○ **Invocação do Elemental Superior** (M3D&T, pg. 99)
- ○ **Invocação do Elemental Supremo** (M3D&T, pg. 99)
- ○ **Invulnerabilidade** (M3D&T, pg. 100)
- ○ **Nevoeiro de Hyninn** (M3D&T, pg. 105)
- ○ **Nevoeiro de Sszzaas** (M3D&T, pg. 105)
- ○ **Nobre Montaria** (M3D&T, pg. 105)
- ○ **Nulificação Total de Talude, A** (M3D&T, pg. 105)
- ✓ **Observar** (MM, pg. 23)
- ○ **Olho de Kilrogg** (MM, pg. 23)
- ○ **Olhos de Azshara** (MM, pg. 23)
- ○ **Onda de Choque** (MM, pg. 24)
- ○ **Onda Explosiva** (MM, pg. 24)
- ○ **Porta Dimensional** (M3D&T, pg. 108)
- ○ **Recuperação Natural** (M3D&T, pg. 109)
- ○ **Reflexos** (M3D&T, pg. 109)
- ○ **Regeneração** (MM, pg. 26)
- ○ **Resistência de Helena, A** (M3D&T, pg. 110)
- ○ **Ressurreição** (M3D&T, pg. 110)
- ○ **Retribuição de Wynna, A** (M3D&T, pg. 110)
- ○ **Rocha Cadente de Vectorius, A** (M3D&T, pg. 110)
- ○ **Roubo de Magia** (M3D&T, pg. 110)
- ○ **Roubo de Vida** (M3D&T, pg. 110)
- ○ **Sopro Atordoante** (MD, pg. 66)
- ○ **Sopro Brilhante** (MD, pg. 66)
- ✓ **Surdez** (MM, pg. 27)
- ○ **Teia de Megalokk** (M3D&T, pg. 112)
- ○ **Teleportação** (M3D&T, pg. 112)
- ○ **Teleportação Aprimorada de Vectorius, A** (M3D&T, pg. 112)
- ○ **Teleportação Planar** (M3D&T, pg. 112)
- ○ **Transformação em Orc** (M3D&T, pg. 114)
- ○ **Transformação em Outro** (M3D&T, pg. 115)
- ○ **Transformação em Pudim de Ameixa** (M3D&T, pg. 115)
- ○ **Transporte** (M3D&T, pg. 115)
- ✓ **Transporte Etéreo** (MM, pg. 28)
- ○ **Tropas de Ragnar** (M3D&T, pg. 115)
- ✓ **Trovão** (MM, pg. 28)
- ✓ **Trovão em Cadeia** (MM, pg. 29)

## Magias não encontradas (7)

- Brilho de Espírito
- Chicote das Trevas
- Comando de Khalmyr
- Feras de Tenebra
- Nevoeiro de Sszzaas
- Pequenos Desejos
- Ressurreição

## Arquivos gerados

- `data/processed/magias/magias_extraidas_agressivo.json` – 283 magias com descrição, escola, custo, alcance, duração, livro
- `data/processed/magias/magias_com_fonte.txt` – Lista magia \| fonte
- `data/processed/magias/magias_nao_encontradas.txt` – 13 magias sem descrição
- `data/processed/magias/magias_nao_encontradas_com_fonte.txt` – Lista magia \| fonte (índice)