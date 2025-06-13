# custom_story_conversation.py
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes
from utils import generate_fairytale

HERO, THEME, TONE, CONFIRM = range(4)

async def start_custom_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Давай сочиним твою сказку! ✨\nКто будет главным героем?")
    return HERO

async def set_hero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hero'] = update.message.text
    await update.message.reply_text("О чём должна быть сказка? Напиши коротко.")
    return THEME

async def set_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['theme'] = update.message.text
    keyboard = [["Весёлая 🎉", "Поучительная 📚"], ["Страшная 👻", "Абсурдная 🤪"]]
    await update.message.reply_text(
        "Какой должна быть сказка по настроению?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TONE

async def set_tone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tone'] = update.message.text

    await update.message.reply_text(
        "Тимоша может сочинить сказку специально для тебя ☕\n"
        "Если хочешь — можешь поблагодарить его переводом: 💳 `Здесь будет номер карты или телефона`\n\n"
        "Когда отправишь — нажми 'Я оплатил', или выбери другой вариант.",
        reply_markup=ReplyKeyboardMarkup(
            [["Я оплатил 💖"], ["Хочу без оплаты 🙈"], ["Отмена"]],
            one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CONFIRM

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tone = context.user_data.get('tone', '')
    hero = context.user_data.get('hero', '')
    theme = context.user_data.get('theme', '')

    prompt = f"Сказка с героем: {hero}. Тема: {theme}. Настроение: {tone}.")
    await update.message.reply_text("Тимоша сел у камина и начал писать... 🕯")
    story = await generate_fairytale(prompt)
    await update.message.reply_text(story)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Хорошо, вернёмся к сказкам позже ☺️")
    return ConversationHandler.END

custom_story_conv = ConversationHandler(
    entry_points=[CommandHandler("custom", start_custom_story)],
    states={
        HERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_hero)],
        THEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_theme)],
        TONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_tone)],
        CONFIRM: [
            MessageHandler(filters.Regex("Я оплатил"), confirm_payment),
            MessageHandler(filters.Regex("Хочу без оплаты"), confirm_payment),
            MessageHandler(filters.Regex("Отмена"), cancel)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)