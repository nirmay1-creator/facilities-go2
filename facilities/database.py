"""
SQLite database layer.

Creates the `analyses` table on first use and provides functions to:
  - save a validated result
  - fetch history records

Only validated AnalysisResult objects are ever written to the DB.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from facilities.config import settings
from facilities.models import HistoryRecord


def _get_connection() -> sqlite3.Connection:
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the analyses table if it does not exist."""
    conn = _get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                subject         TEXT    NOT NULL,
                request_text    TEXT    NOT NULL,
                summary         TEXT    NOT NULL,
                next_action     TEXT    NOT NULL,
                category        TEXT    NOT NULL,
                priority        TEXT    NOT NULL,
                requires_review INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT    NOT NULL
            )
            """
        )
    conn.close()


def save_analysis(subject: str, request_text: str, result) -> HistoryRecord:
    """
    Persist a validated AnalysisResult and return the saved HistoryRecord.

    Parameters
    ----------
    subject      : original subject string
    request_text : original request text
    result       : a validated AnalysisResult instance
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses
                (subject, request_text, summary, next_action,
                 category, priority, requires_review, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                subject,
                request_text,
                result.summary,
                result.next_action,
                result.category,
                result.priority,
                1 if result.requires_review else 0,
                now,
            ),
        )
        row_id = cursor.lastrowid
    conn.close()

    return HistoryRecord(
        id=row_id,
        subject=subject,
        request_text=request_text,
        summary=result.summary,
        next_action=result.next_action,
        category=result.category,
        priority=result.priority,
        requires_review=result.requires_review,
        created_at=datetime.fromisoformat(now),
    )


def get_history(limit: int = 100) -> list[HistoryRecord]:
    """Return the most recent `limit` analysis records."""
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT id, subject, request_text, summary, next_action,
               category, priority, requires_review, created_at
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    return [
        HistoryRecord(
            id=row["id"],
            subject=row["subject"],
            request_text=row["request_text"],
            summary=row["summary"],
            next_action=row["next_action"],
            category=row["category"],
            priority=row["priority"],
            requires_review=bool(row["requires_review"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]
