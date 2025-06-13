# main.py
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.ext import ConversationHandler
from utils import generate_fairytale
from custom_story_conversation import custom_story_conv, start_custom_story
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Хочу свою сказку"]]
    await update.message.reply_text(
        "Привет! Я — Сказочник Тимоша. ✨\nНапиши /skazka — и я расскажу тебе добрую сказку.\n\nИли нажми кнопку, если хочешь свою уникальную:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# Команда /skazka
async def skazka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Погоди немного... я вспоминаю сказку... ☕")
    story = await generate_fairytale()
    
    # Делим сказку на куски по 4000 символов
    for i in range(0, len(story), 4000):
        await update.message.reply_text(story[i:i+4000])

# Обработка кнопки "Хочу свою сказку"
async def handle_custom_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_custom_story(update, context)

# Основной запуск
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skazka", skazka))
    app.add_handler(CommandHandler("custom", start_custom_story))
    app.add_handler(MessageHandler(filters.Regex("Хочу свою сказку"), handle_custom_button))
    app.add_handler(custom_story_conv)

    print("Сказочник Тимоша запущен...")
    app.run_polling()