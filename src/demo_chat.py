from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, List

from src.config import paths
from src.types import QAResult, SourceMetadata


@dataclass(frozen=True)
class DemoEntry:
    title: str
    kind: str
    source: str
    page: int | None
    content: str
    search_text: str


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return " ".join(text.lower().strip().split())


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _build_magia_entries() -> list[DemoEntry]:
    data = _load_json(paths.project_root / "frontend" / "src" / "data" / "magias_3dt.json")
    entries: list[DemoEntry] = []
    for item in data:
        title = str(item.get("nome") or "").strip()
        if not title:
            continue
        source = str(item.get("fonte") or "Magias 3D&T").strip()
        page = item.get("pagina")
        content = " ".join(
            part
            for part in [
                str(item.get("nome") or "").strip(),
                f"Escola: {item.get('escola')}" if item.get("escola") else "",
                f"Custo: {item.get('custo')}" if item.get("custo") else "",
                f"Alcance: {item.get('alcance')}" if item.get("alcance") else "",
                f"Duração: {item.get('duracao')}" if item.get("duracao") else "",
                str(item.get("descricao") or "").strip(),
                str(item.get("texto_completo") or "").strip(),
            ]
            if part
        )
        entries.append(
            DemoEntry(
                title=title,
                kind="magia",
                source=source,
                page=page if isinstance(page, int) else None,
                content=content,
                search_text=_normalize(content),
            )
        )
    return entries


def _build_vantagem_entries() -> list[DemoEntry]:
    data = _load_json(paths.project_root / "frontend" / "src" / "data" / "vantagens_turbinado.json")
    entries: list[DemoEntry] = []
    for item in data:
        title = str(item.get("nome") or "").strip()
        if not title:
            continue
        tipo = str(item.get("tipo") or "vantagem").strip()
        kind = "raca" if tipo == "unica" else tipo
        source = str(item.get("livro") or "Manual 3D&T Turbinado").strip()
        page = item.get("pagina")
        content = " ".join(
            part
            for part in [
                title,
                f"Custo: {item.get('custo')}" if item.get("custo") else "",
                str(item.get("efeito") or "").strip(),
            ]
            if part
        )
        entries.append(
            DemoEntry(
                title=title,
                kind=kind,
                source=source,
                page=page if isinstance(page, int) else None,
                content=content,
                search_text=_normalize(content),
            )
        )
    return entries


def _build_item_entries() -> list[DemoEntry]:
    data = _load_json(paths.project_root / "frontend" / "src" / "data" / "itens_3dt.json")
    entries: list[DemoEntry] = []
    for item in data:
        title = str(item.get("nome") or "").strip()
        if not title:
            continue
        source = str(item.get("livro") or "Itens 3D&T").strip()
        content = " ".join(
            part
            for part in [
                title,
                f"Tipo: {item.get('tipo')}" if item.get("tipo") else "",
                f"Bônus: {item.get('bonus')}" if item.get("bonus") else "",
                f"Custo: {item.get('custo')}" if item.get("custo") else "",
                str(item.get("efeito") or "").strip(),
            ]
            if part
        )
        entries.append(
            DemoEntry(
                title=title,
                kind="item",
                source=source,
                page=None,
                content=content,
                search_text=_normalize(content),
            )
        )
    return entries


def _build_monstro_entries() -> list[DemoEntry]:
    data = _load_json(paths.project_root / "frontend" / "src" / "data" / "monstros.json")
    entries: list[DemoEntry] = []
    for item in data:
        title = str(item.get("nome") or "").strip()
        if not title:
            continue
        car = item.get("caracteristicas") or {}
        car_text = ", ".join(
            f"{key}{value}" for key, value in car.items() if isinstance(value, str) and value.strip()
        )
        habilidades = item.get("habilidades") or []
        habilidades_text = "; ".join(str(h) for h in habilidades if str(h).strip())
        content = " ".join(
            part
            for part in [
                title,
                f"Tipo: {item.get('tipo')}" if item.get("tipo") else "",
                f"Características: {car_text}" if car_text else "",
                f"PV: {item.get('pv')}" if item.get("pv") else "",
                f"PM: {item.get('pm')}" if item.get("pm") else "",
                str(item.get("descricao") or "").strip(),
                habilidades_text,
                str(item.get("comportamento_combate") or "").strip(),
                str(item.get("taticas") or "").strip(),
            ]
            if part
        )
        entries.append(
            DemoEntry(
                title=title,
                kind="monstro",
                source=str(item.get("livro") or item.get("fonte_referencia") or "Bestiário 3D&T").strip(),
                page=item.get("pagina") if isinstance(item.get("pagina"), int) else None,
                content=content,
                search_text=_normalize(content),
            )
        )
    return entries


