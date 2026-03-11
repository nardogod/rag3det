"""
Reindexa magias com metadados enriquecidos para busca por nome exato.
Adiciona chunks magia_nome e magia_completa ao vectorstore.
Executar: python scripts/reindexar_magias.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.ingestion.entity_extractor import extrair_magias_de_texto
from src.utils.livro_normalizado import normalizar_livro
from src.vectorstore.chroma_store import get_vectorstore


def carregar_chunks() -> list[dict]:
    """Carrega todos os chunks de chunks.json."""
    path = Path("data/processed/chunks.json")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("chunks", data.get("documents", [data]))
    return [i for i in items if isinstance(i, dict)]


def reconstruir_texto_por_pagina(chunks: list[dict], source: str) -> str:
    """Concatena chunks de um source ordenados por página (evita magias cortadas)."""
    filtrados = [c for c in chunks if (c.get("metadata") or {}).get("source") == source]
    filtrados.sort(key=lambda c: int((c.get("metadata") or {}).get("page", 0) or 0))
    return "\n\n".join(c.get("content") or c.get("page_content") or "" for c in filtrados if (c.get("content") or c.get("page_content") or "").strip())


def carregar_magias_nao_encontradas() -> list[dict]:
    """Carrega magias não encontradas (fallback canônico) para indexação."""
    path = Path("data/processed/magias/magias_nao_encontradas_canonico.json")
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    magias = []
    for m in data if isinstance(data, list) else []:
        partes = [
            m.get("nome", ""),
            f"Escola: {m.get('escola', '')}.",
            f"Custo: {m.get('custo', '')}." if m.get("custo") else "",
            f"Execução: {m.get('execucao', '')}." if m.get("execucao") else "",
            f"Alcance: {m.get('alcance', '')}." if m.get("alcance") else "",
            f"Duração: {m.get('duracao', '')}." if m.get("duracao") else "",
            m.get("descricao", ""),
        ]
        magias.append({
            "nome": m.get("nome", ""),
            "escola": m.get("escola", ""),
            "custo": m.get("custo", ""),
            "alcance": m.get("alcance", ""),
            "duracao": m.get("duracao", ""),
            "descricao": m.get("descricao", ""),
            "texto_completo": " ".join(p for p in partes if p),
            "livro": "Manual da Magia - Biblioteca Élfica",
            "status": m.get("status", ""),
        })
    return magias


def carregar_magias_agressivo() -> list[dict] | None:
    """Carrega magias do extrator agressivo (extrair_magias_agressivo.py). Prioridade máxima."""
    path = Path("data/processed/magias/magias_extraidas_agressivo.json")
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return None
    # Monta texto_completo para busca semântica
    magias = []
    for m in data:
        partes = [
            m.get("nome", ""),
            f"Escola: {m.get('escola', '')}.",
            f"Custo: {m.get('custo', '')}.",
            f"Alcance: {m.get('alcance', '')}.",
            f"Duração: {m.get('duracao', '')}.",
            m.get("descricao", ""),
        ]
        m["texto_completo"] = " ".join(p for p in partes if p)
        magias.append(m)
    return magias


def carregar_magias_pipeline_3dt() -> list[dict] | None:
    """Carrega magias do pipeline 3 camadas (extrair_todas_magias_3dt.py) se existir."""
    path = Path("data/processed/magias/magias_3dt_completo.json")
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Filtra apenas magias com descrição (fonte delimitador, delimitador_parcial ou extra)
    return [
        m for m in data
        if m.get("fonte") in ("delimitador", "delimitador_parcial", "extra")
        and m.get("escola") != "NÃO ENCONTRADO"
    ]


def extrair_magias_de_todas_fontes(chunks: list[dict]) -> list[dict]:
    """
    Extrai magias: prioriza extrator agressivo; senão pipeline 3 camadas; senão chunks.
    Adiciona magias não encontradas (fallback canônico) para que apareçam no RAG.
    """
    magias_agressivo = carregar_magias_agressivo()
    if magias_agressivo:
        print(f"  Usando {len(magias_agressivo)} magias do extrator agressivo")
        resultado = [
            {
                "nome": m["nome"],
                "escola": m.get("escola", ""),
                "custo": m.get("custo", ""),
                "alcance": m.get("alcance", ""),
                "duracao": m.get("duracao", ""),
                "descricao": m.get("descricao", ""),
                "texto_completo": m.get("texto_completo", m.get("nome", "")),
                "metadata_orig": {"livro": m.get("livro", "")},
            }
            for m in magias_agressivo
        ]
        # Complemento: magias com descrição manual (sobrescreve extraidas)
        complemento = carregar_magias_nao_encontradas()
        nomes_existentes = {m["nome"].strip().lower() for m in resultado}
        by_name = {m["nome"].strip().lower(): m for m in resultado}
        substituidas = 0
        for m in complemento:
            key = m["nome"].strip().lower()
            if m.get("status") == "inserida_manualmente" and m.get("descricao"):
                if key in by_name:
                    idx = resultado.index(by_name[key])
                    resultado[idx] = {
                        "nome": m["nome"],
                        "escola": m.get("escola", ""),
                        "custo": m.get("custo", ""),
                        "alcance": m.get("alcance", ""),
                        "duracao": m.get("duracao", ""),
                        "descricao": m.get("descricao", ""),
                        "texto_completo": m.get("texto_completo", m["nome"]),
                        "metadata_orig": {"livro": m.get("livro", "")},
                    }
                    substituidas += 1
            elif key not in nomes_existentes:
                resultado.append({
                    "nome": m["nome"],
                    "escola": m.get("escola", ""),
                    "custo": m.get("custo", ""),
                    "alcance": m.get("alcance", ""),
                    "duracao": m.get("duracao", ""),
                    "descricao": m.get("descricao", ""),
                    "texto_completo": m.get("texto_completo", m["nome"]),
                    "metadata_orig": {"livro": m.get("livro", "")},
                })
                nomes_existentes.add(key)
        if substituidas:
            print(f"  + {substituidas} magias com descrição manual (complemento)")
        if len(resultado) > len(magias_agressivo) + substituidas:
            print(f"  + {len(resultado) - len(magias_agressivo) - substituidas} magias não encontradas (fallback)")
        return resultado

    magias_pipeline = carregar_magias_pipeline_3dt()
    if magias_pipeline:
        print(f"  Usando {len(magias_pipeline)} magias do pipeline 3 camadas")
        resultado = [
            {
                "nome": m["nome"],
                "escola": m.get("escola", ""),
                "custo": m.get("custo", ""),
                "alcance": m.get("alcance", ""),
                "duracao": m.get("duracao", ""),
                "descricao": m.get("descricao", ""),
                "texto_completo": m.get("texto_completo", m.get("nome", "")),
                "metadata_orig": {},
            }
            for m in magias_pipeline
        ]
        nomes_existentes = {m["nome"].strip().lower() for m in resultado}
        for m in carregar_magias_nao_encontradas():
            if m["nome"].strip().lower() not in nomes_existentes:
                resultado.append({
                    "nome": m["nome"],
                    "escola": m.get("escola", ""),
                    "custo": m.get("custo", ""),
                    "alcance": m.get("alcance", ""),
                    "duracao": m.get("duracao", ""),
                    "descricao": m.get("descricao", ""),
                    "texto_completo": m.get("texto_completo", m["nome"]),
                    "metadata_orig": {"livro": m.get("livro", "")},
                })
        return resultado

    magias = []
    seen = set()

    # Manual da Magia: texto concatenado por página = mais magias extraídas
    manual = "3dt-alpha-manual-da-magia-biblioteca-elfica.pdf"
    texto_manual = reconstruir_texto_por_pagina(chunks, manual)
    if texto_manual and "Escola:" in texto_manual:
        for m in extrair_magias_de_texto(texto_manual):
            k = (m["nome"].strip(), m.get("escola", ""))
            if k not in seen:
                seen.add(k)
                m["metadata_orig"] = {"source": manual}
                magias.append(m)

    # Outras fontes: chunk a chunk (ex: bestiário)
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        if meta.get("source") == manual:
            continue  # já processado
        content = chunk.get("content") or chunk.get("page_content") or ""
        if "Escola:" not in content or "Custo:" not in content or "Alcance:" not in content:
            continue
        for m in extrair_magias_de_texto(content):
            k = (m["nome"].strip(), m.get("escola", ""))
            if k not in seen:
                seen.add(k)
                m["metadata_orig"] = meta
                magias.append(m)

    return magias


def criar_documentos_magia(magia: dict) -> list[Document]:
    """Cria Document objects para indexacao (nome, cabecalho, completo)."""
    docs = []
    meta_orig = magia.get("metadata_orig") or {}
    livro_raw = meta_orig.get("livro", "") or meta_orig.get("source", "")
    meta_base = {
        "tipo": "magia",
        "nome": magia["nome"],
        "escola": magia.get("escola", ""),
        "custo": magia.get("custo", ""),
        "livro": normalizar_livro(livro_raw) or livro_raw,
    }

    # 1. Nome puro (busca exata)
    docs.append(
        Document(
            page_content=magia["nome"],
            metadata={**meta_base, "tipo_chunk": "magia_nome"},
        )
    )

    # 2. Cabecalho (nome + escola)
    cabecalho = f"{magia['nome']}. Magia de {magia.get('escola', '')}."
    docs.append(
        Document(
            page_content=cabecalho,
            metadata={**meta_base, "tipo_chunk": "magia_cabecalho"},
        )
    )

    # 3. Texto completo
    docs.append(
        Document(
            page_content=magia.get("texto_completo", magia["nome"]),
            metadata={**meta_base, "tipo_chunk": "magia_completa"},
        )
    )
    return docs


def main() -> None:
    print("Carregando chunks...")
    chunks = carregar_chunks()
    print(f"  Chunks totais: {len(chunks)}")

    magias = extrair_magias_de_todas_fontes(chunks)
    print(f"  Magias extraidas: {len(magias)}")

    if not magias:
        print("Nenhuma magia encontrada. Verifique se chunks.json tem formato Escola/Custo/Alcance.")
        return

    docs = []
    for m in magias:
        docs.extend(criar_documentos_magia(m))

    print(f"  Documentos a adicionar: {len(docs)}")

    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos de magia adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")
        print("Dica: o Chroma deve existir. Rode a ingestao primeiro.")


if __name__ == "__main__":
    main()
