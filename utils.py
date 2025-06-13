import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = "Ты — добрый сказочник. Пиши короткие (3000–5000 символов), светлые и волшебные сказки для детей. Простым языком, с лёгким юмором и моралью."

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://github.com/GreyCatVP/FairyTaleBot",  # важно для OpenRouter
    "Content-Type": "application/json"
}


async def generate_fairytale():
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",  # 👉 бесплатная модель
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Придумай новую сказку."}
        ],
        "temperature": 1.0
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
        print(f"[OpenRouter ERROR] {e}")
        return "Ой... что-то пошло не так. Тимоша потерял сказку. Попробуй ещё раз позже."
