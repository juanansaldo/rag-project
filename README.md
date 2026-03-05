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