from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, source: str = "") -> list[dict]:
    """
    Split text into overlapping chunks. Returns list of {"text": ..., "source": ..., "index": ...}.
    Uses character count as a simple proxy for token count.
    """
    if not text or not text.strip():
        return []
    text = text.strip()
    chunks = []
    start = 0
    index = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append({"text": chunk_text.strip(), "source": source, "index": index})
            index += 1
        start = end - CHUNK_OVERLAP
        if start >= len(text):
            break;
    return chunks