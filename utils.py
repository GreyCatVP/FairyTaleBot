import os
import httpx
import time
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LAST_REQUEST_TIME = {}

SYSTEM_PROMPT = (
    "Ты — добрый сказочник. Пиши добрые, завершённые сказки для детей (детям 3–8 лет читают родители). "
    "Сказка должна быть простой, понятной, с лёгким юмором, и обязательно нести добрую мораль. "
    "Заканчивай сказку фразой «Вот и сказке конец» или подобной."
)

def is_story_complete(story: str) -> bool:
    final_markers = [
        "Вот и сказке конец",
        "И жили они долго и счастливо",
        "Так закончилась эта сказка",
        "С тех пор они стали"
    ]
    return any(marker in story for marker in final_markers)

async def call_openrouter(messages, model="deepseek/deepseek-r1-0528-qwen3-8b", max_tokens=1800):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://chat.openai.com/",
        "X-Title": "FairytaleBot"
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.9
                }
            )
            print("📡 Ответ OpenRouter:", response.text)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            print("❌ Сетевая ошибка:", str(e))
            raise e
        except httpx.HTTPStatusError as e:
            print("❌ HTTP ошибка:", str(e))
            print("🔽 Ответ тела:", e.response.text)
            raise e

async def generate_fairytale(user_id=None):
    now = time.time()
    if user_id:
        if user_id in LAST_REQUEST_TIME and now - LAST_REQUEST_TIME[user_id] < 300:
            return "⏳ Пожалуйста, не так быстро. Попробуй ещё раз через несколько минут."
        LAST_REQUEST_TIME[user_id] = now

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Придумай короткую, но завершённую сказку для детей. Обязательно включи добрую мораль и финал типа «Вот и сказке конец»."}
    ]

    try:
        story = await call_openrouter(messages)
        print("📜 Сказка сгенерирована:\n", story)
        if is_story_complete(story):
            return story
        else:
            return story + "\n\n(⚠️ История не завершена, но выдана.)"
    except Exception as e:
        print("❌ Ошибка генерации:", str(e))
        return "Ой... что-то пошло не так. Тимоша потерял сказку. Попробуй ещё раз позже.\n❌ Ошибка: {}".format(str(e))