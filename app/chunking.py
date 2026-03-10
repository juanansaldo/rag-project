from app.config import CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS


def chunk_text(
    text: str,
    source: str = "",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    by_words: bool = False,
) -> list[dict]:
    """
    Split text into overlapping chunks. Returns list of {"text": ..., "source": ..., "index": ...}.
    If by_words is False (default), uses character count. If by_words is True, uses word count.
    """
    if not text or not text.strip():
        return []

    if by_words:
        size = chunk_size if chunk_size is not None else CHUNK_SIZE_WORDS
        overlap = chunk_overlap if chunk_overlap is not None else CHUNK_OVERLAP_WORDS
        words = text.strip().split()
        chunks: list[dict] = []
        index, start = 0, 0
        step = max(1, size - overlap)
        while start < len(words):
            end = min(start + size, len(words))
            chunk_words = words[start:end]
            chunk_str = " ".join(chunk_words)
            if chunk_str.strip():
                chunks.append({"text": chunk_str.strip(), "source": source, "index": index})
                index += 1
            start += step
        return chunks

    size = chunk_size if chunk_size is not None else CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else CHUNK_OVERLAP
    text = text.strip()
    chunks: list[dict] = []
    start, index = 0, 0
    while start < len(text):
        end = start + size
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append({"text": chunk_text.strip(), "source": source, "index": index})
            index += 1
        start = end - overlap
        if start >= len(text):
            break
    return chunks