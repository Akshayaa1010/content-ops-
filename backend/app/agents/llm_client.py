# app/agents/llm_client.py
from groq import AsyncGroq
from app.config.settings import settings

client = AsyncGroq(api_key=settings.groq_api_key)

async def generate(system_prompt: str, user_message: str,
                   max_tokens: int = 1500) -> str:
    chat_completion = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        model="llama-3.3-70b-versatile",
        max_tokens=max_tokens,
    )
    return chat_completion.choices[0].message.content

async def generate_json(system_prompt: str, user_message: str) -> str:
    chat_completion = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
    )
    return chat_completion.choices[0].message.content