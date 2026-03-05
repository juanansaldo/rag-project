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