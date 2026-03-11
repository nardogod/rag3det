from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.evaluation.response_validator import ValidationResult
from src.types import RetrievedChunk, SourceMetadata


DB_PATH = Path("data") / "feedback.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            user_rating INTEGER NOT NULL,
            chunks_used TEXT NOT NULL,
            rerank_scores TEXT,
            validation_flags TEXT
        )
        """
    )
    return conn


def save_feedback(
    query: str,
    response: str,
    user_rating: int,
    chunks: List[RetrievedChunk] | List[SourceMetadata],
    rerank_scores: Optional[List[float]] = None,
    validation: Optional[ValidationResult] = None,
) -> None:
    """
    Salva feedback do usuário em SQLite.

    - `user_rating`: +1 (correto), -1 (incorreto), 0 (neutro).
    - `chunks`: pode ser lista de RetrievedChunk ou apenas metadados usados.
    """
    conn = _get_connection()
    ts = datetime.utcnow().isoformat() + "Z"

    # Serializa chunks de forma leve
    serializable_chunks = []
    for c in chunks:
        meta: SourceMetadata
        if isinstance(c, dict):
            meta = c  # já é metadado
        else:
            meta = c.metadata or {}
        serializable_chunks.append(
            {
                "book_title": meta.get("book_title"),
                "source": meta.get("source"),
                "page": meta.get("page"),
                "section": meta.get("section"),
            }
        )

    data = (
        ts,
        query,
        response,
        int(user_rating),
        json.dumps(serializable_chunks, ensure_ascii=False),
        json.dumps(rerank_scores or [], ensure_ascii=False),
        json.dumps(asdict(validation) if validation else {}, ensure_ascii=False),
    )

    conn.execute(
        """
        INSERT INTO feedback (
            timestamp, query, response, user_rating,
            chunks_used, rerank_scores, validation_flags
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )
    conn.commit()
    conn.close()


def analyze_feedback() -> dict:
    """
    Lê o banco de feedback e calcula estatísticas simples.

    - Média de rating por query.
    - Top queries com mais avaliações negativas.
    """
    conn = _get_connection()
    cur = conn.cursor()

    # Média de rating por query
    cur.execute(
        """
        SELECT query, AVG(user_rating) as avg_rating, COUNT(*) as n
        FROM feedback
        GROUP BY query
        ORDER BY avg_rating ASC, n DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    low_satisfaction = [
        {"query": r[0], "avg_rating": float(r[1]), "count": int(r[2])}
        for r in rows
        if r[1] is not None and r[1] < 0
    ]

    return {
        "low_satisfaction_queries": low_satisfaction,
        "total_entries": len(rows),
    }

