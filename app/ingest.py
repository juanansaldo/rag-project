from pathlib import Path
import uuid

from app.chunking import chunk_text
from app.loaders import load_document
from app.store import add_batch


def ingest_file(path: str | Path, session_id: str = "default") -> int:
    """Load one file, chunk, add to store. Returns number of chunks added."""
    pages = load_document(path)
    ids, texts, metadatas = [], [], []

    for p in pages:
        source = p["source"]
        page = p["page"]
        for c in chunk_text(p["text"], source=source):
            chunk_id = f"{session_id}_{source}_{page}_{c['index']}_{uuid.uuid4().hex[:8]}"
            ids.append(chunk_id)
            texts.append(c["text"])
            metadatas.append({"source": source, "page": str(page), "index": str(c["index"])})
    
    if ids:
        add_batch(ids, texts, metadatas, session_id=session_id)
    
    return len(ids)


def ingest_directory(dir_path: str | Path, session_id: str = "default") -> int:
    """Load all supported files from directory, chunk, add to store. Returns total chunks added."""
    dir_path = Path(dir_path)
    total = 0
    for ext in ("*.txt", "*.md", "*.pdf"):
        for f in dir_path.glob(ext):
            total += ingest_file(f, session_id=session_id)
    return total