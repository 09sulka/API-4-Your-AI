from fastapi import FastAPI
import ollama
from typing import Optional, List, Union
from pydantic import BaseModel

app = FastAPI()

MODEL_NAME = "hf.co/speakleash/Bielik-4.5B-v3.0-Instruct-GGUF:Q8_0"

class Request(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = None

class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None

class EmbeddingItem(BaseModel):
    embedding: List[float]
    index: int

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int = 0
    total_tokens: int

class Response(BaseModel):
    data: List[EmbeddingItem]
    model: Optional[str] = None
    usage: TokenUsage

class CompletionChoice(BaseModel):
    index: int
    text: str
    finish_reason: str = "stop"

class CompletionResponse(BaseModel):
    choices: List[CompletionChoice]
    model: Optional[str] = None
    usage: TokenUsage

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    choices: List[ChatCompletionChoice]
    model: Optional[str] = None
    usage: TokenUsage


@app.post("/openai/deployments/local/embeddings")
async def get_embeddings(request: Request):
    inputs = request.input
    model_name =  MODEL_NAME

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

@app.post("/openai/deployments/local/completions")
async def generate(request: PromptRequest):
    model_name = MODEL_NAME

    # Call Ollama chat model
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": request.prompt}]
    )

    # Extract text result
    output_text = response["message"]["content"]

    # Extract token usage (may be missing depending on model)
    prompt_tokens = response.get("prompt_eval_count") or 0
    completion_tokens = response.get("eval_count") or 0

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )

    # Construct the standard choice structure
    choice = CompletionChoice(
        index=0,
        text=output_text,
        finish_reason="stop"
    )

    # Build final response
    return CompletionResponse(
        choices=[choice],
        model=response.get("model"),
        usage=usage,
    )


@app.post("/openai/deployments/local/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    model_name = request.model or MODEL_NAME
    messages = request.messages or []

    # Convert OpenAI message schema to Ollama message schema
    ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

    # Call the chat model through Ollama
    response = ollama.chat(
        model=model_name,
        messages=ollama_messages
    )

    # Text output from the model
    output_text = response.get("message", {}).get("content", "")

    # Token usage
    prompt_tokens = response.get("prompt_eval_count") or 0
    completion_tokens = response.get("eval_count") or 0

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )

    # Prepare OpenAI-style output
    choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(
            role="assistant",
            content=output_text
        ),
        finish_reason="stop"
    )

    return ChatCompletionResponse(
        choices=[choice],
        model=response.get("model") or model_name,
        usage=usage
    )
