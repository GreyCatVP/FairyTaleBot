
import os
import httpx
import asyncio
import re
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://t.me/SkazochnikTimoshaBot",
    "Content-Type": "application/json"
}

async def gpt_call(messages, max_tokens=2048, retries=2):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tokens
    }
    for attempt in range(retries + 1):
        try:
            sys.stderr.write(f"[🌀] Попытка запроса #{attempt+1} к GPT\n")
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=HEADERS, json=payload)
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"].strip()
                sys.stderr.write(f"[DEBUG] GPT ответ (обрезано): {content[:100]}...\n")
                if any(msg in content.lower() for msg in ["слишком много запросов", "too many requests", "rate limit", "model is busy"]):
                    sys.stderr.write("[⚠️] Заглушка от OpenRouter: GPT не был запущен.\n")
                    return "Сегодня волшебный портал перегружен. Я тихонько посижу и подожду. Загляни чуть позже ☁️"
                return content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                sys.stderr.write(f"[🚫] 429 Too Many Requests от OpenRouter (попытка {attempt+1})\n")
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                return "Слишком много запросов. Подожди немного и попробуй ещё раз ☕"
            raise
        except Exception as ex:
            sys.stderr.write(f"[❌] Ошибка при обращении к GPT: {str(ex)}\n")
            return "Произошла ошибка при обращении к сказочному порталу 😢"

def is_truncated(text):
    last_word = re.split(r'\s+', text.strip())[-1]
    return not re.match(r'^[А-Яа-яA-Za-z0-9ёЁ\-–—"“”«»!?.,;:…]+$', last_word)

def is_only_moral(text):
    lowered = text.lower()
    return (
        lowered.startswith("вот и сказке конец") or
        "мораль" in lowered[:300] and len(text.split()) < 100
    )

async def generate_fairytale():
    base_prompt = [
        {"role": "system", "content": (
            "Ты — сказочник. Пиши добрые, понятные сказки для детей 3–8 лет (читают родители). "
            "Главное — сюжет, эмоции, финал с моралью. Избегай длинных описаний и избыточных метафор. "
            "Пиши лаконично, образно, но просто. Объём — 1500–2000 символов."
        )},
        {"role": "user", "content": "Расскажи добрую сказку."}
    ]

    story = await gpt_call(base_prompt, retries=2)
    if "волшебный портал перегружен" in story or "Слишком много запросов" in story:
        return story

    if is_only_moral(story):
        sys.stderr.write("[❗] Получена мораль без сказки — повторная генерация\n")
        story = await gpt_call(base_prompt)

    verify_prompt = [{"role": "user", "content": f"Вот сказка:\n\n{story}\n\nСкажи честно, завершена ли она логически и художественно? Ответь только 'да' или 'нет'."}]
    verdict = await gpt_call(verify_prompt, max_tokens=10)
    if not verdict.strip().lower().startswith("да"):
        cont_prompt = base_prompt + [{"role": "assistant", "content": story}, {"role": "user", "content": "Пожалуйста, продолжи сказку до её полного завершения с финалом и моралью."}]
        continuation = await gpt_call(cont_prompt)
        story += "\n" + continuation

    last_line = story.strip().split("\n")[-1].lower()
    if any(last_line.endswith(w) for w in ["ла", "ел", "лся", "ала", "ли", "всё", "нет"]) or len(last_line.split()) < 5 or is_truncated(story):
        final_prompt = base_prompt + [{"role": "assistant", "content": story}, {"role": "user", "content": "Пожалуйста, допиши финальную сцену. Герои уже собрались. Добавь, как они чувствуют себя, что поняли, и какой вывод остался."}]
        final_piece = await gpt_call(final_prompt)
        story += "\n" + final_piece

    if not story.strip().endswith("Вот и сказке конец. ✨"):
        story += "\n\nВот и сказке конец. ✨"

    return story

def split_story(text, max_length=4096):
    parts = []
    paragraphs = text.split("\n")
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 1 > max_length:
            parts.append(current)
            current = p
        else:
            current += "\n" + p
    if current:
        parts.append(current)
    return parts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — Сказочник Тимоша. ✨\nНапиши /skazka — и я расскажу тебе добрую сказку.")

async def skazka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Погоди немного... я вспоминаю сказку... ☕")
    story = await generate_fairytale()
    parts = split_story(story)
    for i, part in enumerate(parts):
        header = f"📘 Часть {i+1}/{len(parts)}\n" if len(parts) > 1 else ""
        await update.message.reply_text(header + part.strip())

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skazka", skazka))

    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Service is up')
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

    def run_dummy_server():
        server = HTTPServer(('0.0.0.0', 8080), DummyHandler)
        server.serve_forever()

    threading.Thread(target=run_dummy_server, daemon=True).start()
    app.run_polling()
