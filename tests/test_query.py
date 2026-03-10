from unittest.mock import patch

from app.query import rag_query


def test_rag_query_empty_retrieval():
    with patch("app.query.search", return_value=[]):
        result = rag_query("Anything?")
    assert "answer" in result
    assert "sources" in result
    assert result["sources"] == []
    assert "no relevant" in result["answer"].lower() or "ingest" in result["answer"].lower()


def test_rag_query_with_hits_returns_answer_and_sources():
    fake_hits = [
        {"document": "Paris is the capital of France.", "metadata": {"source": "doc.txt"}, "distance": 0.1},
    ]
    with patch("app.query.search", return_value=fake_hits), patch(
        "app.query.generate", return_value=f"Paris is the capital of France."
    ):
        result = rag_query("What is the capital of France?")
    assert result["answer"] == "Paris is the capital of France."
    assert len(result["sources"]) == 1
    assert "Paris" in result["sources"][0]["document"]
    assert result["sources"][0]["metadata"]["source"] == "doc.txt"


def test_rag_query_uses_top_k_override():
    fake_hits = [
        {"document": "doc1", "metadata": {"source": "a.txt"}, "distance": 0.1}
    ]

    with patch("app.query.search", return_value=fake_hits) as mock_search, patch(
        "app.query.generate", return_value="answer"
    ):
        rag_query("question", session_id="sess-1", top_k=7)

    mock_search.assert_called_once()
    _, kwargs = mock_search.call_args
    assert kwargs["top_k"] == 7
    assert kwargs["session_id"] == "sess-1"


def test_rag_query_passes_model_to_generate():
    fake_hits = [
        {"document": "Some context.", "metadata": {"source": "x.txt"}, "distance": 0.1},
    ]
    with patch("app.query.search", return_value=fake_hits), patch(
        "app.query.generate", return_value="answer"
    ) as mock_generate:
        rag_query("question", session_id="s1", model="phi3")

    mock_generate.assert_called_once()
    _, kwargs = mock_generate.call_args
    assert kwargs["model"] == "phi3"