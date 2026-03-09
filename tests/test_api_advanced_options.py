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