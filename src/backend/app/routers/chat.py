from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.services.llm import chat_stream

router = APIRouter()

SYSTEM_PROMPT = """你是一个招聘数据分析助手。你可以帮助用户：
1. 分析招聘数据趋势
2. 提供求职建议
3. 回答关于系统数据可视化的相关问题
请用友好、专业的语气回答。"""


@router.post("")
async def chat_endpoint(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in req.history:
        messages.append(m)
    messages.append({"role": "user", "content": req.message})

    async def event_stream():
        for text in chat_stream(messages):
            yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
