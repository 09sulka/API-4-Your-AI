import ollama
from app.config import MODEL_NAME

def get_model(requested_model: str | None) -> str:
    return requested_model or MODEL_NAME

def embed_text(model: str, inputs: list[str]):
    return ollama.embed(model=model, input=inputs)

def chat(model: str, messages: list[dict]):
    return ollama.chat(model=model, messages=messages)
