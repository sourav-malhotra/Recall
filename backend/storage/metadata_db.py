"""
backend/storage/metadata_db.py

SQLite wrapper for source metadata — title, url, type, date added, tags.
This is the "bookkeeping" half of the Cortex; vector_store.py handles
the "meaning" half. Every source lives in BOTH stores, linked by the
same source_id.
"""

import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager

_DB_PATH = "./recall_metadata.db"


@contextmanager
def _get_connection():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Creates the sources table if it doesn't exist yet. Safe to call every startup."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source_type TEXT NOT NULL,      -- 'youtube' or 'article'
                date_added TEXT NOT NULL,        -- ISO timestamp
                tags TEXT,                        -- comma-separated, for Stage 7 auto-tagging
                chunk_count INTEGER NOT NULL
            )
        """)


def add_source(source_id: str, title: str, url: str, source_type: str, chunk_count: int, tags: str = "") -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sources (id, title, url, source_type, date_added, tags, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (source_id, title, url, source_type, datetime.now(timezone.utc).isoformat(), tags, chunk_count),
        )


def list_sources() -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute("SELECT * FROM sources ORDER BY date_added DESC").fetchall()
        return [dict(row) for row in rows]


def get_source(source_id: str) -> dict | None:
    with _get_connection() as conn:
        row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
        return dict(row) if row else None


def delete_source(source_id: str) -> None:
    """
    Removes the metadata row for one source. Must be called alongside
    vector_store.delete_by_source() — deleting from only one store leaves
    orphaned data (see the data-consistency note in ARCHITECTURE.md).
    """
    with _get_connection() as conn:
        conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))


# --- Quick manual test ---
if __name__ == "__main__":
    init_db()
    add_source(
        source_id="test-001",
        title="Wireshark: The Basics",
        url="https://medium.com/@4ghora/wireshark-the-basics-df1d23c3ab40",
        source_type="article",
        chunk_count=2,
    )
    print("Sources currently stored:")
    for s in list_sources():
        print(f"- {s['title']} ({s['source_type']}, {s['chunk_count']} chunks)")

    delete_source("test-001")
    print("\nCleaned up test data.")
