from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Header, HTTPException

from app.ingest import ingest_file
from app.query import rag_query
from app.sessions import touch_session, maybe_get_expired_sessions, remove_session_tracking
from app.store import delete_session

app = FastAPI(title="RAG API")


def _run_ttl_cleanup():
    expired = maybe_get_expired_sessions()
    for sid in expired:
        delete_session(sid)


def _require_session_id(x_session_id: str | None) -> str:
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-ID header")
    return x_session_id


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest/file")
async def ingest_upload(
    file: UploadFile = File(...),
    x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
):
    """Upload a single file (PDF, TXT, MD); chunk and add to vector store."""
    _run_ttl_cleanup()
    session_id = _require_session_id(x_session_id)
    touch_session(session_id)

    if not file.filename:
        return {"ok": False, "error": "No filename"}
    
    path = Path("data") / file.filename
    path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    path.write_bytes(content)
    
    try:
        n = ingest_file(path, session_id=session_id)
        return {"ok": True, "chunks_added": n}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(req: QueryRequest, x_session_id: str | None = Header(default=None, alias="X-Session-ID")):
    """Ask a question; returns answer and source chunks."""
    _run_ttl_cleanup()
    session_id = _require_session_id(x_session_id)
    touch_session(session_id)

    try:
        return rag_query(req.question, session_id=session_id)
        
    except Exception as e:
        return {"answer": "", "sources": [], "error": str(e)}


@app.delete("/session")
def clear_session(x_session_id: str | None = Header(default=None, alias="X-Session-ID")):
    session_id = _require_session_id(x_session_id)
    removed = delete_session(session_id)
    remove_session_tracking(session_id)
    return {"ok": True, "deleted_chunks": removed}