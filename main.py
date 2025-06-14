
import os
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """Ты — добрый сказочник. Придумывай оригинальные добрые сказки для детей, чтобы их могли читать родители перед сном.
Истории должны быть тёплыми, с моралью, легко читаемыми. Не пиши слишком коротко и не перегружай сложными словами.

Размер сказки — 1500–2000 символов."""

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://t.me/SkazochnikTimoshaBot",
    "Content-Type": "application/json"
}

async def generate_fairytale():
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {
                "role": "system",
                "content": "Ты — добрый рассказчик сказок для детей. Пиши короткие, добрые, волшебные истории, которые приятно читать вслух. Сохраняй тепло, смысл и лёгкость."
            },
            {
                "role": "user",
                "content": "Придумай новую добрую сказку на русском языке. Сюжет должен быть интересным детям. Объём — строго от 1500 до 2000 символов. Используй простые слова, без лишней воды. Сказку будут читать вслух мама или папа."
            }
        ],
        "max_tokens": 800  # ≈ 1600–2000 символов
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
        print(f"❌ Ошибка генерации: {e}")
        return "Ой... что-то пошло не так. Тимоша потерял сказку. Попробуй ещё раз позже."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — Сказочник Тимоша. ✨\nНапиши /skazka — и я расскажу тебе добрую сказку.")

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
