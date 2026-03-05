from pathlib import Path
from fastapi import FastAPI, UploadFile, File

from app.ingest import ingest_file

app = FastAPI(title="RAG API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest/file")
async def ingest_upload(file: UploadFile = File(...)):
    """Upload a single file (PDF, TXT, MD); chunk and add to vector store."""
    if not file.filename:
        return {"ok": False, "error": "No filename"}
    path = Path("data") / file.filename
    path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    path.write_bytes(content)
    try:
        n = ingest_file(path)
        return {"ok": True, "chunks_added": n}
    except Exception as e:
        return {"ok": False, "error": str(e)}