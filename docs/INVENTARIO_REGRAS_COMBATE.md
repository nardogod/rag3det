# Inventário: Regras de Combate 3D&T

## Avaliação das informações

As Regras de Combate são **centrais** ao sistema 3D&T. Tudo se encaixa: dados, turno, FA, FD, tipos de dano, vulnerabilidades. A extração deve preservar:

1. **Fórmulas exatas** (FA = H+F+1d, FD = H+A+1d)
2. **Ordem dos passos** (Iniciativa → FA → FD)
3. **Exceções** (Esquiva antes do Passo 3, Aceleração +1, Teleporte +2)
4. **Regras do Mestre** (inventar regras, modificar à vontade)

## Categorização proposta

| Categoria | Conteúdo | Exemplos |
|-----------|----------|----------|
| **regras_gerais** | Dados, turno, testes, papel do Mestre | d6, 3d, 1d+3, turno = uma ação |
| **turno_combate** | Passos do combate | Iniciativa, FA, FD, Esquiva |
| **tipos_dano** | Dano personalizado, vulnerabilidades | Fogo, Gelo, Vulnerabilidade, Resistência |
| **formulas** | Fórmulas canônicas | FA corpo-a-corpo, FA distância, FD |

## Organização dos dados

### Estrutura por bloco

```json
{
  "id": "turno_combate_passo1",
  "categoria": "turno_combate",
  "titulo": "Passo 1 - Iniciativa",
  "formula": "H + 1d",
  "modificadores": ["+1 Aceleração", "+2 Teleporte (não cumulativos)"],
  "descricao": "Cada combatente rola um dado e acrescenta à Habilidade...",
  "livro": "Manual 3D&T Turbinado",
  "pagina": 57
}
```

### Blocos a extrair (índice)

| ID | Título | Página |
|----|--------|--------|
| inventar_regras | Inventar Regras | 57 |
| dados | Dados (d6, 3d, 1d+3) | 57 |
| turno_rodada | Turno ou Rodada | 57 |
| testes | Testes | 57 |
| classe_dificuldade | Classe de Dificuldade (CD) | 57 |
| turno_combate | Turno de Combate (visão geral) | 57+ |
| passo_iniciativa | Passo 1 - Iniciativa | 57+ |
| passo_fa | Passo 2 - Força de Ataque | 57+ |
| passo_fd | Passo 3 - Força de Defesa | 57+ |
| esquiva | Esquiva | 57+ |
| tipos_dano | Tipos de Dano | 57+ |
| vulnerabilidade | Vulnerabilidade | 57+ |
| resistencia | Resistência | 57+ |
| invulnerabilidade | Invulnerabilidade | 57+ |
| escala_poder | Escala de Poder (0, 1, >1) | 58 |
| poder_gigante | Poder de Gigante | 58 |
| poder_gigante_atributos | Atributos no Poder de Gigante | 58 |
| quando_usar_pg | Quando Usar Poder de Gigante | 58 |
| tamanho_gigante | Tamanho Gigante | 58 |
| esquiva_vs_gigante | Esquiva vs gigante | 58 |
| custos_caracteristicas | Custos Sobre-Heróicos (tabela 5–30) | 121 |
| efeitos_caracteristicas | Efeitos de Características (A6=Deflexão) | 121 |
| efeitos_forca | Efeitos de Força (toneladas) | 121 |
| formas_obter_pg | Formas de Obter Poder de Gigante | 58 |

Ver também: [INVENTARIO_PODER_GIGANTE.md](INVENTARIO_PODER_GIGANTE.md), [INVENTARIO_PERSONAGEM.md](INVENTARIO_PERSONAGEM.md) (origem de F, H, A, PdF)

## Livro fonte

| Livro | Capítulo | Páginas |
|-------|----------|---------|
| **Manual 3D&T Turbinado Digital** | Regras e Combate | ~57+ |

## Scripts

| Script | Função |
|--------|--------|
| `scripts/extrair_regras_combate.py` | Carrega regras (canônico) |
| `scripts/reindexar_regras_combate.py` | Chroma para RAG |

## Pipeline

```bash
python scripts/extrair_regras_combate.py
python scripts/reindexar_regras_combate.py
```

## Arquivos gerados

| Arquivo | Descrição |
|---------|-----------|
| `data/processed/regras_combate/regras_combate_canonico.json` | Regras estruturadas |
| `data/processed/regras_combate/regras_combate_consolidado.json` | Saída do extrator |
