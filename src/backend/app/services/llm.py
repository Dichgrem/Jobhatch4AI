from openai import OpenAI

from app.config import ARK_API_KEY, ARK_BASE_URL, LLM_MODEL

client = OpenAI(api_key=ARK_API_KEY, base_url=ARK_BASE_URL)


def chat(messages: list[dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def chat_stream(messages: list[dict[str, str]]):
    stream = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
