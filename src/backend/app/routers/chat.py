from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.rag import (
    build_rag_prompt,
    build_rag_prompt_with_semantic,
    build_stats_context,
    generate_stream,
)

router = APIRouter()


@router.post("")
async def chat_endpoint(req: dict):
    message = req.get("message", "")
    history = req.get("history", [])
    use_semantic = req.get("use_semantic", False)

    if use_semantic:
        semantic_results = _try_semantic_search(message)
    else:
        semantic_results = []

    stats_context = build_stats_context()

    if semantic_results:
        messages = build_rag_prompt_with_semantic(
            message, semantic_results, stats_context
        )
    else:
        chunks = [stats_context] if stats_context else []
        messages = build_rag_prompt(message, chunks)

    for m in history:
        messages.append(m)

    if history:
        messages.append({"role": "user", "content": message})

    async def event_stream():
        for text in generate_stream(messages):
            yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/context")
async def get_chat_context():
    return {"context": build_stats_context()}


def _try_semantic_search(query: str) -> list[dict]:
    try:
        from app.services.embedding import text_to_embedding
        from app.services.vector_search import search, index_exists

        if not index_exists("job_index"):
            return []
        query_vec = text_to_embedding(query)
        return search(query_vec, top_k=5, name="job_index")
    except Exception:
        return []
