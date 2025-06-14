import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "Ты — добрый сказочник. Пиши добрые, завершённые сказки для детей (детям 3–8 лет читают родители). "
    "Сказка должна быть простой, понятной, с лёгким юмором, и обязательно нести добрую мораль. "
    "В финале обязательно сделай вывод, чему научила эта история. "
    "Заканчивай сказку фразой вроде: «Вот и сказке конец» или «И жили они долго и счастливо». "
    "Размер: от 1500 до 2000 символов. Только текст сказки. Без заголовков, без пояснений."
)


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
        "temperature": 0.9,
        "stop": None,
        "max_tokens": 1800
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
