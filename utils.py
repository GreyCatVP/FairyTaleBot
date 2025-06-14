import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "Ты — добрый сказочник. Пиши добрые, завершённые сказки для детей (детям 3–8 лет читают родители). "
    "Сказка должна быть простой, понятной, с лёгким юмором, и обязательно нести добрую мораль. "
    "Текст без заголовков и пояснений. Только сама сказка."
)

RESERVE_PROMPT = (
    "Ты — добрый сказочник. Придумай короткую, но завершённую сказку для детей до 8 лет. "
    "Она должна быть цельной, без повторов, без обрывов, длиной до 1800 символов. "
    "Включи добрую мораль и обязательно закончи сказку финальной фразой, например: «Вот и сказке конец»."
)

def is_story_complete(story: str) -> bool:
    final_markers = [
        "Вот и сказке конец",
        "И жили они долго и счастливо",
        "Так закончилась эта сказка",
        "С тех пор они стали"
    ]
    return any(marker in story for marker in final_markers)

async def call_openrouter(messages, model="deepseek/deepseek-r1-0528-qwen3-8b", max_tokens=600):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://chat.openai.com/",
        "X-Title": "FairytaleBot"
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
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
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

async def generate_fairytale():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    try:
        part1_prompt = messages + [{"role": "user", "content": "Напиши первую часть сказки (вступление), до 500 символов."}]
        part1 = await call_openrouter(part1_prompt)
        await asyncio.sleep(10)

        part2_prompt = messages + [{
            "role": "user",
            "content": """Вот первая часть:
{}

Напиши вторую часть сказки (развитие событий), до 500 символов. Используй тех же героев и продолжи сюжет.""".format(part1)
        }]
        part2 = await call_openrouter(part2_prompt)
        await asyncio.sleep(10)

        part3_prompt = messages + [{
            "role": "user",
            "content": """Вот первая и вторая части одной сказки:
{}
{}

Заверши именно ЭТУ историю. Не начинай новую! Обязательно сохрани героев и тему. Заверши доброй моралью и фразой вроде «Вот и сказке конец».""".format(part1, part2)
        }]
        part3 = await call_openrouter(part3_prompt)

        story = part1.strip() + "\n\n" + part2.strip() + "\n\n" + part3.strip()

        if is_story_complete(story):
            return story
    except Exception:
        pass

    reserve_prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": RESERVE_PROMPT}
    ]
    fallback_story = await call_openrouter(
        reserve_prompt,
        max_tokens=1800
    )
    return fallback_story