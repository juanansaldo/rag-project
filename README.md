# RAG Project

A retrieval-augmented generation (RAG) API: ingest documents, then ask questions and get answers grounded in stored content. Uses open-source models via Ollama (embeddings + LLM) and Chroma for the vector store. Data is isolated per session and expires after a configurable TTL. Advanced options let you tune chunking and retrieval per session. The React UI keeps a chat-style history of questions and answers for the current session, supports uploading multiple documents at once, and uses a single flow: when you select files, ingest runs **in the background** so you can type and submit a question immediately; if ingest is still running when you click Ask, the app waits for it to finish before running the query. Supported formats: PDF, TXT, MD, HTML, CSV, and DOCX.

## Stack

- **API:** FastAPI
- **Embeddings:** Ollama (`nomic-embed-text`)
- **Vector store:** Chroma (persistent, cosine similarity)
- **LLM:** Ollama (default model set by `LLM_MODEL`; UI and API can override with any Ollama model, e.g. mistral, llama3.2, phi3)
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

   Edit `.env` for `VECTOR_STORE_PATH`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `CHUNK_SIZE_WORDS`, `CHUNK_OVERLAP_WORDS`, `TOP_K`, `LLM_MODEL`, `SESSION_TTL_SECONDS`, `SESSION_CLEANUP_INTERVAL_SECONDS`, etc.

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

5. Start the React frontend to upload docs and ask questions in the browser:

   ```bash
   cd frontend && npm install && npm run dev
   ```

   Open http://localhost:5173. Keep the API running (step 4). The dev server proxies `/api` to the backend. For production, set `VITE_API_URL` to your API base URL and serve the built `frontend/dist` from your host.

## Session isolation & TTL

- Every **ingest** and **query** request must send the header **`X-Session-ID`** (any string, e.g. a UUID). All chunks are stored and searched per session; users only see their own documents.
- **TTL:** Sessions that receive no requests for `SESSION_TTL_SECONDS` (default 1800) are removed automatically. A background task runs every `SESSION_CLEANUP_INTERVAL_SECONDS` (default 30).
- **Deduplication:** Re-ingesting the same file in a session replaces that source’s chunks (no duplicates).
- **DELETE /session** clears the current session’s data (used by “Start new session” in the UI).

## Per-session advanced options

The React UI has an **Options** panel (left sidebar) that controls behavior **per browser session**:

- **Chunk by:** Toggle between **Characters** and **Words**.
  - **Characters (default):** Chunk by character count. Defaults: chunk size `CHUNK_SIZE` (e.g. 512), overlap `CHUNK_OVERLAP` (e.g. 100).
  - **Words:** Chunk by word count. Defaults: chunk size `CHUNK_SIZE_WORDS` (e.g. 100), overlap `CHUNK_OVERLAP_WORDS` (e.g. 20). When you switch to Words, the UI resets size/overlap to these defaults.
- **Chunk size:** Maximum length per chunk (in characters or words, depending on mode). Labels and ranges update with the selected mode.
- **Chunk overlap:** Overlap between neighboring chunks (same unit as chunk size). Clamped so overlap < chunk size.
- **Top K:** Number of chunks retrieved per query. Defaults to `TOP_K`.
- **LLM model:** Ollama model used for generating answers (e.g. mistral, llama3.2, llama3.1, phi3, gemma2). Defaults to `LLM_MODEL` from `.env` if it’s in the list; otherwise mistral.

These settings:

- Apply only to the current session’s uploads and questions.
- Are sent to the FastAPI backend on each ingest/query and override the config defaults.
- Reset only when you change them or restart the browser tab (the session’s data still respects TTL and `/session` deletion).

## Supported file types

The ingest pipeline accepts:

- **PDF** — One item per page; text extracted via pypdf.
- **TXT, MD** — Read as plain text (UTF-8).
- **HTML** — Tags stripped; text content extracted for chunking.
- **CSV** — Rows flattened to a single text block (one line per row).
- **DOCX** — Paragraph text extracted via python-docx.

