# 🧠 Recall

**Your own digital hippocampus.** Recall is a personal RAG (Retrieval-Augmented Generation) agent that remembers everything you've learned — YouTube videos you've watched, articles you've read, projects you've built — and answers your questions from that knowledge, with sources cited.

No more "I know I saw this somewhere but can't remember where." Just ask Recall.

---

## Why

Recommendation engines tell you what to consume next. Recall does the opposite job: it remembers what you *already* consumed, so you can actually use it later — as a searchable, queryable second brain instead of a scattered history of open tabs and closed videos.

## How it works

1. **Feed it** — paste a YouTube link or article URL (via the web UI or a Telegram bot)
2. **It remembers** — transcript/article text is extracted, chunked, embedded, and stored
3. **Ask it anything** — get a streamed, cited answer pulled only from what you've actually learned

Full breakdown in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Build roadmap in [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md).

## Tech Stack

- **Frontend:** React + Tailwind, streaming chat UI (SSE)
- **Backend:** FastAPI
- **Orchestration:** LangChain (LCEL)
- **Embeddings:** Sentence Transformers
- **Vector store:** ChromaDB
- **Metadata:** SQLite
- **LLM:** Claude API
- **Secondary input:** Telegram Bot

## Project Structure

```
recall/
├── backend/
│   ├── api/          # FastAPI routes: /chat, /ingest, /memory
│   ├── agent/         # retrieval + LCEL QA chain
│   ├── ingestion/      # YouTube/article extraction + chunk/embed pipeline
│   └── storage/         # ChromaDB + SQLite wrappers
├── frontend/
│   └── src/components/  # ChatWindow, Sidebar, MemoryBrowser, AddLink
├── telegram_bot/
├── ARCHITECTURE.md
└── IMPLEMENTATION_PLAN.md
```

## Status

🚧 In active development — following the staged plan in [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md).

## Setup

```bash
git clone <your-repo-url>
cd recall
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # add your Claude API key + Telegram bot token
```

## License

MIT
