import aiohttp
import os

SYSTEM_PROMPT = (
    "Ты — Сказочник Тимоша, искусный рассказчик добрых сказок для детей. "
    "Каждая сказка должна быть закончена, содержать мораль и завершаться фразой вроде «Вот и сказке конец»."
)

async def call_openrouter(payload):
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "HTTP-Referer": "https://t.me/SkazochnikTimoshaBot",
        "X-Title": "FairyTaleBot"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Ошибка запроса: {resp.status}")
            result = await resp.json()
            return result["choices"][0]["message"]["content"]

async def generate_fairytale():
    prompt = {"role": "user", "content": "Придумай новую сказку."}
    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, prompt],
        "temperature": 0.9,
        "max_tokens": 1800
    }

    story = await call_openrouter(payload)
    if is_story_complete(story):
        return story

    # Автозавершение если сказка не закончена
    continuation_prompt = {
        "role": "user",
        "content": f"Вот начало сказки:

{story}

Заверши эту сказку. Не начинай новую. Сохрани героев и добавь мораль. Закончить фразой «Вот и сказке конец»."
    }
    continuation_payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, continuation_prompt],
        "temperature": 0.9,
        "max_tokens": 800
    }

    ending = await call_openrouter(continuation_payload)
    return story.strip() + "

" + ending.strip()

def is_story_complete(story: str) -> bool:
    lowered = story.lower()
    completion_markers = [
        "вот и сказке конец", "вот и всё", "и с тех пор", "и жили они долго",
        "с тех пор", "и больше он никогда", "с этого дня", "так закончилась"
    ]
    moral_markers = [
        "мораль", "урок", "научился", "понял", "дружба", "добро", "важно", "всегда", "настоящее"
    ]
    # наличие финального маркера или морального вывода
    has_final = any(marker in lowered for marker in completion_markers)
    has_moral = any(phrase in lowered for phrase in moral_markers)
    return has_final or has_moral