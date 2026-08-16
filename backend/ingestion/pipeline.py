"""
backend/ingestion/pipeline.py

The orchestrator — this is the single function the rest of the system
(Telegram bot, future /ingest API endpoint) calls. It doesn't know or
care about YouTube vs articles beyond routing; that logic lives in
youtube.py / article.py.

Flow: URL -> route -> extract -> chunk -> embed -> store in both DBs,
linked by a shared source_id.
"""

import os
import sys
import uuid

# backend/ingestion/ and backend/storage/ are sibling folders — add
# backend/ (the parent of this file's folder) to the path so both
# `from youtube import ...` and `from storage.vector_store import ...`
# resolve correctly regardless of where this script is run from.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.append(_BACKEND_DIR)

from youtube import process_youtube_url
from article import process_article_url, is_youtube_url
from chunk import chunk_text
from storage.vector_store import add_chunks
from storage.metadata_db import add_source, init_db


def ingest_url(url: str) -> dict:
    """
    Main entry point for adding a new memory. Returns a summary dict
    the API/bot can use to confirm success to the user.
    """
    init_db()  # safe to call every time — no-ops if table already exists

    source_id = str(uuid.uuid4())

    if is_youtube_url(url):
        content = process_youtube_url(url)
        title = content.title
        raw_text = content.transcript
        source_type = "youtube"
    else:
        content = process_article_url(url)
        title = content.title
        raw_text = content.text
        source_type = "article"

    chunks = chunk_text(raw_text, chunk_size=400, overlap=50)

    if not chunks:
        raise ValueError(f"No content extracted from {url} — nothing to store.")

    add_chunks(
        source_id=source_id,
        chunks=chunks,
        title=title,
        url=url,
        source_type=source_type,
    )

    add_source(
        source_id=source_id,
        title=title,
        url=url,
        source_type=source_type,
        chunk_count=len(chunks),
    )

    return {
        "source_id": source_id,
        "title": title,
        "source_type": source_type,
        "chunk_count": len(chunks),
    }


# --- Quick manual test ---
# Run from backend/ingestion/: python pipeline.py
if __name__ == "__main__":
    test_url = input("Paste a YouTube or article URL to fully ingest: ").strip()
    result = ingest_url(test_url)
    print(f"\n✅ Ingested: {result['title']}")
    print(f"   Type: {result['source_type']}")
    print(f"   Chunks stored: {result['chunk_count']}")
    print(f"   Source ID: {result['source_id']}")
