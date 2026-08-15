# 🧠 Recall — Implementation Plan

> Building a brain in six stages, the same way a real one develops: senses first, memory second, voice last.

Each stage below is a **milestone**, not a sprint deadline — move to the next once the current one actually works, tested from the command line before any UI touches it.

---

## 🥚 Stage 0 — Setup
*"Before a brain can think, it needs a skull."*

- [ ] Repo scaffold: `backend/`, `frontend/`, `telegram_bot/`
- [ ] Python venv + `requirements.txt` (langchain, chromadb, sentence-transformers, fastapi, uvicorn, youtube-transcript-api, yt-dlp, trafilatura, python-telegram-bot)
- [ ] `.env` for API keys (Claude API key, Telegram bot token) — **never commit this**
- [ ] `config.py` — central place for chunk size, top-k, model names

---

## 👁️ Stage 1 — Senses (Ingestion)
*Teach the brain to perceive.*

- [ ] `ingestion/youtube.py`
  - Extract video ID from any YouTube URL format
  - Pull transcript via `youtube-transcript-api`
  - Pull title/channel/duration via `yt-dlp` metadata
- [ ] `ingestion/article.py`
  - Fetch URL, run through `trafilatura` for clean text
- [ ] **Checkpoint:** run both extractors standalone on 3 real links each, print clean output to terminal. If the text is messy, fix extraction before moving on — garbage in, garbage remembered.

---

## 🗂️ Stage 2 — Hippocampus (Encoding)
*Teach the brain to file what it perceives.*

- [ ] `storage/vector_store.py` — ChromaDB client, `add_chunks()`, `query()`, `delete_by_source()`
- [ ] `storage/metadata_db.py` — SQLite schema: `id, title, url, source_type, date_added, tags`
- [ ] `ingestion/pipeline.py` — orchestrates: extract → chunk (~300–500 tokens, ~50 overlap) → embed → store in both DBs, linked by a shared `source_id`
- [ ] **Checkpoint:** ingest 5 real links end-to-end, confirm chunk count + metadata rows match in both stores

---

## 💬 Stage 3 — Voice (Retrieval + Reasoning)
*Teach the brain to answer, not just store.*

- [ ] `agent/retriever.py` — embed query → top-k semantic search → return chunks + their source metadata
- [ ] `agent/qa_chain.py` — LangChain LCEL chain with a citation-aware prompt:
  > *"Answer only from the provided context. Cite the source title for each claim. If nothing relevant is found, say so plainly."*
- [ ] **Checkpoint:** CLI test — ask 5 questions you know the answer to (because you watched/read the source), confirm answers are accurate *and* correctly cited

---

## 🌐 Stage 4 — The Gateway (API)
*Give the brain a mouth to the outside world.*

- [ ] `api/ingest.py` — `POST /ingest {url}` → runs Stage 1+2 pipeline
- [ ] `api/chat.py` — `POST /chat {question}` → streams tokens via SSE from Stage 3 chain
- [ ] `api/memory.py` — `GET /memory` (list all), `DELETE /memory/{id}` (removes from **both** ChromaDB and SQLite, atomically)
- [ ] **Checkpoint:** test all three endpoints with `curl`/Postman before writing any frontend code

---

## 💻 Stage 5 — The Face (Frontend)
*Give the brain an expression.*

- [ ] `Sidebar.jsx` — Chat / Memory / Add Link tabs
- [ ] `ChatWindow.jsx` — connects to `/chat` SSE stream, renders answer token-by-token with source citations as clickable links
- [ ] `MemoryBrowser.jsx` — searchable/filterable list of everything stored, delete button per item
- [ ] `AddLink.jsx` — paste a URL, live ingestion status ("Fetching → Chunking → Indexed ✅")
- [ ] **Checkpoint:** full loop — paste a link in the UI, watch it get indexed, ask about it in chat, see a cited streaming answer

---

## 📱 Stage 6 — The Second Mouth (Telegram Bot)
*Let the brain hear you from anywhere.*

- [ ] `telegram_bot/bot.py` — listens for messages, detects URLs, calls the same `/ingest` endpoint the UI uses (no duplicated logic)
- [ ] **Checkpoint:** forward a link to your bot from your phone, confirm it shows up in the Memory tab

---

## 🚀 Stage 7 — Making It *Smart* (Stretch Goals)
*The difference between a search bar and a second brain.*

- [ ] **Auto-tagging** — LLM generates 3–5 topic tags on ingest, filterable in Memory Browser
- [ ] **Cross-source synthesis** — prompt the agent to explicitly connect ideas across multiple sources in one answer
- [ ] **Spaced-repetition nudges** — background job flags memories untouched in 2+ weeks, surfaces them proactively
- [ ] **Knowledge-gap fallback** — if retrieval finds nothing relevant, offer to search the web instead of hallucinating
- [ ] **Voice input** — Whisper-powered voice questions (you've already done this in ContextIQ AI)

---

## Suggested commit rhythm

Each ✅ checkpoint above = one meaningful commit/PR. This gives your repo a clean, readable history that tells the story of the build — genuinely useful if you ever walk someone through this project in an interview.
