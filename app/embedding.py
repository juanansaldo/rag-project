import ollama
from app.config import EMBEDDING_MODEL, OLLAMA_BASE_URL

def embed(text: str) -> list[float]:
    """Embed a single string. Returns a list of floats."""
    client = ollama.Client(host=OLLAMA_BASE_URL)
    out = client.embeddings(model=EMBEDDING_MODEL, prompt=text)
    return out["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple strings. Returns a list of embedding vectors."""
    return [embed(t) for t in texts]