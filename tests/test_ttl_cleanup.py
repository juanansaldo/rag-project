from unittest.mock import patch

from app.main import _cleanup_expired_sessions


def test_cleanup_expired_sessions_deletes_from_store_and_db():
    expired = ["s1", "s2", "s3"]

    with patch("app.main.get_expired_sessions", return_value=expired) as mock_get, patch(
        "app.main.delete_session"
    ) as mock_delete_store, patch("app.main.remove_session") as mock_remove_db:
        removed_count = _cleanup_expired_sessions()

    mock_get.assert_called_once()
    assert removed_count == 3
    assert mock_delete_store.call_count == 3
    assert mock_remove_db.call_count == 3
    mock_delete_store.assert_any_call("s1")
    mock_remove_db.assert_any_call("s1")