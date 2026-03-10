# RAG Project

A retrieval-augmented generation (RAG) API: ingest documents, then ask questions and get answers grounded in stored content. Uses open-source models via Ollama (embeddings + LLM) and Chroma for the vector store. Data is isolated per session and expires after a configurable TTL. Advanced options let you tune chunking and retrieval per session. The Streamlit UI keeps a chat-style history of questions and answers for the current session, supports uploading multiple documents at once, and uses a single flow: documents are ingested automatically when you select files (no separate Ingest button).

## Stack

- **API:** FastAPI
- **Embeddings:** Ollama (`nomic-embed-text`)
- **Vector store:** Chroma (persistent, cosine similarity)
- **LLM:** Mistral 7B (Ollama)
- **Session tracking:** SQLite (`session_state.db`)

## Setup

1. Create and activate the conda env:

   ```bash
   conda env create -f environment.yml
   conda activate rag
   ```

   Or: `conda create -n rag python=3.11 -y` then `pip install -r requirements.txt`.

2. Copy env template and set options if needed:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` for `VECTOR_STORE_PATH`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `SESSION_TTL_SECONDS`, `SESSION_CLEANUP_INTERVAL_SECONDS`, etc.

3. Run Ollama and pull models:

   ```bash
   ollama pull nomic-embed-text
   ollama pull mistral
   ```

4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

   - Health: http://127.0.0.1:8000/health
   - Docs: http://127.0.0.1:8000/docs

5. (Optional) Start the Streamlit UI to upload docs and ask questions in the browser:

   ```bash
   python -m streamlit run streamlit_app.py
   ```

   Open http://localhost:8501. Keep the API running in another terminal.

## Session isolation & TTL

- Every **ingest** and **query** request must send the header **`X-Session-ID`** (any string, e.g. a UUID). All chunks are stored and searched per session; users only see their own documents.
- **TTL:** Sessions that receive no requests for `SESSION_TTL_SECONDS` (default 1800) are removed automatically. A background task runs every `SESSION_CLEANUP_INTERVAL_SECONDS` (default 30).
- **Deduplication:** Re-ingesting the same file in a session replaces that source’s chunks (no duplicates).
- **DELETE /session** clears the current session’s data (used by “Start new session” in the UI).

## Per-session advanced options

In the Streamlit UI there is an **“Advanced options”** panel that controls behavior **per browser session**:

- **Chunk size (characters):** Maximum length of each stored chunk. Defaults to `CHUNK_SIZE` from `.env`.
- **Chunk overlap (characters):** How much neighboring chunks overlap. Defaults to `CHUNK_OVERLAP`.
- **Top K:** Number of chunks retrieved per query. Defaults to `TOP_K`.

These settings:

- Apply only to the current session’s uploads and questions.
- Are sent to the FastAPI backend on each ingest/query and override the config defaults.
- Reset only when you change them or restart the browser tab (the session’s data still respects TTL and `/session` deletion).

## Single-flow upload

In the Streamlit UI, **ingest runs automatically** when you choose one or more files in the upload area. There is no separate “Ingest” button: once the file selection changes, the app sends the files to `POST /ingest/files` and shows chunk counts. The same selection is not re-ingested on later runs; change the selection or click “Start new session” to ingest again. This keeps the flow to: select files → (auto-ingest) → ask questions.

## Chat history

In the Streamlit UI, a **“Previous Q&A”** section shows all questions and answers for the current browser session. Each entry displays the question, the answer, and expandable sources. History is kept in memory only (per tab) and is cleared when you click **“Start new session”**; it is not sent to or stored by the API.

## API

- **GET /health** — Liveness check; returns `{"status": "ok"}`.

- **POST /ingest/file** — Upload a single document (PDF, TXT, or MD). Send as **form-data** with key `file`. Include header **`X-Session-ID`**. Optional form fields: `chunk_size`, `chunk_overlap`. Returns `{"ok": true, "chunks_added": n}`.

  Example in Postman: Body → form-data → key `file` (type: File) → select a file; add header `X-Session-ID: your-session-id`.

- **POST /ingest/files** — Upload multiple documents in one request. Send as **form-data** with key `files` (multiple file parts). Include header **`X-Session-ID`**. Optional form fields: `chunk_size`, `chunk_overlap`. Returns `{"ok": true, "total_chunks": n, "files": [{"filename": "...", "chunks_added": k}, ...]}`. The UI uses this for “Choose one or more files”.

- **POST /query** — Ask a question. Body: JSON `{"question": "..."}`. Include header **`X-Session-ID`**. Returns `{"answer": "...", "sources": [...]}` (each source has `document` snippet and `metadata`).

  Example in Postman: Body → raw → JSON → `{"question": "What is in the document?"}`; add header `X-Session-ID: your-session-id`.

- **DELETE /session** — Delete the session’s chunks and tracking. Include header **`X-Session-ID`**. Returns `{"ok": true, "deleted_chunks": n}`.

## Project layout

- `app/main.py` — FastAPI app (health, ingest/file, ingest/files, query, DELETE session), lifespan cleanup
- `app/config.py` — Settings from env
- `app/embedding.py` — Text to vector via Ollama
- `app/store.py` — Chroma: add/upsert chunks, search by similarity, delete by session/source
- `app/llm.py` — Call Mistral via Ollama for generation
- `app/query.py` — RAG pipeline: retrieve → prompt → generate (session-scoped)
- `app/chunking.py` — Split text into overlapping chunks
- `app/loaders.py` — Load PDF, TXT, MD from file or directory
- `app/ingest.py` — Ingest pipeline: load → chunk → upsert (re-ingest replaces by source)
- `app/session_db.py` — SQLite session tracking and TTL expiry
- `vector_store/` — Chroma persistence (created on first use)
- `data/` — Staged uploads (optional)
- `streamlit_app.py` — Streamlit UI: session ID, multi-file upload, auto-ingest (single flow), query, chat history, “Start new session”
- `tests/` — Pytest: chunking, loaders, ingest, ingest batch, single-flow fingerprint, store, llm, query, session isolation, TTL cleanup, dedup, advanced options, chat history

## Tests

From project root:

```bash
python -m pytest tests/ -v
```

Requires Ollama running for `test_store.py`; other tests use mocks.