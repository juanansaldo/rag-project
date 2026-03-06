import chromadb

from app.config import VECTOR_STORE_PATH, TOP_K
from app.embedding import embed

# Persist under project root; Chroma creates the directory
_path = VECTOR_STORE_PATH
_path.mkdir(parents=True, exist_ok=True)

_client = chromadb.PersistentClient(path=str(_path))
_collection = _client.get_or_create_collection(name="rag", metadata={"hnsw:space": "cosine"})


def add(id: str, text: str, metadata: dict | None = None, session_id: str = "default"):
    """Store one document chunk: embed and add to Chroma"""
    vector = embed(text)
    meta = dict(metadata or {})
    meta["session_id"] = session_id
    if not meta:
        meta = {"_": 0}
    _collection.add(ids=[id], embeddings=[vector], documents=[text], metadatas=[meta])


def add_batch(
    ids: list[str], 
    texts: list[str], 
    metadatas: list[dict] | None = None,
    session_id: str = "default",    
):
    """Store multiple chunks: Metadatas can be a list of dicts (one per chunk) or None."""
    vectors = [embed(t) for t in texts]
    base_metas = metadatas or [{}] * len(texts)
    final_metas = []
    for m in base_metas:
        mm = dict(m or {})
        mm["session_id"] = session_id
        if not mm:
            mm = {"_": 0}
        final_metas.append(mm)

    _collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=final_metas)


def search(query: str, top_k: int | None = None, session_id: str = "default") -> list[dict]:
    """Return top_k chunks for the query. Each item has 'document', 'metadata', 'distance'."""
    k = top_k if top_k is not None else TOP_K
    qvec = embed(query)
    results = _collection.query(
        query_embeddings=[qvec],
        n_results=k,
        where={"session_id": session_id},
        include=["documents", "metadatas", "distances"]
    )

    docs = results.get("documents", [])
    if not docs or not docs[0]:
        return []

    out = []
    for i, doc in enumerate(docs[0]):
        out.append({
            "document": doc,
            "metadata": (results.get("metadatas", [[]])[0] or [{}])[i],
            "distance": (results.get("distances", [[]])[0] or [0])[i],
        })
    return out


def delete_session(session_id: str) -> int:
    res = _collection.get(where={"session_id": session_id})
    ids = res.get("ids", []) if res else []
    if ids:
        _collection.delete(ids=ids)
    return len(ids)