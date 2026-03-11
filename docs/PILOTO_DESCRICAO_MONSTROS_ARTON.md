# Piloto: Descrição Enriquecida — 5 Monstros do Livro de Arton

## Objetivo

Avaliar a expansão de campos estruturados na descrição dos monstros, extraídos do texto do Guia de Monstros de Arton (Daemon).

## Campos adicionados

| Campo | Descrição |
|-------|-----------|
| **comportamento** | Comportamento geral da criatura |
| **altura_tamanho** | Dimensões físicas |
| **peso** | Peso aproximado |
| **habitat** | Onde vive |
| **comportamento_dia_noite** | Atividade diurna ou noturna |
| **comportamento_combate** | Táticas e estratégias de combate |
| **habilidades_extra** | Habilidades além das mecânicas (habilidades) |

## Monstros do piloto

1. **Abelha-Gigante** — inseto tamanho felino, colmeia, veneno
2. **Ameba-Gigante** — 10 m diâmetro, 4 pseudópodes, vulnerável a fogo
3. **Asa Negra** — águia, montanhas, falcoaria
4. **Asfixor** — lesma 5 m, masmorras, sufocação
5. **Gondo** — fera 3 m, 300 kg, noturno, invisível

## Execução

```bash
# 1. Extrair monstros do Guia Daemon (se necessário)
python scripts/extrair_daemon_guia.py

# 2. Aplicar enriquecimento (piloto)
python scripts/enriquecer_descricao_monstros.py
```

**Importante:** O enriquecimento deve ser executado **após** a extração do Guia Daemon, pois ele substitui os monstros no ecossistema.

## Avaliação para expansão

Para expandir ao livro todo:

1. **Extração automática:** Criar parser de regex/heurísticas baseado nos padrões do Guia Daemon (ex.: "mede X m", "pesa Y kg", "habita Z", "durante o dia/noite").
2. **Integração no pipeline:** Incluir `enriquecer_descricao_monstros.py` no fluxo de `extrair_daemon_guia.py` ou rodar em sequência.
3. **Cobertura:** Os 154 monstros do Guia Daemon têm descrições variadas; alguns campos podem ficar vazios ("Não especificado").
4. **Outros livros:** O Bestiário Alpha e Manual dos Monstros têm formato diferente; exigir adaptação do parser.

## Arquivos

- `src/ingestion/enriquecer_descricao_monstro.py` — lógica e dados do piloto
- `scripts/enriquecer_descricao_monstros.py` — script de execução
- `data/processed/monstros/monstros_extraidos.json` — ecossistema (5 monstros enriquecidos)
- `data/processed/monstros/schema_monstros.json` — schema atualizado
