from typing import List, Optional, Union
from pydantic import BaseModel
from .base import ChatMessage

class Request(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = None

class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = None

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

class EmbeddingResponse(BaseModel):
    data: List[EmbeddingItem]
    model: Optional[str]
    usage: TokenUsage

class CompletionChoice(BaseModel):
    index: int
    text: str
    finish_reason: str = "stop"

class CompletionResponse(BaseModel):
    choices: List[CompletionChoice]
    model: Optional[str]
    usage: TokenUsage

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    choices: List[ChatCompletionChoice]
    model: Optional[str]
    usage: TokenUsage
