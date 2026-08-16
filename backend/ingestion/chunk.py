"""
backend/ingestion/chunk.py

Splits long text (transcripts, articles) into overlapping chunks sized by
token count, not character count — LLMs and embedding models think in
tokens, so this keeps chunks consistently sized regardless of language
or verbosity.
"""

import tiktoken

# cl100k_base is the tokenizer used by GPT-4/Claude-family models — good
# enough as a general-purpose token counter even though we're not calling
# OpenAI directly.
_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    Splits text into chunks of ~chunk_size tokens, with `overlap` tokens
    repeated between consecutive chunks so an idea that spans a chunk
    boundary doesn't get cut off mid-thought and lose context.

    chunk_size=400 is a reasonable default: big enough to hold a full idea
    or a few sentences of transcript, small enough to keep retrieval precise
    (a 400-token chunk is roughly 1-2 paragraphs).
    """
    if not text or not text.strip():
        return []

    tokens = _encoding.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_str = _encoding.decode(chunk_tokens)
        chunks.append(chunk_str.strip())

        if end >= len(tokens):
            break
        start = end - overlap  # step forward, but re-include the overlap

    return chunks


# --- Quick manual test ---
if __name__ == "__main__":
    sample = "This is a test sentence. " * 200  # ~1000+ tokens
    result = chunk_text(sample, chunk_size=100, overlap=20)
    print(f"Split into {len(result)} chunks")
    print(f"First chunk token count: {count_tokens(result[0])}")
    print(f"First chunk preview: {result[0][:100]}...")
