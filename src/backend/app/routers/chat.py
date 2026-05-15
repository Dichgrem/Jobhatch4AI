from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.rag import build_rag_prompt, generate_stream

router = APIRouter()


@router.post("")
async def chat_endpoint(req: dict):
    message = req.get("message", "")
    history = req.get("history", [])

    messages = build_rag_prompt(message, [])
    messages.insert(0, {"role": "system", "content": messages.pop(0)["content"]})

    for m in history:
        messages.append(m)
    messages.append({"role": "user", "content": message})

    async def event_stream():
        for text in generate_stream(messages):
            yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
