from pathlib import Path
import hashlib

from app.chunking import chunk_text
from app.loaders import load_document
from app.store import add_batch, delete_session_source


def ingest_file(
    path: str | Path, 
    session_id: str = "default",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """Load one file, chunk, add to store. Returns number of chunks added."""
    pages = load_document(path)

    if not pages:
        return 0

    source_name = pages[0]["source"]
    delete_session_source(session_id=session_id, source=source_name)
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    for p in pages:
        source = p["source"]
        page = p["page"]
        for c in chunk_text(
            p["text"], 
            source=source,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        ):
            text = c["text"]
            fingerprint = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
            chunk_id = f"{session_id}:{source}:{page}:{c['index']}:{fingerprint}"
            ids.append(chunk_id)
            texts.append(text)
            metadatas.append({"source": source, "page": str(page), "index": str(c["index"])})
    
    if ids:
        add_batch(ids, texts, metadatas, session_id=session_id)
    
    return len(ids)


def ingest_directory(
    dir_path: str | Path, 
    session_id: str = "default",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """Load all supported files from directory, chunk, add to store. Returns total chunks added."""
    dir_path = Path(dir_path)
    total = 0
    for ext in ("*.txt", "*.md", "*.pdf"):
        for f in dir_path.glob(ext):
            total += ingest_file(
                f,
                session_id=session_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
    return total