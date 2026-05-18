from pathlib import Path

from app.services.llm import _get_client
from app.services.pipeline import load_pipeline_state
from app.config import LLM_MODEL

SYSTEM_PROMPT = """你是一个招聘数据智能分析助手。基于用户已上传的招聘数据集，你可以帮助用户：
1. 分析薪资分布、学历要求、经验门槛等市场趋势
2. 根据用户的技能推荐匹配的岗位方向
3. 分析不同岗位的技术栈需求差异
4. 提供求职策略和职业发展建议

请在回答时引用数据集中的具体数字，保持专业、客观的语气。如果没有数据支撑，请如实告知用户需要先上传招聘数据。"""


def build_rag_prompt(query: str, context_chunks: list[str]) -> list[dict[str, str]]:
    context_text = "\n\n---\n\n".join(context_chunks)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"【参考资料】\n{context_text}\n\n【用户问题】\n{query}\n\n请基于参考资料回答用户问题。如果参考资料中找不到相关信息，请如实告知。",
        },
    ]


def build_stats_context() -> str:
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


def build_rag_prompt_with_semantic(
    query: str,
    semantic_results: list[dict],
    stats_context: str | None = None,
) -> list[dict[str, str]]:
    context_parts = []

    if stats_context:
        context_parts.append(f"【数据统计】\n{stats_context}")

    if semantic_results:
        semantic_chunks = []
        for r in semantic_results[:5]:
            text = r.get("text", "")
            if text:
                similarity = r.get("similarity", 0)
                semantic_chunks.append(
                    f"[相似度:{similarity:.3f}] {text}"
                )
        if semantic_chunks:
            context_parts.append(
                "【语义检索的相关职位描述】\n" + "\n---\n".join(semantic_chunks)
            )

    context_text = "\n\n".join(context_parts)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"【参考资料】\n{context_text}\n\n【用户问题】\n{query}\n\n请基于参考资料回答用户问题。如果参考资料中找不到相关信息，请如实告知。",
        },
    ]


def generate(data: list[dict[str, str]]) -> str:
    response = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=data,
    )
    return response.choices[0].message.content or ""


def generate_stream(data: list[dict[str, str]]):
    stream = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=data,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def load_chunks_from_dir(directory: str | Path, pattern: str = "*.txt") -> list[str]:
    return [f.read_text(encoding="utf-8") for f in Path(directory).glob(pattern)]
