"""
Reindexa Vantagens e Desvantagens no Chroma para busca RAG.
Carrega vantagens_turbinado_canonico.json (Manual Turbinado) e vantagens_magia
(Manual da Magia), aplicando política de prioridade entre fontes.
Executar: python scripts/reindexar_vantagens.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.utils.expandir_siglas_3dt import expandir_siglas_3dt
from src.utils.livro_normalizado import normalizar_livro, obter_prioridade_fonte
from src.vectorstore.chroma_store import get_vectorstore

BASE = Path(__file__).resolve().parent.parent
VD_DIR = BASE / "data" / "processed" / "vantagens_desvantagens"


def carregar_turbinado() -> list[dict]:
    """Carrega vantagens do Manual Turbinado (canônico)."""
    path = VD_DIR / "vantagens_turbinado_canonico.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def carregar_magia() -> list[dict]:
    """Carrega vantagens do Manual da Magia (categorizadas ou extraídas)."""
    cat_path = VD_DIR / "vantagens_magia_categorizadas.json"
    path = cat_path if cat_path.exists() else VD_DIR / "vantagens_magia_extraidas.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def mesclar_vantagens_com_prioridade() -> list[dict]:
    """
    Mescla turbinado + magia. Política: Manual Turbinado > Manual da Magia.
    Para duplicatas (mesmo nome), usa a fonte com maior prioridade.
    """
    turbinado = carregar_turbinado()
    magia = carregar_magia()
    por_nome: dict[str, dict] = {}
    for m in turbinado:
        nome = (m.get("nome") or "").strip()
        if nome:
            m["livro"] = normalizar_livro(m.get("livro")) or m.get("livro", "")
            por_nome[nome.lower()] = m
    for m in magia:
        nome = (m.get("nome") or "").strip()
        if not nome:
            continue
        key = nome.lower()
        livro_m = normalizar_livro(m.get("livro")) or m.get("livro", "")
        m["livro"] = livro_m
        if key in por_nome:
            # Mantém o que tem maior prioridade (menor índice)
            if obter_prioridade_fonte(livro_m) < obter_prioridade_fonte(por_nome[key].get("livro")):
                por_nome[key] = m
        else:
            por_nome[key] = m
    resultado = list(por_nome.values())
    for m in resultado:
        partes = [
            m.get("nome", ""),
            f"Tipo: {m.get('tipo', '')}." if m.get("tipo") else "",
            f"Custo: {m.get('custo', '')}." if m.get("custo") else "",
            m.get("efeito", ""),
            f"Fonte: {m.get('livro', '')}." if m.get("livro") else "",
        ]
        texto = " ".join(p for p in partes if p)
        m["texto_completo"] = expandir_siglas_3dt(texto)
    return resultado


def carregar_vantagens() -> list[dict] | None:
    """Carrega vantagens mescladas (turbinado + magia) com prioridade de fontes."""
    data = mesclar_vantagens_com_prioridade()
    return data if data else None


def carregar_kits() -> list[dict]:
    """Carrega Kits de personagem (entidade separada de vantagens)."""
    path = VD_DIR / "kits_canonico.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def criar_documentos_kit(item: dict) -> list[Document]:
    """Cria Document objects para Kits (tipo: kit)."""
    docs = []
    partes = [
        item.get("nome", ""),
        f"Custo: {item.get('custo', '')}." if item.get("custo") else "",
        f"Restrições: {item.get('restricoes', '')}." if item.get("restricoes") else "",
        f"Vantagens: {item.get('vantagens', '')}." if item.get("vantagens") else "",
        item.get("efeito", ""),
        f"Fonte: {item.get('livro', '')}." if item.get("livro") else "",
    ]
    texto_completo = expandir_siglas_3dt(" ".join(p for p in partes if p))
    meta_base = {
        "tipo": "kit",
        "nome": item["nome"],
        "tipo_item": "kit",
        "custo": item.get("custo", ""),
        "livro": normalizar_livro(item.get("livro")) or item.get("livro", ""),
    }
    docs.append(
        Document(
            page_content=item["nome"],
            metadata={**meta_base, "tipo_chunk": "kit_nome"},
        )
    )
    cabecalho = f"{item['nome']} (Kit). Custo: {item.get('custo', '')}."
    docs.append(
        Document(
            page_content=expandir_siglas_3dt(cabecalho.strip()),
            metadata={**meta_base, "tipo_chunk": "kit_cabecalho"},
        )
    )
    docs.append(
        Document(
            page_content=texto_completo,
            metadata={**meta_base, "tipo_chunk": "kit_completo"},
        )
    )
    return docs


def criar_documentos_vantagem(item: dict) -> list[Document]:
    """Cria Document objects para indexação."""
    docs = []
    meta_base = {
        "tipo": "vantagem_desvantagem",
        "nome": item["nome"],
        "tipo_item": item.get("tipo", ""),
        "custo": item.get("custo", ""),
        "livro": item.get("livro", ""),
        "categoria": item.get("categoria", ""),
        "categoria_label": item.get("categoria_label", ""),
    }

    docs.append(
        Document(
            page_content=item["nome"],
            metadata={**meta_base, "tipo_chunk": "vantagem_nome"},
        )
    )

    cabecalho = f"{item['nome']}. "
    if item.get("tipo"):
        cabecalho += f"Tipo: {item['tipo']}. "
    if item.get("custo"):
        cabecalho += f"Custo: {item['custo']}. "
    docs.append(
        Document(
            page_content=expandir_siglas_3dt(cabecalho.strip()),
            metadata={**meta_base, "tipo_chunk": "vantagem_cabecalho"},
        )
    )

    docs.append(
        Document(
            page_content=item.get("texto_completo", expandir_siglas_3dt(item["nome"])),
            metadata={**meta_base, "tipo_chunk": "vantagem_completo"},
        )
    )
    return docs


def carregar_efeitos_em_pericias() -> list[dict]:
    """Carrega Efeitos de V/D em Perícias (bônus/redutores)."""
    path = VD_DIR / "efeitos_em_pericias.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def criar_documentos_efeito_pericia(item: dict) -> list[Document]:
    """Cria Document para efeito de V/D em Perícias."""
    texto = f"{item['vantagem_desvantagem']}: {item['efeitos']}"
    meta = {
        "tipo": "efeito_vantagem_pericia",
        "nome": item["vantagem_desvantagem"],
        "tipo_item": item.get("tipo", ""),
        "efeitos": item.get("efeitos", ""),
    }
    return [
        Document(page_content=texto, metadata={**meta, "tipo_chunk": "efeito_pericia"}),
    ]


def main() -> None:
    print("Carregando vantagens e desvantagens...")

    itens = carregar_vantagens()
    if not itens:
        print("Nenhuma vantagem encontrada. Execute: python scripts/extrair_vantagens_magia_agressivo.py")
        return

    print(f"  Itens carregados: {len(itens)}")

    docs = []
    for item in itens:
        docs.extend(criar_documentos_vantagem(item))

    # Kits de personagem (entidade separada)
    kits = carregar_kits()
    if kits:
        for k in kits:
            docs.extend(criar_documentos_kit(k))
        print(f"  Kits carregados: {len(kits)}")

    # Efeitos de V/D em Perícias (bônus/redutores)
    efeitos = carregar_efeitos_em_pericias()
    if efeitos:
        for e in efeitos:
            docs.extend(criar_documentos_efeito_pericia(e))
        print(f"  Efeitos em Perícias: {len(efeitos)}")

    print(f"  Documentos a adicionar: {len(docs)}")

    try:
        vs = get_vectorstore()
        vs.add_documents(docs)
        print(f"[OK] {len(docs)} documentos de vantagens/desvantagens/efeitos adicionados ao Chroma.")
    except Exception as e:
        print(f"Erro ao adicionar ao Chroma: {e}")
        print("Dica: o Chroma deve existir. Rode a ingestao primeiro.")


if __name__ == "__main__":
    main()
