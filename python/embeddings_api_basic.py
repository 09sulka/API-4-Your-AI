from fastapi import FastAPI
import ollama
from typing import Optional, List, Union
from pydantic import BaseModel

app = FastAPI()

MODEL_NAME = "hf.co/speakleash/Bielik-4.5B-v3.0-Instruct-GGUF:Q8_0"

class Request(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = None

class EmbeddingItem(BaseModel):
    embedding: List[float]
    index: int

class TokenUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int

class Response(BaseModel):
    data: List[EmbeddingItem]
    model: Optional[str] = None
    usage: TokenUsage


@app.post("/openai/deployments/local/embeddings")
async def get_embeddings(request: Request):
    inputs = request.input
    model_name = request.model or MODEL_NAME

    if isinstance(inputs, str):
        inputs = [inputs]

    embed_response = ollama.embed(model=model_name, input=inputs)
    embeddings = embed_response.get("embeddings", [])
    prompt_tokens = embed_response.get("prompt_eval_count") or 0
    eval_tokens = embed_response.get("eval_count") or 0

    data = [
        EmbeddingItem(embedding=embedding, index=index)
        for index, embedding in enumerate(embeddings)
    ]

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        total_tokens=prompt_tokens + eval_tokens,
    )

    return Response(
        data=data,
        model=embed_response.get("model"),
        usage=usage,
    )
