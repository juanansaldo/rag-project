import ollama
from app.config import LLM_MODEL, OLLAMA_BASE_URL


def generate(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    """Call Ollama chat. Uses model from config if model is None. Returns the model's reply text."""
    client = ollama.Client(host=OLLAMA_BASE_URL)
    model_name = model if model is not None else LLM_MODEL
    response = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"].strip()