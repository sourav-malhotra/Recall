#  Recall — System Architecture

> *"You've watched it. You've read it. You've built it. You just forgot where."*
> Recall is the second brain that remembers so you don't have to.

---

## The Metaphor

Think of Recall as a **digital hippocampus** — the part of your brain that decides what's worth remembering and files it away for later retrieval. Every video you save, every article you read, every project you push to GitHub becomes a **memory trace**. Ask Recall a question, and it doesn't guess — it *recalls*, citing exactly which memory the answer came from.

Four organs make up this brain:

| Organ | Biological analogy | What it actually does |
|---|---|---|
| **The Senses** | Eyes/ears — how memories enter | Ingestion pipeline (YouTube, articles, GitHub) |
| **The Hippocampus** | Encodes short-term → long-term memory | Chunking + embedding pipeline |
| **The Cortex** | Long-term storage | ChromaDB (vectors) + SQLite (metadata) |
| **The Voice** | Speech/reasoning center | LangChain agent + Claude, streamed to chat UI |

---

## High-Level Diagram

```
                     ╔══════════════════════════════╗
                     ║        YOU (the user)         ║
                     ╚═══════════════╦════════════════╝
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
      ┌───────────────┐     ┌─────────────────┐     ┌──────────────────┐
      │  Web UI      │     │  Telegram Bot  │     │  (future) Chrome   │
      │  React + Tailwind│     │  quick link drop │     │  extension          │
      └───────┬────────┘     └────────┬─────────┘     └─────────┬─────────┘
              │                       │                          │
              └───────────────┬───────┴──────────────────────────┘
                               ▼
                     ┌──────────────────────┐
                     │   FastAPI Gateway      │
                     │  /chat  /ingest  /memory│
                     └──────────┬─────────────┘
                                │
           ┌────────────────────┼─────────────────────┐
           ▼                    ▼                      ▼
 ┌───────────────────┐ ┌─────────────────┐  ┌───────────────────────┐
 │  SENSES           │ │  VOICE          │  │  HIPPOCAMPUS           │
 │ youtube.py          │ │ retriever.py     │  │ chunk.py                │
 │ article.py           │ │ qa_chain.py      │  │ embed.py                │
 │ github.py             │ │ (LangChain LCEL) │  │                          │
 └──────────┬──────────┘ └────────┬─────────┘  └────────────┬─────────────┘
            │                     │                          │
            └─────────────────────┼──────────────────────────┘
                                  ▼
                      ┌───────────────────────┐
                      │    CORTEX               │
                      │  ChromaDB (vectors)      │
                      │  SQLite (metadata)        │
                      └───────────────────────┘
```

---

## Component Breakdown

### 1. The Senses — Ingestion Layer
Responsible for turning a raw link into clean, structured text.

- `youtube.py` — `youtube-transcript-api` + `yt-dlp` pull transcript + title/channel, no OAuth needed
- `article.py` — `trafilatura` strips ads/navigation, returns clean readable text
- `github.py` *(stretch)* — pulls README + commit messages from your own repos, so "what I've built" is also queryable

### 2. The Hippocampus — Encoding Layer
Turns raw text into searchable memory.

- `chunk.py` — splits text into ~300–500 token pieces with slight overlap so no idea gets cut mid-sentence
- `embed.py` — Sentence Transformers (`bge-small-en`) turns each chunk into a vector

### 3. The Cortex — Storage Layer
- **ChromaDB** — the vector memory: "what does this *mean*"
- **SQLite** — the metadata memory: "what *is* this, and when did I learn it" (title, url, source type, date, tags)

Two stores, two jobs — meaning vs. bookkeeping. Deleting a memory means deleting from **both**, atomically, or you get a ghost memory (vector with no name).

### 4. The Voice — Reasoning Layer
- `retriever.py` — semantic (+ optional keyword) search across the Cortex for the top-k relevant memories
- `qa_chain.py` — LangChain LCEL chain: retrieved memories + your question → Claude → streamed, cited answer

---

## Why This Shape

- **Senses are swappable** — adding a new source (podcasts, Kindle highlights, Twitter bookmarks) means writing one new file in `ingestion/`, nothing else changes
- **Cortex is dumb on purpose** — it just stores; all the "intelligence" lives in the Voice layer, which keeps retrieval logic testable in isolation from storage
- **One gateway, many mouths** — Web UI, Telegram, and a future browser extension all hit the same FastAPI endpoints, so there's no duplicated ingestion logic to maintain

---

## Tech Stack Summary

| Layer | Tool |
|---|---|
| Frontend | React + Tailwind, SSE streaming |
| API | FastAPI |
| Orchestration | LangChain (LCEL) |
| Embeddings | Sentence Transformers |
| Vector store | ChromaDB |
| Metadata | SQLite |
| LLM | Claude API |
| Secondary input | Telegram Bot API |
