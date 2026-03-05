from pathlib import Path

from app.chunking import chunk_text
from app.loaders import load_document, load_directory
from app.store import add_batch


def ingest_file(path: str | Path) -> int:
    """Load one file, chunk, add to store. Returns number of chunks added."""
    pages = load_document(path)
    ids = []
    texts = []
    metadatas = []
    for p in pages:
        source = p["source"]
        page = p["page"]
        for c in chunk_text(p["text"], source=source):
            chunk_id = f"{source}_{page}_{c['index']}"
            ids.append(chunk_id)
            texts.append(c["text"])
            metadatas.append({"source": source, "page": str(page), "index": str(c["index"])})
        if ids:
            add_batch(ids, texts, metadatas)
        return len(ids)


def ingest_directory(dir_path: str | Path) -> int:
    """Load all supported files from directory, chunk, add to store. Returns total chunks added."""
    dir_path = Path(dir_path)
    total = 0
    for ext in ("*.txt", "*.md", "*.pdf"):
        for f in dir_path.glob(ext):
            total += ingest_file(f)
    return total