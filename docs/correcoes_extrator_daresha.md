# Correções no extrator — Daresha e erros similares

> Alterações no código para evitar os mesmos erros (nome errado, boundary, título da seção).

---

## 1. MANUAL_PATTERN — Nome, Variante, Escala

**Problema:** O livro usa "Daresha, Guerreira Deicida, 58S" mas o padrão esperava "Nome, NúmeroEscala" (ex.: "Harpia, 8N"). O extrator não reconhecia o formato com variante.

**Correção:** `src/ingestion/extrair_monstros_manual_format.py`
- Padrão atualizado para aceitar `Nome, Variante, NúmeroEscala` (variante opcional)
- Ex.: "Daresha, Guerreira Deicida, 58S" → nome = "Daresha, Guerreira Deicida"

---

## 2. Título da seção

**Problema:** O livro tem "Daresha, a Caçadora de Keenn" como título da seção e "Daresha, Guerreira Deicida, 58S" no stat block. O extrator usava só o stat block.

**Correção:** `_extrair_titulo_secao()` em `extrair_monstros_manual_format.py`
- Analisa o texto antes do stat block
- Procura linhas no formato "NomeBase, a/o/de ..." (título típico do Manual)
- Se encontrar, usa o título como nome em vez do stat block

---

## 3. NOME_CANONICO — Mapeamento para PILOTO_EXTRA

**Problema:** A extração antiga gerava "Guerreira Deicida" (extrator agressivo) e o PILOTO_EXTRA usa "Daresha, a Caçadora de Keenn". Não havia ligação entre eles.

**Correção:** `scripts/extrair_monstros_modelo_enriquecido.py`
- `NOME_CANONICO`: mapeia nomes extraídos para nomes canônicos
- "Guerreira Deicida" → "Daresha, a Caçadora de Keenn"
- "Daresha, Guerreira Deicida" → "Daresha, a Caçadora de Keenn"
- Ao aplicar PILOTO_EXTRA, usa o nome canônico e evita duplicatas na injeção

---

## 4. Injeção sem duplicatas

**Problema:** Monstros só em PILOTO_EXTRA eram injetados mesmo quando um nome extraído já mapeava para o mesmo canônico.

**Correção:** `nomes_ja_cobertos` inclui `NOME_CANONICO.get(n, n)` para todos os nomes extraídos. Assim, "Daresha, a Caçadora de Keenn" não é injetada se "Guerreira Deicida" já foi convertida.

---

## Resumo

| Erro | Correção |
|------|----------|
| Stat "Nome, Variante, Escala" não reconhecido | MANUAL_PATTERN com variante opcional |
| Título da seção ignorado | `_extrair_titulo_secao()` |
| Nome extraído ≠ nome no PILOTO_EXTRA | NOME_CANONICO |
| Duplicata (extraído + injetado) | nomes_ja_cobertos com mapeamento |
