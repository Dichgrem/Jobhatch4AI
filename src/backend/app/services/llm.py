from openai import OpenAI

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


def chat(messages: list[dict[str, str]]) -> str:
    response = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def chat_stream(messages: list[dict[str, str]]):
    stream = _get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
