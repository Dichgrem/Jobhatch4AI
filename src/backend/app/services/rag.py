from pathlib import Path

from app.services.llm import client
from app.config import LLM_MODEL

SYSTEM_PROMPT = """你是一个招聘数据分析助手。你可以帮助用户：
1. 根据用户的技能推荐合适的岗位方向
2. 分析不同岗位的技术栈需求
3. 提供求职和职业发展建议
4. 回答关于招聘市场趋势的问题

请在回答时引用数据支撑你的观点，保持专业、客观的语气。"""


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
