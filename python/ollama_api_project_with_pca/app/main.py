from fastapi import FastAPI
from app.routers import embeddings, completions, chat_completions

app = FastAPI(title="Local OpenAI-compatible API for Ollama with Dimension Reduction")

app.include_router(embeddings.router)
app.include_router(completions.router)
app.include_router(chat_completions.router)
