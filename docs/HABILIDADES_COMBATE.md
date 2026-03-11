# Habilidades de Combate — Extração da Descrição

Dois parsers:

- **`src/ingestion/extrair_habilidades_combate.py`** — genérico, para todos os livros
- **`src/ingestion/extrair_habilidades_daemon.py`** — **dedicado ao Guia Daemon**, usa bloco completo (ataques + descrição). A descrição neste livro é parte crucial para tabulação; o extrator corta no nome do próximo monstro e aplica normalização OCR (ex.: `ivford.ida` → Mordida, `c:auda` → Cauda).

---

## Schema

Cada habilidade extraída tem:

```json
{
  "nome": "Veneno",
  "detalhes": "10d6 dano, 3 PVs por turno",
  "tipo": "veneno"
}
```

**Tipos:** `veneno`, `teste`, `imunidade`, `restricao`, `efeito_especial`, `ataque`, `vulnerabilidade`

---

## Padrões extraídos

| Tipo | Exemplos |
|------|----------|
| **Veneno** | `veneno(10d6)`, `3 PVs por turno`, `perde 3 PVs por turno (10d6)` |
| **Teste para atacar** | `Oponentes precisam passar em Teste de WILL antes de atacar` |
| **Teste para agredir** | `Mulheres devem ter sucesso em Teste de R cada vez que tenta agredir` |
| **Beleza atordoante** | `Falha em R: efeito da Magia Coma` |
| **Voz Melodiosa** | `Voz Melodiosa (ver abaixo)` |
| **Imune** | `Construtos, Mortos-Vivos são imunes` |
| **Incapaz de lutar** | `Totalmente incapaz de lutar`, `Nunca atacará` |
| **Definhar** | `Morre em 1 hora fora do ambiente natural` |
| **Constrição** | `Constrição: dano de 1d6+3 por rodada` |
| **Invulnerabilidade** | `Invulnerabilidade a: Contusão, Corte, Perfuração` |
| **Vulnerabilidade** | `Vulnerabilidade a: Calor/Fogo` |

---

## Uso

- **Extração automática:** Os scripts `extrair_monstros_agressivo.py` e `extrair_daemon_guia.py` já adicionam `habilidades_combate` aos monstros.
- **Enriquecimento em lote:** `python scripts/enriquecer_habilidades_combate.py` — processa todos os monstros em `monstros_extraidos.json`.

---

## Campo no monstro

```json
{
  "nome": "Serpente Marinha",
  "caracteristicas": { "F": "0", "H": "1-3", "R": "1", "A": "0", "PdF": "0" },
  "habilidades": [],
  "habilidades_combate": [
    { "nome": "Veneno", "detalhes": "10d6 dano, 3 PVs por turno", "tipo": "veneno" }
  ],
  "descricao": "..."
}
```
