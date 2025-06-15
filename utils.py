
import os
import httpx
import time
import asyncio
import re
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LAST_REQUEST_TIME = {}

MODELS = [
    "deepseek/deepseek-r1-0528-qwen3-8b",
    "gryphe/mythomax-l2-13b"
]

SYSTEM_PROMPT = (
    "Ты — добрый сказочник. Придумай ОДНУ короткую и завершённую сказку для детей (3–8 лет). "
    "Не начинай вторую даже если осталось место. Добавь мораль — добро побеждает, забота важна, дружба ценна. "
    "Заверши сказку словами типа: «Вот и сказке конец», «Так закончилась сказка», «С тех пор они жили счастливо»."
)

def is_story_complete(story: str) -> bool:
    final_markers = [
        "Вот и сказке конец",
        "Так закончилась сказка",
        "И жили они долго и счастливо",
        "С тех пор они жили",
        "И на этом сказка закончилась"
    ]
    return any(marker in story for marker in final_markers)

def cut_to_first_story(story: str) -> str:
    intro_markers = [
        r"(Жила-была|Жил да был|Однажды|Давным-давно|В одном лесу|В далёкой деревне|Была у бабушки)"
    ]
    matches = list(re.finditer(intro_markers[0], story))
    if len(matches) > 1:
        cut_pos = matches[1].start()
        print("🪄 Обнаружено несколько сказок — обрезаем на первой.")
        return story[:cut_pos].strip() + "\n\n(🪄 Обрезано на первой сказке)"
    return story

async def call_openrouter(messages, model, max_tokens=1700, retries=3, delay=5):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://chat.openai.com/",
        "X-Title": "FairytaleBot"
    }

    for attempt in range(1, retries + 1):
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
                print(f"📡 [{model}] Ответ OpenRouter:", response.text)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    print(f"⚠️ Попытка {attempt} — модель перегружена ({model})")
                    await asyncio.sleep(delay)
                else:
                    print(f"❌ Ошибка [{model}]:", str(e))
                    raise e
            except Exception as e:
                print(f"❌ Другая ошибка [{model}]:", str(e))
                raise e
    raise Exception(f"Модель {model} перегружена (429) после {retries} попыток")

async def generate_fairytale(user_id=None):
    now = time.time()
    if user_id:
        if user_id in LAST_REQUEST_TIME and now - LAST_REQUEST_TIME[user_id] < 60:
            return "⏳ Пожалуйста, не так быстро. Подожди чуть-чуть — Тимоша пока варит варенье 🍓"
        LAST_REQUEST_TIME[user_id] = now

    for model in MODELS:
        try:
            # Основной запрос
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Расскажи одну добрую завершённую сказку с моралью. Только одну. Не продолжай и не добавляй вторую."}
            ]
            story = await call_openrouter(messages, model)
            story = cut_to_first_story(story)

            if is_story_complete(story):
                return story

            # Попытка завершения сказки
            print("⚠️ Сказка незавершённая — просим завершить...")
            continuation_prompt = [
                {"role": "system", "content": "Ты добрый сказочник, завершающий начатую сказку."},
                {"role": "user", "content": f"Вот первая часть сказки:\n\n{story}\n\nЗаверши ТОЛЬКО эту сказку. Не добавляй новых героев. Не начинай новую. Добавь мораль и финал в том же стиле."}
            ]
            continuation = await call_openrouter(continuation_prompt, model)
            full_story = (story.strip() + "\n\n" + continuation.strip()).strip()

            if is_story_complete(full_story):
                return full_story
            else:
                print("⚠️ Даже завершение не помогло — честно сообщаем пользователю.")
                return "🌫 Тимоша начал рассказывать сказку, но она убежала в кусты, не досказав финал. Попробуй снова — возможно, она вернётся."

        except Exception as e:
            print(f"🛑 [{model}] ошибка генерации:", str(e))

    return "😓 Все модели устали и ушли спать. Попробуй снова чуть позже."
