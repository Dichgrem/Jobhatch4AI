from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.pipeline import load_pipeline_state
from app.services.rag import build_rag_prompt, generate_stream

router = APIRouter()


def _build_context() -> str:
    state = load_pipeline_state()
    parts = []

    if state["total_jobs"]:
        parts.append(f"数据集中共 {state['total_jobs']} 条招聘数据。")

    if state["avg_salary"]:
        parts.append(f"平均薪资 {state['avg_salary']} 元/月。")

    sd = state.get("salary_distribution", {})
    if sd.get("data") and any(sd["data"]):
        sm_entries = [
            f"{label}:{cnt}条" for label, cnt in zip(sd["labels"], sd["data"]) if cnt
        ]
        parts.append(f"薪资分布: {', '.join(sm_entries)}。")

    ed = state.get("education_distribution", {})
    if ed.get("data") and any(ed["data"]):
        edu_entries = [
            f"{label}:{cnt}条" for label, cnt in zip(ed["labels"], ed["data"]) if cnt
        ]
        parts.append(f"学历要求分布: {', '.join(edu_entries)}。")

    skills = state.get("top_skills", [])
    if skills:
        top = ", ".join(s["skill"] for s in skills[:10])
        parts.append(f"热门技能关键词: {top}。")

    return "\n".join(parts)


@router.post("")
async def chat_endpoint(req: dict):
    message = req.get("message", "")
    history = req.get("history", [])

    context = _build_context()
    chunks = [context] if context else []

    messages = build_rag_prompt(message, chunks)
    messages.insert(0, {"role": "system", "content": messages.pop(0)["content"]})

    for m in history:
        messages.append(m)
    messages.append({"role": "user", "content": message})

    async def event_stream():
        for text in generate_stream(messages):
            yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/context")
async def get_chat_context():
    return {"context": _build_context()}
