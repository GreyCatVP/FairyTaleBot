import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = (
    "Ты — добрый сказочник. Пиши добрые, завершённые сказки для детей (детям 3–8 лет читают родители). "
    "Сказка должна быть простой, понятной, с лёгким юмором, и обязательно нести добрую мораль. "
    "Текст без заголовков и пояснений. Только сама сказка."
)

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

    part1_prompt = messages + [{"role": "user", "content": "Напиши первую часть сказки (вступление), до 500 символов."}]
    part1 = await call_openrouter(part1_prompt)

    part2_prompt = messages + [
        {
            "role": "user",
            "content": (
                f"Вот первая часть:
{part1}

"
                "Напиши вторую часть сказки (развитие событий), до 500 символов. "
                "Используй тех же героев и продолжи сюжет."
            )
        }
    ]
    part2 = await call_openrouter(part2_prompt)

    part3_prompt = messages + [
        {
            "role": "user",
            "content": (
                f"Вот первая и вторая части одной сказки:
{part1}
{part2}

"
                "Заверши именно ЭТУ историю. Не начинай новую! Обязательно сохрани героев и тему. "
                "Заверши доброй моралью и фразой вроде «Вот и сказке конец»."
            )
        }
    ]
    part3 = await call_openrouter(part3_prompt)

    full_story = part1.strip() + "\n\n" + part2.strip() + "\n\n" + part3.strip()
    return full_story