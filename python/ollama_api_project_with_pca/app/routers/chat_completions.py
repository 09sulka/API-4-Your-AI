from fastapi import APIRouter
from app.models.openai_schemas import ChatCompletionRequest, ChatCompletionChoice, ChatCompletionResponse, ChatMessage, TokenUsage
from app.services.ollama_service import chat, get_model

router = APIRouter(prefix="/openai/deployments/local")

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    model = get_model(request.model)
    ollama_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    response = chat(model, ollama_messages)
    output = response.get("message", {}).get("content", "")

    prompt_tokens = response.get("prompt_eval_count") or 0
    completion_tokens = response.get("eval_count") or 0

    usage = TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                       total_tokens=prompt_tokens + completion_tokens)

    choice = ChatCompletionChoice(index=0, message=ChatMessage(role="assistant", content=output),
                                  finish_reason="stop")

    return ChatCompletionResponse(choices=[choice], model=response.get("model") or model, usage=usage)
