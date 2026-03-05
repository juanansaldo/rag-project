from unittest.mock import MagicMock, patch

from app.llm import generate


def test_generate_returns_model_reply():
    fake_reply = "The answer is forty-two."
    with patch("app.llm.ollama") as mock_ollama:
        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": " " + fake_reply + " "}}
        mock_ollama.Client.return_value = mock_client
        out = generate("You are helpful.", "what i 6*7?")
    assert out == fake_reply
    mock_client.chat.assert_called_once()
    call_kw = mock_client.chat.call_args[1]
    assert call_kw["model"] is not None
    assert len(call_kw["messages"]) == 2
    assert call_kw["messages"][0]["role"] == "system"
    assert call_kw["messages"][1]["role"] == "user"