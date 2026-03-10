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


def test_generate_uses_provided_model():
    """When model is passed, Ollama client is called with that model."""
    with patch("app.llm.ollama") as mock_ollama:
        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": "Hi"}}
        mock_ollama.Client.return_value = mock_client
        generate("System", "User", model="llama3.2")
    mock_client.chat.assert_called_once()
    call_kw = mock_client.chat.call_args[1]
    assert call_kw["model"] == "llama3.2"


def test_generate_uses_config_model_when_model_is_none():
    """When model is None, Ollama client is called with LLM_MODEL from config."""
    with patch("app.llm.ollama") as mock_ollama, patch("app.llm.LLM_MODEL", "mistral"):
        mock_client = MagicMock()
        mock_client.chat.return_value = {"message": {"content": "Hi"}}
        mock_ollama.Client.return_value = mock_client
        generate("System", "User")
    mock_client.chat.assert_called_once()
    call_kw = mock_client.chat.call_args[1]
    assert call_kw["model"] == "mistral"