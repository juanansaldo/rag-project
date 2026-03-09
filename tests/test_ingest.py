from pathlib import Path
from unittest.mock import patch

from app.ingest import ingest_file


def test_ingest_file_calls_add_batch(tmp_path):
    (tmp_path / "doc.txt").write_text("The secret code is 42.")
    with patch("app.ingest.add_batch") as mock_add:
        n = ingest_file(tmp_path / "doc.txt")
    mock_add.assert_called_once()
    call_args = mock_add.call_args
    ids, texts, metadatas = call_args[0]
    assert len(ids) == n
    assert n >= 1
    assert any("secret" in t.lower() or "42" in t for t in texts)
    for m in metadatas:
        assert "source" in m
        assert "page" in m
        assert "index" in m


def test_ingest_file_forwards_chunk_params(tmp_path: Path):
    f = tmp_path / "doc.txt"
    f.write_text("hello world", encoding="utf-8")

    with patch("app.ingest.chunk_text") as mock_chunk_text, patch(
        "app.ingest.add_batch"
    ) as mock_add_batch, patch("app.ingest.delete_session_source"):
        mock_chunk_text.return_value = [
            {"text": "hello world", "source": "doc.txt", "index": 0}
        ]

        n = ingest_file(
            f,
            session_id="sess-1",
            chunk_size=123,
            chunk_overlap=7,
        )

    mock_chunk_text.assert_called_once()
    args, kwargs = mock_chunk_text.call_args
    assert kwargs["chunk_size"] == 123
    assert kwargs["chunk_overlap"] == 7
    mock_add_batch.assert_called_once()
    assert n == 1

