# Roadmap RAG 3D&T

Plano de entregas por semana. Itens marcados com ✅ têm código/scripts prontos; os artefatos são gerados ao rodar os scripts indicados.

| Semana | Tarefa | Entregável | Status |
|--------|--------|------------|--------|
| **1** | Dataset + Fine-tuning embedding | `models/embeddings/3dt_finetuned/` | ✅ Scripts: `generate_embedding_dataset.py` → `finetune_embeddings.py` |
| **1** | Avaliação embedding | `models/embeddings/evaluation_report.json` (MRR +15%) | ✅ Script: `evaluate_embeddings.py` |
| **2** | Dataset reranking | `data/training/rerank_pairs.jsonl` | 🔲 A fazer |
| **2** | Fine-tuning reranker | `models/reranker/3dt_finetuned/` | 🔲 A fazer |
| **3** | Extração de tabelas | `data/tables/extracted_tables.json` | 🔲 A fazer |
| **3** | Layout-aware chunking | Chunks com tabelas preservadas | 🔲 A fazer |
| **4** | CI/CD retraining | `.github/workflows/retrain.yml` | 🔲 A fazer |
| **4** | Monitoring básico | Logs de latência/satisfação | 🔲 A fazer |

---

## Semana 1 (entregue)

- **Dataset de triplas**: `python scripts/generate_embedding_dataset.py` → gera `data/training/train_triples.jsonl`, `val_triples.jsonl`.
- **Fine-tuning**: `python scripts/finetune_embeddings.py` → salva em `models/embeddings/3dt_finetuned/`.
- **Avaliação**: `python scripts/evaluate_embeddings.py` → gera `models/embeddings/evaluation_report.json`; critério de aceite: MRR melhorou ≥ 15% vs baseline.
- **Depois do fine-tuning:** rodar `python scripts/reindex_with_finetuned.py` para o Chroma usar embeddings de 384 dims (MiniLM); caso contrário ocorre erro de dimensão (768 vs 384). Ver `docs/TESTING_EMBEDDINGS.md`.

## Semana 2 (planejado)

- **Dataset reranking**: pares (query, doc_positivo, doc_negativo ou similar) em `data/training/rerank_pairs.jsonl`.
- **Fine-tuning reranker**: modelo cross-encoder fine-tuned para 3D&T em `models/reranker/3dt_finetuned/`.

## Semana 3 (planejado)

- **Extração de tabelas**: pipeline para extrair tabelas dos PDFs → `data/tables/extracted_tables.json`.
- **Layout-aware chunking**: chunking que preserva tabelas (não quebra células/linhas).

## Semana 4 (planejado)

- **CI/CD retraining**: workflow GitHub Actions para re-treino (embeddings e/ou reranker) sob demanda ou agendado.
- **Monitoring**: logs de latência por etapa (retrieve, rerank, LLM) e de satisfaçao (ex.: thumbs up/down).

## CONQUISTA: Nível 4 - Fine-tuning de Embeddings (CONCLUÍDO)
Data: 2026-02-26
- A/B Test: 66.0% de vitórias (meta: 55%)
- Modelo: 3dt_finetuned_v3 (score 0.93, normalizado L2)
- Dataset: v2 com 3.787 triplas (hard negatives aprimorados)
- Status: ✅ CONSOLIDADO, pronto para produção
