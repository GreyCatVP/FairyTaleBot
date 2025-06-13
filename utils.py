# utils.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

SYSTEM_PROMPT = (
    "Ты — добрый сказочник по имени Тимоша. Пиши сказки для детей 5–9 лет."
    " Они должны быть тёплыми, добрыми, волшебными, без жестокости."
    " Объём — от 3000 до 5000 символов. Используй простой, но выразительный язык."
)

async def generate_fairytale():
    payload = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Придумай новую сказку."}
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=HEADERS,
                json=payload
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return "Ой... что-то пошло не так. Тимоша потерял сказку. Попробуй ещё раз позже."