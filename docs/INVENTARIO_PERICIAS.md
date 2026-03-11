# Inventário: Perícias 3D&T

## Visão geral

> Perícias são parte do realismo. Personagens podem ser cientistas, espiões, detetives, médicos... possuem outras habilidades além de lutar.
>
> **11 Perícias**: Animais, Arte, Ciência, Idiomas, Investigação, Máquinas, Medicina, Sobrevivência, Crime, Esporte e Manipulação. Todas custam **2 pontos** cada (completa).
>
> **Especializações**: 3 por 1 ponto (área restrita). Ex.: Animais → Doma, Montaria, Tratamento, Treinamento, Veterinária.

## Livro fonte

| Livro | Conteúdo | Páginas |
|-------|----------|---------|
| **Manual 3D&T Turbinado / Manual do Aventureiro** | LISTA DE PERÍCIAS, Especializações | ~51+ |

## Estrutura por Perícia

| Campo | Descrição |
|-------|-----------|
| `nome` | Animais, Arte, Ciência, etc. |
| `custo` | 2 pontos (completa) |
| `descricao` | Texto explicativo |
| `especializacoes` | Lista (Doma, Montaria, Tratamento...) |
| `livro` | PDF de origem |
| `pagina` | Página no livro |

## As 11 Perícias (índice fixo)

1. Animais
2. Arte
3. Ciência
4. Idiomas
5. Investigação
6. Máquinas
7. Medicina
8. Sobrevivência
9. Crime
10. Esporte
11. Manipulação

## Scripts

| Script | Função |
|--------|--------|
| `scripts/extrair_pericias_agressivo.py` | Carrega Perícias (canônico ou PDF) |
| `scripts/reindexar_pericias.py` | Chroma para RAG |

## Pipeline

```bash
python scripts/extrair_pericias_agressivo.py
python scripts/reindexar_pericias.py
```

## Arquivos gerados

| Arquivo | Descrição |
|---------|-----------|
| `data/processed/pericias/pericias_canonico.json` | Descrições canônicas (Manual Turbinado) |
| `data/processed/pericias/pericias_extraidas.json` | Perícias com descrição e especializações |
| `data/processed/pericias/pericias_por_grupo.txt` | Relatório |

**Nota:** A extração do PDF é complexa (estrutura varia entre livros). O script usa `pericias_canonico.json` como fonte primária quando disponível.
