
import os
import httpx
import asyncio
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://t.me/SkazochnikTimoshaBot",
    "Content-Type": "application/json"
}

MODEL = "deepseek/deepseek-r1-0528:free"

async def gpt_call(messages, max_tokens=2048):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": max_tokens
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=HEADERS, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Слишком много запросов. Подожди немного и попробуй ещё раз ☕"
        raise

def is_truncated(text):
    last_word = re.split(r'\s+', text.strip())[-1]
    return not re.match(r'^[А-Яа-яA-Za-z0-9ёЁ\-–—"“”«»!?.,;:…]+$', last_word)

async def generate_fairytale():
    base_prompt = [
        {"role": "system", "content": (
            "Ты — сказочник. Пиши добрые, понятные сказки для детей 3–8 лет (читают родители). "
            "Главное — сюжет, эмоции, финал с моралью. Избегай длинных описаний и избыточных метафор. "
            "Пиши лаконично, образно, но просто. Объём — 1500–2000 символов."
        )},
        {"role": "user", "content": "Расскажи добрую сказку."}
    ]

    story = await gpt_call(base_prompt)
    if "Слишком много запросов" in story:
        return story

    verify_prompt = [{"role": "user", "content": f"Вот сказка:\n\n{story}\n\nСкажи честно, завершена ли она логически и художественно? Ответь только 'да' или 'нет'."}]
    verdict = await gpt_call(verify_prompt, max_tokens=10)
    if verdict.lower().strip().startswith("н"):
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
    current = ""
    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) + 1 > max_length:
            parts.append(current)
            current = paragraph
        else:
            current += "\n" + paragraph
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
