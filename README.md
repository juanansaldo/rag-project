# RAG Project

A retrieval-augmented generation (RAG) API: ingest documents, then ask questions and get answers grounded in stored content. Uses open-source models via Ollama (embeddings + LLM) and Chroma for the vector store.

## Stack

- **API:** FastAPI
- **Embeddings:** Ollama (`nomic-embed-text`)
- **Vector store:** Chroma (persistent, cosine similarity)
- **LLM:** Mistral 7B (Ollama) — to be wired in for query step

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

## Project layout

- `app/main.py` — FastAPI app (health check; ingest/query routes to come)
- `app/config.py` — Settings from env
- `app/embedding.py` — Text to vector via Ollama
- `app/store.py` — Chroma: add chunks, search by similarity
- `vector_store/` — Chroma persistence (created on first use)
- `data/` — Documents to ingest (to be used by ingest pipeline)

## Tests

From project root (with Ollama running):

```bash
python -m pytest tests/ -v
```