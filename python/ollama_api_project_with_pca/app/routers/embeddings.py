from fastapi import APIRouter
from app.models.openai_schemas import Request, EmbeddingItem, TokenUsage, EmbeddingResponse
from app.services.ollama_service import embed_text, get_model
from app.services.dim_reduction import reduce_embedding

router = APIRouter(prefix="/openai/deployments/local")

@router.post("/embeddings", response_model=EmbeddingResponse)
async def embeddings(request: Request):
    model = get_model(request.model)
    inputs = request.input if isinstance(request.input, list) else [request.input]

    response = embed_text(model, inputs)
    embeddings = response.get("embeddings", [])
    prompt_tokens = response.get("prompt_eval_count") or 0
    eval_tokens = response.get("eval_count") or 0

    items = [
        EmbeddingItem(
            embedding=reduce_embedding(e),
            index=i
        )
        for i, e in enumerate(embeddings)
    ]

    usage = TokenUsage(prompt_tokens=prompt_tokens, total_tokens=prompt_tokens + eval_tokens)

    return EmbeddingResponse(data=items, model=response.get("model"), usage=usage)
