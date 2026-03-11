# Extrair dados dos livros 3D&T (PDFs)

O projeto busca informações nos PDFs configurados em `SOURCE_PDF_DIR` (`.env`).

## 1. Configurar o caminho dos PDFs

No `.env`:
```
SOURCE_PDF_DIR="C:\\Users\\Desktop\\Downloads\\3det\\usoldle"
```

Ajuste para o nome correto da sua pasta (`usoldle` ou `usoIdle`).

## 2. Livros usados

| Livro | Uso |
|-------|-----|
| **Manual 3D&T Turbinado** | Raças, vantagens base, regras |
| **Manual da Magia** | Vantagens/desvantagens mágicas, raças (Brownie, Meio-Gênio, Sátiro, Dragonete, Grig, Pixie) |
| **Manual dos Monstros** | Licantropo (raça 0 pts), monstros |
| **Bestiário Alpha** | Monstros adicionais |
| **Guia de Monstros (Tormenta/Daemon)** | Monstros de Arton |

## 3. Scripts de extração

### Vantagens e Desvantagens (Manual da Magia)
```bash
# 1. Extrair índice do PDF
python scripts/extrair_indice_vantagens_magia.py

# 2. Extrair blocos completos
python scripts/extrair_vantagens_magia_agressivo.py

# 3. Categorizar
python scripts/categorizar_vantagens.py
```

Saída: `data/processed/vantagens_desvantagens/vantagens_magia_categorizadas.json`

### Magias
```bash
python scripts/extrair_magias_agressivo.py
```

### Itens Mágicos
```bash
python scripts/extrair_itens_magicos_agressivo.py
```

### Monstros
```bash
python scripts/extrair_monstros_agressivo.py
```

### Perícias
```bash
python scripts/extrair_pericias_agressivo.py
```

## 4. Sincronizar com o frontend

Após extrair, os dados em `data/processed/` precisam ser copiados ou convertidos para o frontend:

- **Vantagens**: `frontend/src/data/vantagens_turbinado.json` (editar manualmente ou via script)
- **Monstros**: `scripts/sync_monstros_frontend.py`

## 5. Dependências

- **PyMuPDF** (`pip install pymupdf`) ou **pdfplumber** (`pip install pdfplumber`) para extrair texto dos PDFs
