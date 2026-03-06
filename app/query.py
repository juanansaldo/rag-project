from app.config import TOP_K
from app.llm import generate
from app.store import search

SYSTEM_PROMPT = """Answer only using the context below. If the answer is not in the context, say
    "I don't see that in the documents." Do not make up information."""


def rag_query(question: str, session_id: str = "default", top_k: int | None = None) -> dict:
    """Run RAG: retrieve chunks, then generate answer. Returns {"answer": str, "sources": list}."""
    k = top_k if top_k is not None else TOP_K
    hits = search(question, top_k=k, session_id=session_id)
    if not hits:
        return {"answer": "No relevant documents found. Ingest some documents first.", "sources": []}
    context = "\n\n---\n\n".join(h["document"] for h in hits)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    answer = generate(SYSTEM_PROMPT, user_prompt)
    sources = [{"document": h["document"][:200], "metadata": h["metadata"]} for h in hits]
    return {"answer": answer, "sources": sources}