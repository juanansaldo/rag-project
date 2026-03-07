from unittest.mock import patch

from app.ingest import ingest_file


def test_ingest_file_generates_stable_ids_for_same_content(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Hello world.\nThis is a stable chunk test.")

    with patch("app.ingest.delete_session_source"), patch("app.ingest.add_batch") as mock_add:
        n1 = ingest_file(f, session_id="s1")
        args1, kwargs1 = mock_add.call_args
        ids1, texts1, metas1 = args1
        
        n2 = ingest_file(f, session_id="s1")
        args2, kwargs2 = mock_add.call_args
        ids2, texts2, metas2 = args2

    assert n1 >= 1
    assert n2 >= 1
    assert ids1 == ids2
    assert texts1 == texts2
    assert metas1 == metas2
    assert kwargs1["session_id"] == "s1"
    assert kwargs2["session_id"] == "s1"


def test_ingest_file_replaces_source_before_upsert(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Version A text.")

    with patch("app.ingest.delete_session_source") as mock_delete, patch("app.ingest.add_batch"):
        ingest_file(f, session_id="s2")
    
    mock_delete.assert_called_once_with(session_id="s2", source="doc.txt")