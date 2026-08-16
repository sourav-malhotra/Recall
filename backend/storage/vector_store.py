"""
backend/storage/vector_store.py

Thin wrapper around ChromaDB — this is "the Cortex" from the architecture
doc. Handles embedding chunks, storing them, and semantic search.

Deliberately dumb: no reasoning here, just storage + similarity search.
All the "intelligence" lives in agent/retriever.py and agent/qa_chain.py.
"""

import chromadb
from sentence_transformers import SentenceTransformer

# BAAI/bge-small-en-v1.5: small, fast, strong English embedding quality.
# Since we standardized on translating everything to English before it
# reaches this layer, an English-only embedding model is the right choice.
_EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_COLLECTION_NAME = "recall_memory"
_DB_PATH = "./chroma_db"  # persisted to disk, survives restarts

_model = None
_client = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_EMBEDDING_MODEL_NAME)
    return _model


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=_DB_PATH)
        _collection = _client.get_or_create_collection(name=_COLLECTION_NAME)
    return _collection


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds a batch of text chunks into vectors."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def add_chunks(
    source_id: str,
    chunks: list[str],
    title: str,
    url: str,
    source_type: str,
) -> None:
    """
    Embeds and stores a list of text chunks belonging to one source
    (one video or one article). Each chunk gets its own ID:
    f"{source_id}_{index}", so they can all be found/deleted together
    via the shared source_id in the metadata filter.
    """
    if not chunks:
        return

    collection = _get_collection()
    embeddings = embed_texts(chunks)

    ids = [f"{source_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source_id": source_id, "title": title, "url": url, "source_type": source_type}
        for _ in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def query(question: str, top_k: int = 5) -> list[dict]:
    """
    Semantic search — embeds the question, returns the top_k most similar
    chunks across all stored sources, each with its text + source metadata.
    """
    collection = _get_collection()
    question_embedding = embed_texts([question])[0]

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
    )

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return matches


def delete_by_source(source_id: str) -> None:
    """
    Removes ALL chunks belonging to one source (one video/article).
    Must be called alongside metadata_db.delete_source() to avoid orphaned
    data — see the data-consistency note in ARCHITECTURE.md.
    """
    collection = _get_collection()
    collection.delete(where={"source_id": source_id})


# --- Quick manual test ---
if __name__ == "__main__":
    test_chunks = [
        "Wireshark is a network packet analyzer used for troubleshooting.",
        "It captures live traffic and can inspect packet capture files.",
    ]
    add_chunks(
        source_id="test-001",
        chunks=test_chunks,
        title="Wireshark: The Basics",
        url="https://medium.com/@4ghora/wireshark-the-basics-df1d23c3ab40",
        source_type="article",
    )
    print("Stored 2 test chunks.")

    results = query("what is wireshark used for?", top_k=2)
    print(f"\nQuery returned {len(results)} results:")
    for r in results:
        print(f"- ({r['distance']:.4f}) {r['text'][:80]}...")

    delete_by_source("test-001")
    print("\nCleaned up test data.")
