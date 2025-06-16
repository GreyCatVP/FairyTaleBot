import os
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://t.me/SkazochnikTimoshaBot",
    "Content-Type": "application/json"
}

ENDINGS = [
    "Вот и сказке конец.",
    "И жили они долго и счастливо.",
    "И с тех пор никто их не видел.",
    "С тех пор все были счастливы.",
    "А добрая фея наблюдала за ними с неба.",
    "Так закончилась эта история.",
    "И всё было хорошо.",
    "А мы отправимся в следующую сказку.",
    "Вот и всё, ребята.",
    "Вот такая сказка.",
    "И больше они не боялись темноты.",
]

def is_story_ok(story: str):
    return len(story) >= 1200

def ensure_ending(story: str):
    if not any(end in story[-300:] for end in ENDINGS):
        story += "\n\nВот и сказке конец. ✨"
    return story

async def generate_fairytale():
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "max_tokens": 1600,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — сказочник. Твоя задача — рассказывать добрые, понятные сказки для детей. "
                    "Целевая аудитория: дети 3–8 лет, читают родители. "
                    "Сказка должна быть завершённой, без обрыва. Не добавляй ничего после сказки. "
                    "Желаемый объём — от 1500 до 2000 символов."
                )
            },
            {
                "role": "user",
                "content": "Расскажи добрую сказку."
            }
        ]
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=HEADERS,
                    json=payload
                )
                response.raise_for_status()
                story = response.json()["choices"][0]["message"]["content"].strip()
                print(f"\n=== GPT Сказка [{attempt+1}] ===\n{story}\n")
                if is_story_ok(story):
                    return ensure_ending(story)
        except Exception as e:
            print(f"❌ Попытка {attempt+1}: ошибка генерации — {e}")

    return "Сказка сбежала в лес... Попробуй ещё раз позже 🐾"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я — Сказочник Тимоша. ✨\nНапиши /skazka — и я расскажу тебе добрую сказку."
    )

async def skazka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Погоди немного... я вспоминаю сказку... ☕")
    story = await generate_fairytale()

    if len(story) <= 4096:
        await update.message.reply_text(story)
    else:
        for i in range(0, len(story), 4096):
            await update.message.reply_text(story[i:i+4096])

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