The API rejects other extensions with `Unsupported file type`. The UI file picker is limited to these types.

## Single-flow upload and background ingest

In the React UI, **ingest runs automatically in the background** when you choose one or more files via the + button. There is no separate “Ingest” button: once you select files, the app starts ingest and you can use the query box right away. If you submit a question while ingest is still running, the app waits for ingest to complete before running the RAG query. When ingest finishes, uploaded documents appear as tabs above the query box. The same selection is not re-ingested; change the selection or click “Start new session” to ingest again. Flow: select files → (background ingest) → ask questions anytime; query step waits for ingest when needed.

## Chat history

The React UI shows all questions and answers for the current browser session. Each entry displays the question, the answer, and expandable sources. History is kept in memory only (per tab) and is cleared when you click **“Start new session”**; it is not sent to or stored by the API.

## API

- **GET /health** — Liveness check; returns `{"status": "ok"}`.

- **POST /ingest/file** — Upload a single document (PDF, TXT, MD, HTML, CSV, or DOCX). Send as **form-data** with key `file`. Include header **`X-Session-ID`**. Optional form fields: `chunk_size`, `chunk_overlap`, `chunk_by_words` (`"true"` or `"false"` for word-based chunking). Returns `{"ok": true, "chunks_added": n}`.

  Example in Postman: Body → form-data → key `file` (type: File) → select a file; add header `X-Session-ID: your-session-id`.

- **POST /ingest/files** — Upload multiple documents in one request (same formats as above). Send as **form-data** with key `files` (multiple file parts). Include header **`X-Session-ID`**. Optional form fields: `chunk_size`, `chunk_overlap`, `chunk_by_words` (`"true"` or `"false"` for word-based chunking). Returns `{"ok": true, "total_chunks": n, "files": [{"filename": "...", "chunks_added": k}, ...]}`. The React UI uses this for multi-file upload.

- **POST /query** — Ask a question. Body: JSON `{"question": "...", "top_k": optional int, "model": optional str}`. `model` is the Ollama model name (e.g. mistral, llama3.2). Include header **`X-Session-ID`**. Returns `{"answer": "...", "sources": [...]}` (each source has `document` snippet and `metadata`).

  Example in Postman: Body → raw → JSON → `{"question": "What is in the document?"}`; add header `X-Session-ID: your-session-id`.

- **DELETE /session** — Delete the session’s chunks and tracking. Include header **`X-Session-ID`**. Returns `{"ok": true, "deleted_chunks": n}`.

## Project layout

- `app/main.py` — FastAPI app (health, ingest/file, ingest/files, query, DELETE session), lifespan cleanup
- `app/config.py` — Settings from env
- `app/embedding.py` — Text to vector via Ollama
- `app/store.py` — Chroma: add/upsert chunks, search by similarity, delete by session/source
- `app/llm.py` — Ollama chat for generation (model configurable via config or request)
- `app/query.py` — RAG pipeline: retrieve → prompt → generate (session-scoped)
- `app/chunking.py` — Split text into overlapping chunks (character-based or word-based; configurable size/overlap)
- `app/loaders.py` — Load PDF, TXT, MD, HTML, CSV, DOCX from file or directory
- `app/ingest.py` — Ingest pipeline: load → chunk → upsert (re-ingest replaces by source)
- `app/session_db.py` — SQLite session tracking and TTL expiry
- `vector_store/` — Chroma persistence (created on first use)
- `data/` — Staged uploads (optional)
- `frontend/` — React (Vite) UI: session, Options sidebar (chunk by characters/words, chunk size/overlap, top K, LLM model), upload (+ button), background ingest, query, chat history, "Start new session". Run `npm run dev` in `frontend/` and open http://localhost:5173
- `tests/` — Pytest: chunking (character + word mode), loaders, ingest, ingest batch, single-flow fingerprint, store, llm (including model override), query, session isolation, TTL cleanup, dedup, advanced options, chat history

## Tests

From project root:

```bash
python -m pytest tests/ -v
```

Requires Ollama running for `test_store.py`; other tests use mocks.