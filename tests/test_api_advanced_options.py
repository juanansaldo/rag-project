from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ingest_endpoint_passes_chunk_params():
    fake_file = BytesIO(b"hello world")
    with patch("app.main.ingest_file", return_value=3) as mock_ingest:
        resp = client.post(
            "/ingest/file",
            headers={"X-Session-ID": "sess-1"},
            files={"file": ("doc.txt", fake_file, "text/plain")},
            data={"chunk_size": "256", "chunk_overlap": "32"},
        )

    assert resp.status_code == 200
    mock_ingest.assert_called_once()
    _, kwargs = mock_ingest.call_args
    assert kwargs["session_id"] == "sess-1"
    assert kwargs["chunk_size"] == 256
    assert kwargs["chunk_overlap"] == 32


def test_query_endpoint_passes_top_k():
    with patch("app.main.rag_query", return_value={"answer": "a", "sources": []}) as mock_rag:
        resp = client.post(
            "/query",
            headers={"X-Session-ID": "sess-1"},
            json={"question": "q", "top_k": 9},
        )
    
    assert resp.status_code == 200
    mock_rag.assert_called_once()
    _, kwargs = mock_rag.call_args
    assert kwargs["top_k"] == 9
    assert kwargs["session_id"] == "sess-1"


def test_query_endpoint_passes_model():
    with patch("app.main.rag_query", return_value={"answer": "a", "sources": []}) as mock_rag:
        resp = client.post(
            "/query",
            headers={"X-Session-ID": "sess-1"},
            json={"question": "q", "model": "gemma2"},
        )

    assert resp.status_code == 200
    mock_rag.assert_called_once()
    _, kwargs = mock_rag.call_args
    assert kwargs["model"] == "gemma2"


def test_delete_session_endpoint_returns_ok():
    """DELETE /session (used by 'Start new session' confirmation) returns success."""
    with patch("app.main.delete_session", return_value=0) as mock_delete, patch(
        "app.main.remove_session"
    ) as mock_remove:
        resp = client.delete(
            "/session",
            headers={"X-Session-ID": "sess-to-clear"},
        )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "deleted_chunks" in data
    mock_delete.assert_called_once_with("sess-to-clear")
    mock_remove.assert_called_once_with("sess-to-clear")