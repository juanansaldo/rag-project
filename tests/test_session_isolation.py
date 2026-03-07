from unittest.mock import patch

from app.config import TOP_K
from app.query import rag_query


def test_rag_query_passes_session_id_to_search():
    fake_hits = [{"document": "Only session A doc", "metadata": {"source": "a.txt"}, "distance": 0.1}]

    with patch("app.query.search", return_value=fake_hits) as mock_search, patch(
        "app.query.generate", return_value="Only session A doc"
    ):
        result = rag_query("question", session_id="session-A")

    mock_search.assert_called_once_with("question", top_k=TOP_K, session_id="session-A")
    assert result["answer"] == "Only session A doc"
    assert result["sources"][0]["metadata"]["source"] == "a.txt"