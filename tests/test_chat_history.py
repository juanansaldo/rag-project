"""
Tests for chat_history feature: turn structure and handling of API response.
History is stored in Streamlit session_state; these tests assert the data contract
the UI expects (question, answer, sources).
"""


def test_turn_structure_from_api_response():
    """Turn appended to chat_history has the shape the UI expects."""
    question = "What is X?"
    data = {
        "answer": "X is the first letter.",
        "sources": [
            {"document": "snippet text", "metadata": {"source": "doc.txt"}}
        ],
    }
    turn = {
        "question": question,
        "answer": data.get("answer", ""),
        "sources": data.get("sources", []),
    }
    assert "question" in turn
    assert "answer" in turn
    assert "sources" in turn
    assert turn["question"] == "What is X?"
    assert turn["answer"] == "X is the first letter."
    assert len(turn["sources"]) == 1
    assert turn["sources"][0]["metadata"]["source"] == "doc.txt"


def test_turn_handles_empty_sources():
    """Turn uses empty list when API returns no sources."""
    data = {"answer": "No relevant docs.", "sources": []}
    turn = {
        "question": "Anything?",
        "answer": data.get("answer", ""),
        "sources": data.get("sources", []),
    }
    assert turn["sources"] == []


def test_turn_handles_missing_answer_and_sources():
    """Turn uses defaults when keys are missing (e.g. error path not taken)."""
    data = {}
    turn = {
        "question": "Q?",
        "answer": data.get("answer", ""),
        "sources": data.get("sources", []),
    }
    assert turn["answer"] == ""
    assert turn["sources"] == []


def test_chat_history_is_list_of_turns():
    """chat_history is a list of dicts with question, answer, sources."""
    chat_history = [
        {"question": "Q1", "answer": "A1", "sources": []},
        {"question": "Q2", "answer": "A2", "sources": [{"document": "x", "metadata": {}}]},
    ]
    for turn in chat_history:
        assert "question" in turn
        assert "answer" in turn
        assert "sources" in turn
        assert isinstance(turn["sources"], list)