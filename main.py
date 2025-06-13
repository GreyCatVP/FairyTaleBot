import os
import smtplib
from email.mime.text import MIMEText
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Переменные окружения
TOKEN = os.environ.get("TOKEN")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")

print(f"🔐 Бот запускается с токеном: {TOKEN}")

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 Команда /start получена")
    await update.message.reply_text("Привет! Введите кодовое слово:")

# Обработка текстового сообщения (кодовое слово)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("➡️ handle_message вызван")
    print("📨 Получено сообщение:", update.message.text)
    context.user_data["codeword"] = update.message.text

    button = KeyboardButton("Отправить номер телефона", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Спасибо! Теперь нажмите кнопку, чтобы отправить номер телефона:",
        reply_markup=keyboard
    )

# Обработка контакта (номер телефона)
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("➡️ handle_contact вызван")
    contact = update.message.contact
    user = update.effective_user
    codeword = context.user_data.get("codeword", "—")

    email_text = f"""Новый купон!

🔤 Кодовое слово: "{codeword}"
📱 Телефон: {contact.phone_number}
👤 Telegram: @{user.username}
Имя в Telegram: {user.full_name}
"""

    print("📧 Отправка письма...")
    try:
        msg = MIMEText(email_text)
        msg["Subject"] = "Новый купон"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("📧 Письмо успешно отправлено!")

        await update.message.reply_text(
            "Спасибо! Купон будет активирован в течении 24 часов.\n"
            "Кстати, Вы подписаны на наши соцсети?\n\n"
            "📲 Вот где мы делимся новостями, вкусными находками и хорошим настроением:\n\n"
            "🔹 Instagram — https://instagram.com/2coffeemaniacs\n"
            "🔹 Telegram — https://t.me/TwoCoffeeManiacs\n"
            "🔹 Facebook — https://facebook.com/2coffeemaniacs\n"
            "🔹 ВКонтакте — https://vk.com/2coffeemaniacs"
        )
    except Exception as e:
        print(f"📧 Ошибка отправки email: {e}")
        await update.message.reply_text("Произошла ошибка при отправке. Попробуйте позже.")

# Запуск сервера для Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Service is up")

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 8080), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    threading.Thread(target=run_dummy_server, daemon=True).start()

    print("✅ Polling запущен — бот слушает команды")
    app.run_polling()
