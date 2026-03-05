import chromadb
from pathlib import Path

from app.config import VECTOR_STORE_PATH, TOP_K
from app.embedding import embed

# Persist under project root; Chroma creates the directory
_path = VECTOR_STORE_PATH
_path.mkdir(parents=True, exist_ok=True)

_client = chromadb.PersistentClient(path=str(_path))
_collection = _client.get_or_create_collection(name="rag", metadata={"hnsw:space": "cosine"})


def add(id: str, text: str, metadata: dict | None = None):
    """Store one document chunk: embed and add to Chroma"""
    vector = embed(text)
    meta = metadata if metadata else {"_": 0}
    _collection.add(ids=[id], embeddings=[vector], documents=[text], metadatas=[meta])


def add_batch(ids: list[str], texts: list[str], metadatas: list[dict] | None = None):
    """Store multiple chunks: Metadatas can be a list of dicts (one per chunk) or None."""
    vectors = [embed(t) for t in texts]
    _collection.add(
        ids=ids,
        embeddings=vectors,
        documents=texts,
        metadatas=[m if m else {"_": 0} for m in (metadatas or [{}] * len(texts))],
    )


def search(query: str, top_k: int | None = None) -> list[dict]:
    """Return top_k chunks for the query. Each item has 'document', 'metadata', 'distance'."""
    k = top_k if top_k is not None else TOP_K
    qvec = embed(query)
    results = _collection.query(
        query_embeddings=[qvec],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    out = []
    for i, doc in enumerate(results["documents"][0]):
        out.append({
            "document": doc,
            "metadata": (results["metadatas"][0] or [{}])[i],
            "distance": (results["distances"][0] or [0])[i],
        })
    return out