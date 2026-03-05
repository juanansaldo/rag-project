# RAG Project

A retrieval-augmented generation (RAG) API: ingest documents, then ask questions and get answers grounded in stored content. Uses open-source models via Ollama (embeddings + LLM) and Chroma for the vector store.

## Stack

- **API:** FastAPI
- **Embeddings:** Ollama (`nomic-embed-text`)
- **Vector store:** Chroma (persistent, cosine similarity)
- **LLM:** Mistral 7B (Ollama)

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

   Edit `.env` to change `VECTOR_STORE_PATH`, `CHUNK_SIZE`, `TOP_K`, etc.

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

## API

- **GET /health** — Liveness check; returns `{"status": "ok"}`.
- **POST /ingest/file** — Upload a document (PDF, TXT, or MD). Send as **form-data** with key `file` and value = your file. Returns `{"ok": true, "chunks_added": n}`.

  Example in Postman: Body → form-data → key `file` (type: File) → select a file.

- **POST /query** — Ask a question. Body: JSON `{"question": "..."}`. Returns `{"answer": "...", "sources": [...]}` (each source has `document` snippet and `metadata`).

  Example in Postman: Body → raw → JSON → `{"question": "What is in the document?"}`

## Project layout

- `app/main.py` — FastAPI app (health, ingest/file, query)
- `app/config.py` — Settings from env
- `app/embedding.py` — Text to vector via Ollama
- `app/store.py` — Chroma: add chunks, search by similarity
- `app/llm.py` — Call Mistral via Ollama for generation
- `app/query.py` — RAG pipeline: retrieve → prompt → generate
- `app/chunking.py` — Split text into overlapping chunks
- `app/loaders.py` — Load PDF, TXT, MD from file or directory
- `app/ingest.py` — Ingest pipeline: load → chunk → add to store
- `vector_store/` — Chroma persistence (created on first use)
- `data/` — Uploaded documents (optional; add sample files here)
- `tests/` — Pytest tests (chunking, loaders, ingest, store, llm, query)

## Tests

From project root (with Ollama running):

```bash
python -m pytest tests/ -v
```

Requires Ollama running for `test_store.py`; other tests use mocks.