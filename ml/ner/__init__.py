"""
Módulo de NER (Reconhecimento de Entidades) específico para 3D&T.

Componentes principais:
- `patterns.py` – padrões regex e listas de termos (atributos, raças, classes, magias).
- `weak_annotate.py` – gera dados anotados automaticamente (weak supervision) e exporta em formato spaCy v3.
- `model_integration.py` – carrega o modelo spaCy e enriquece os chunks do RAG com metadados de entidades.
"""

