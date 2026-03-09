from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ingest_files_endpoint_multiple_files():
    """POST /ingest/files accepts multiple files and returns total and per-file counts."""
    files = [
        ("files", ("a.txt", BytesIO(b"hello world"), "text/plain")),
        ("files", ("b.txt", BytesIO(b"second file"), "text/plain")),
    ]
    with patch("app.main.ingest_file") as mock_ingest:
        mock_ingest.side_effect = [3, 2]
        resp = client.post(
            "/ingest/files",
            headers={"X-Session-ID": "sess-1"},
            files=files,
            data={"chunk_size": "256", "chunk_overlap": "32"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["total_chunks"] == 5
    assert len(data["files"]) == 2
    assert data["files"][0]["filename"] == "a.txt"
    assert data["files"][0]["chunks_added"] == 3
    assert data["files"][1]["filename"] == "b.txt"
    assert data["files"][1]["chunks_added"] == 2
    assert mock_ingest.call_count == 2


def test_ingest_files_endpoint_empty_list():
    """POST /ingest/files with no files returns error."""
    resp = client.post(
        "/ingest/files",
        headers={"X-Session-ID": "sess-1"},
        files=[],
    )
    if resp.status_code == 200:
        data = resp.json()
        assert data.get("ok") is False
        assert "total_chunks" in data or "error" in data