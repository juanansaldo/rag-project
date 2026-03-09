from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(
    text: str,
    source: str = "",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict]:
    """
    Split text into overlapping chunks. Returns list of {"text": ..., "source": ..., "index": ...}.
    Uses character count. If chunk_size/chunk_overlap are None, uses config defaults.
    """
    if not text or not text.strip():
        return []

    size = chunk_size if chunk_size is not None else CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else CHUNK_OVERLAP

    text = text.strip()
    chunks: list[dict] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + size
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append({"text": chunk_text.strip(), "source": source, "index": index})
            index += 1
        start = end - overlap
        if start >= len(text):
            break;

    return chunks