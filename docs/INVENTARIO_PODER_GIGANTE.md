# Inventário: Poder de Gigante e Características Sobre-Heróicas

## Avaliação das informações

O Poder de Gigante é uma **escala de poder** para personagens muito poderosos ou de tamanho gigante. A extração deve preservar:

1. **Fórmula de conversão** (F, A, PdF, PV × 10; H, R, PM inalterados)
2. **Quando usar** (apenas Mestre autoriza; sem Vantagem ou compra)
3. **Tamanho gigante** (≥50m; normal vs gigante; sem intermediários)
4. **Esquiva vs gigante** (personagem normal recebe H+3 em Esquiva)
5. **Custos cumulativos** (6→+3, 7→+5, 8→+7, etc.; até 10 = 40 pts)
6. **Formas de obter** (Aventuras Cósmicas, Condições Especiais, Máquinas)

## Categorização proposta

| Categoria | Conteúdo | Exemplos |
|-----------|----------|----------|
| **escala_poder** | Conceito, limites das regras normais | 0=humano normal, 1=máx humano, >1=super |
| **poder_gigante** | Definição, atributos afetados | F, A, PdF, PV ×10 |
| **quando_usar** | Autorização, cautela do Mestre | Sem Vantagem, sem compra |
| **tamanho_gigante** | Definição, combate gigante vs normal | ≥50m, Esquiva +H+3 |
| **custos_caracteristicas** | Custos sobre-heróicos (6 a 10+) | 5→5pts, 6→8pts, 7→13pts... |
| **formas_obter** | Aventuras Cósmicas, Condições, Máquinas | |

## Organização dos dados

Integrado ao inventário de **Regras de Combate** (`regras_combate_canonico.json`), pois estende as regras de combate para escalas cósmicas.

### Blocos a extrair

| ID | Título | Categoria |
|----|--------|-----------|
| escala_poder | Escala de Poder (0, 1, >1) | escala_poder |
| poder_gigante | Poder de Gigante (definição) | poder_gigante |
| poder_gigante_atributos | Atributos afetados pelo Poder de Gigante | poder_gigante |
| quando_usar_pg | Quando Usar Poder de Gigante | quando_usar |
| tamanho_gigante | Tamanho Gigante | tamanho_gigante |
| esquiva_vs_gigante | Esquiva contra ataque de gigante | tamanho_gigante |
| custos_caracteristicas | Custos de Características Sobre-Heróicas (tabela 5–30) | custos_caracteristicas |
| efeitos_caracteristicas | Efeitos de Características (≥7 = efeito de Vantagem) | custos_caracteristicas |
| efeitos_forca | Efeitos de Força — capacidade em toneladas | custos_caracteristicas |
| formas_obter_pg | Formas de Obter Poder de Gigante | formas_obter |

## Livro fonte

| Livro | Capítulo | Páginas |
|-------|----------|---------|
| **Manual 3D&T Turbinado Digital** | Poder de Gigante / Escalas Cósmicas | ~58+ |

## Pipeline

Usa o mesmo pipeline das Regras de Combate:

```bash
python scripts/extrair_regras_combate.py
python scripts/reindexar_regras_combate.py
```
