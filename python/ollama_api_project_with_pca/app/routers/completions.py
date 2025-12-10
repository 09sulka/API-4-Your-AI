from fastapi import APIRouter
from app.models.openai_schemas import PromptRequest, CompletionChoice, CompletionResponse, TokenUsage
from app.services.ollama_service import chat, get_model

router = APIRouter(prefix="/openai/deployments/local")

@router.post("/completions", response_model=CompletionResponse)
async def completions(request: PromptRequest):
    model = get_model(request.model)
    response = chat(model, messages=[{"role": "user", "content": request.prompt}])

    output = response["message"]["content"]
    prompt_tokens = response.get("prompt_eval_count") or 0
    completion_tokens = response.get("eval_count") or 0

    usage = TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                       total_tokens=prompt_tokens + completion_tokens)

    choice = CompletionChoice(index=0, text=output, finish_reason="stop")

    return CompletionResponse(choices=[choice], model=response.get("model"), usage=usage)
