# Pipeline de descoberta de conhecimento 3D&T

Extração de entidades, grafo de relações, taxonomia e propriedades **diretamente dos PDFs**, sem conhecimento prévio.

## Ordem de execução

1. **Entidades** – `python scripts/extract_entities.py`  
   - Chunks de `data/processed/` ou ingestão dos PDFs  
   - Padrões: CAIXA ALTA, Title Case, "O X é um Y", "• Nome", seção → tipo  
   - Saída: `data/entities/extracted_entities.json`

2. **Propriedades** – `python scripts/infer_properties.py`  
   - Custa X PM, duração, alcance, PV, F/H/R/A, imunidades, etc.  
   - Saída: `data/properties/entity_properties.json`

3. **Grafo** – `python scripts/build_knowledge_graph.py`  
   - Relações: is_a, cost_pm, requires, school, element, weakness, effect  
   - Saída: `data/knowledge_graph/relations.json`

4. **Taxonomia** – `python scripts/discover_taxonomy.py`  
   - TF-IDF + K-Means nos contexts (requer `scikit-learn`)  
   - Saída: `data/taxonomy/auto_taxonomy.json`

5. **Pipeline completo** – `python scripts/discover_knowledge.py --full`

## Uso no RAG

- **Query expansion**: `src/retrieval/graph_expansion.py` – expande "Fênix" com relações e cluster  
- **Base de conhecimento**: `src/knowledge/base.py` – carrega entidades, relações, taxonomia, propriedades  
- **Hybrid retriever**: `use_graph_expansion=True` em `hybrid_retrieve()` para buscar por termos do grafo  

## NER treinado no corpus

- `python scripts/prepare_ner_data.py` – gera `data/ner/training_data.jsonl`  
- `python scripts/train_corpus_ner.py` – treina modelo em `models/ner_3det_corpus`  
- `python scripts/test_ner.py "Invocação da Fênix"`

## Validação

- `python scripts/validate_entities.py` – conferir/corrigir tipos das entidades  
- `python scripts/test_graph_expansion.py "Fênix"` – ver expansões do grafo  
