# Livros e quantidade de monstros

Tabela de todos os livros que contribuem monstros para o ecossistema (`monstros_extraidos.json`).

| Livro | Monstros |
|-------|----------|
| 3DT Alpha Bestiário Alpha (Biblioteca Élfica) | 211 |
| 3DT Alpha Manual dos Dragões (Biblioteca Élfica) | 141 |
| Tormenta Daemon Guia de Monstros de Arton (Biblioteca Élfica) | 154 |
| 3DT Alpha Manual da Magia (Biblioteca Élfica) | 27 |
| 3DT Alpha Manual (Biblioteca Élfica) | 7 |
| 3DT Alpha Manual Revisado (Biblioteca Élfica) | 7 |
| 3DT Manual da Magia (Biblioteca Élfica) | 5 |
| 3DT Alpha Tormenta Alpha | 4 |
| 3D&T Manual Turbinado Digital | 2 |
| **Total** | **558** |

---

## Scripts de extração

- **`scripts/extrair_monstros_agressivo.py`** — Extrai de PDFs com formato `Nome: F X, H X, R X, A X, PdF X` (Bestiário Alpha, Manual dos Dragões, etc.)
- **`scripts/extrair_daemon_guia.py`** — Extrai do Guia de Monstros de Arton (formato Daemon) e mescla ao ecossistema

**Ordem recomendada:** rodar `extrair_monstros_agressivo.py` primeiro, depois `extrair_daemon_guia.py`.
