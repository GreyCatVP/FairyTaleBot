import os
import re
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

WEAK_END_VERBS = [
    "сидел", "сидела", "думал", "думала", "плакал", "плакала", "стоял", "стояла",
    "ждал", "ждала", "молчал", "молчала", "смотрел", "смотрела", "бежал", "бежала",
    "смотрели", "стояли", "плакали", "молчали", "бежали"
]

MAX_LENGTH = 4096

def is_story_ok(story: str):
    return len(story) >= 1200

def is_story_finished(story: str):
    cleaned = story.strip()
    last_line = cleaned.split("\n")[-1].lower().strip(" .!?«»")
    if any(end in cleaned[-300:] for end in ENDINGS) and cleaned[-1] in ".!?":
        return True
    if any(last_line.endswith(verb) for verb in WEAK_END_VERBS):
        return False
    return len(last_line.split()) >= 5 and cleaned[-1] in ".!?"

def ensure_ending(story: str):
    if not is_story_finished(story):
        story += "\n\nВот и сказке конец. ✨"
    return story

def split_text_smart(text, max_len=MAX_LENGTH):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(para) > max_len:
            sentences = re.split(r'(?<=[.!?…]) +', para)
            for sentence in sentences:
                if len(current) + len(sentence) + 1 > max_len:
                    chunks.append(current.strip())
                    current = sentence
                else:
                    current += " " + sentence
        else:
            if len(current) + len(para) + 2 > max_len:
                chunks.append(current.strip())
                current = para
            else:
                current += "\n" + para

    if current.strip():
        chunks.append(current.strip())
    return chunks

async def request_gpt_story(messages: list, max_tokens=2000):
    payload = {
        "model": "deepseek/deepseek-r1-0528:free",
        "max_tokens": max_tokens,
        "messages": messages
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

async def generate_fairytale():
    base_messages = [
        {
            "role": "system",
            "content": (
                "Ты — сказочник. Твоя задача — рассказывать добрые, понятные сказки для детей. "
                "Целевая аудитория: дети 3–8 лет, читают родители. "
                "Сказка должна быть завершённой, с понятной моралью. Не добавляй ничего после сказки. "
                "Желаемый объём — от 1500 до 2000 символов."
            )
        },
        {
            "role": "user",
            "content": "Расскажи добрую сказку."
        }
    ]

    for attempt in range(3):
        try:
            story = await request_gpt_story(base_messages)
            print(f"\n=== GPT Сказка [{attempt+1}] ===\n{story}\n")

            if is_story_ok(story):
                if is_story_finished(story):
                    return ensure_ending(story)

                print("⏭ Обнаружен обрыв — GPT продолжит сказку...")
                continuation_messages = [
                    *base_messages,
                    {
                        "role": "assistant",
                        "content": story
                    },
                    {
                        "role": "user",
                        "content": "Пожалуйста, закончи эту сказку до конца, добавив финал и мораль."
                    }
                ]
                continuation = await request_gpt_story(continuation_messages, max_tokens=600)
                full_story = story + "\n" + continuation
                return ensure_ending(full_story)
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
    parts = split_text_smart(story)

    for i, part in enumerate(parts, start=1):
        if len(parts) > 1:
            header = f"📘 Часть {i}/{len(parts)}\n"
        else:
            header = ""
        await update.message.reply_text(header + part)

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
