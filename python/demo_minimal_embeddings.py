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

class Response(BaseModel):
    data: List[EmbeddingItem]


@app.post("/generate")
async def generate(prompt: str):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return {"response": response["message"]["content"]}


@app.post("/openai/deployments/local/embeddings")
async def get_embeddings(request: Request):
    inputs = request.input


    if isinstance(inputs, str):
        inputs = [inputs]

    data = []

    for text in inputs:
        emb = ollama.embeddings(model=MODEL_NAME, prompt=text)
        data.append(EmbeddingItem(embedding=emb["embedding"]))

    return Response(data=data)