@lru_cache(maxsize=1)
def _get_entries() -> tuple[DemoEntry, ...]:
    entries = [
        *_build_magia_entries(),
        *_build_vantagem_entries(),
        *_build_item_entries(),
        *_build_monstro_entries(),
    ]
    return tuple(entries)


def _score(entry: DemoEntry, query: str) -> int:
    normalized_query = _normalize(query)
    title = _normalize(entry.title)
    tokens = [token for token in normalized_query.split() if len(token) >= 2]

    score = 0
    if title == normalized_query:
        score += 400
    if normalized_query and normalized_query in title:
        score += 200
    if normalized_query and normalized_query in entry.search_text:
        score += 90

    for token in tokens:
        if token in title:
            score += 40
        if token in entry.search_text:
            score += 8
    if tokens and all(token in title for token in tokens):
        score += 140
    return score


def _sources_from_entries(entries: Iterable[DemoEntry]) -> list[SourceMetadata]:
    sources: list[SourceMetadata] = []
    for entry in entries:
        sources.append(
            SourceMetadata(
                book_title=entry.source,
                source=entry.source,
                page=entry.page or 0,
                section=entry.kind,
            )
        )
    return sources


def _format_list_answer(question: str, entries: list[DemoEntry], heading: str) -> str:
    lines = [heading, ""]
    for entry in entries[:8]:
        excerpt = entry.content.replace(entry.title, "", 1).strip()
        excerpt = excerpt[:180].strip()
        lines.append(f"- **{entry.title}** ({entry.source})")
        if excerpt:
            lines.append(f"  {excerpt}")
    lines.append("")
    lines.append(f"Modo demo: resposta baseada nos dados versionados do projeto para a pergunta '{question}'.")
    return "\n".join(lines)


def answer_demo_question(question: str) -> QAResult:
    query = question.strip()
    normalized_query = _normalize(query)
    if not normalized_query:
        return QAResult(answer="Faça uma pergunta sobre magias, monstros, vantagens ou itens de 3D&T.", sources=[])

    if normalized_query in {"oi", "ola", "olá", "hello", "hi"}:
        return QAResult(
            answer="Olá! Posso responder em modo demo sobre monstros, magias, vantagens e itens de 3D&T usando os dados publicados no projeto.",
            sources=[],
        )

    entries = list(_get_entries())

    if "magia" in normalized_query and "fogo" in normalized_query:
        matches = [entry for entry in entries if entry.kind == "magia" and "fogo" in entry.search_text]
        unique_matches: list[DemoEntry] = []
        seen_titles: set[str] = set()
        for match in matches:
            key = _normalize(match.title)
            if key in seen_titles:
                continue
            seen_titles.add(key)
            unique_matches.append(match)
        if unique_matches:
            return QAResult(
                answer=_format_list_answer(query, unique_matches, "Encontrei estas magias relacionadas a fogo:"),
                sources=_sources_from_entries(unique_matches[:8]),
            )

    ranked = sorted(
        ((entry, _score(entry, query)) for entry in entries),
        key=lambda item: item[1],
        reverse=True,
    )
    ranked = [(entry, score) for entry, score in ranked if score > 0][:5]

    if not ranked:
        return QAResult(
            answer=(
                "Modo demo: não encontrei uma resposta direta nos dados publicados do projeto. "
                "Tente usar o nome exato da magia, monstro, vantagem ou item."
            ),
            sources=[],
        )

    best_entry, best_score = ranked[0]
    if best_score >= 200:
        answer = (
            f"**{best_entry.title}**\n\n"
            f"{best_entry.content}\n\n"
            f"Modo demo: resposta baseada nos dados publicados do projeto."
        )
        return QAResult(answer=answer, sources=_sources_from_entries([best_entry]))

    answer = _format_list_answer(
        query,
        [entry for entry, _ in ranked],
        "Encontrei estas referências relacionadas à sua pergunta:",
    )
    return QAResult(answer=answer, sources=_sources_from_entries([entry for entry, _ in ranked]))
