import ollama
from app.config import LLM_MODEL, OLLAMA_BASE_URL


def generate(system_prompt: str, user_prompt: str) -> str:
    """Call Mistral via Ollama. Returns the model's reply text."""
    client = ollama.Client(host=OLLAMA_BASE_URL)
    response = client.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"].strip()