import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Form

from app.config import SESSION_TTL_SECONDS, SESSION_CLEANUP_INTERVAL_SECONDS
from app.ingest import ingest_file
from app.query import rag_query
from app.session_db import touch_session, get_expired_sessions, remove_session
from app.store import delete_session


def _require_session_id(x_session_id: str | None) -> str:
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-ID header")
    return x_session_id


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".csv", ".docx"}


def _cleanup_expired_sessions() -> int:
    """Delete expired sessions from vector store and session DB."""
    expired = get_expired_sessions(SESSION_TTL_SECONDS)
    for sid in expired:
        delete_session(sid)  # Remove chunks from Chroma
        remove_session(sid)  # Remove tracking row from SQLite
    return len(expired)


async def _cleanup_loop() -> None:
    while True:
        try:
            _cleanup_expired_sessions()
        except Exception as e:
            print(f"[cleanup_loop] cleanup failed: {e}")
        await asyncio.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: cleanup once (handles stal sessions after restarts)
    try:
        _cleanup_expired_sessions()
    except Exception as e:
        print(f"[lifespan] startup cleanup failed: {e}")
        
    #Background periodic cleanup
    task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="RAG API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest/file")
async def ingest_upload(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    chunk_size: int | None = Form(default=None),
    chunk_overlap: int | None = Form(default=None),
):
    """Upload a single file (PDF, TXT, MD); chunk and add to vector store."""
    session_id = _require_session_id(x_session_id)
    touch_session(session_id)

    if not file.filename:
        return {"ok": False, "error": "No filename"}

    path = Path("data") / file.filename
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return {"ok": False, "error": f"Unsupported file type: {path.suffix}"}

    path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    path.write_bytes(content)
    
    try:
        n = ingest_file(
            path,
            session_id=session_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return {"ok": True, "chunks_added": n}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/ingest/files")
async def ingest_upload_batch(
    files: list[UploadFile] = File(default=[]),
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    chunk_size: int | None = Form(default=None),
    chunk_overlap: int | None = Form(default=None),
):
    """Upload multiple files (PDF, TXT, MD); chunk and add to vector store. Returns total and per-file counts."""
    session_id = _require_session_id(x_session_id)
    touch_session(session_id)

    if not files:
        return {"ok": False, "error": "No files", "total_chunks": 0, "files": []}

    total_chunks = 0
    file_results = []

    for file in files:
        if not file.filename:
            file_results.append({"filename": "", "chunks_added": 0, "error": "No filename"})
            continue
        
        path = Path("data") / file.filename
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            file_results.append({
                "filename": file.filename,
                "chunks_added": 0,
                "error": f"Unsupported file type: {path.suffix}",
            })
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        path.write_bytes(content)
        try:
            n = ingest_file(
                path,
                session_id=session_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            total_chunks += n
            file_results.append({"filename": file.filename, "chunks_added": n})
        except Exception as e:
            file_results.append({"filename": file.filename, "chunks_added": 0, "error": str(e)})
    
    return {"ok": True, "total_chunks": total_chunks, "files": file_results}


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


@app.post("/query")
def query(req: QueryRequest, x_session_id: str | None = Header(default=None, alias="X-Session-ID")):
    """Ask a question; returns answer and source chunks."""
    session_id = _require_session_id(x_session_id)
    touch_session(session_id)

    try:
        return rag_query(req.question, session_id=session_id, top_k=req.top_k)
        
    except Exception as e:
        return {"answer": "", "sources": [], "error": str(e)}


@app.delete("/session")
def clear_session(x_session_id: str | None = Header(default=None, alias="X-Session-ID")):
    session_id = _require_session_id(x_session_id)
    removed = delete_session(session_id)
    remove_session(session_id)
    return {"ok": True, "deleted_chunks": removed}