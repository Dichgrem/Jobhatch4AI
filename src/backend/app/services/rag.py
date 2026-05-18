from pathlib import Path

from app.services.llm import client
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


def generate(data: list[dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=data,
    )
    return response.choices[0].message.content or ""


def generate_stream(data: list[dict[str, str]]):
    stream = client.chat.completions.create(
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
