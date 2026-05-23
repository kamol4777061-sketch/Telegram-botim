import os
import telebot
from flask import Flask
import threading
from google import genai

# Muhitdan o'zgaruvchilarni o'qib olish
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("GOOGLE_API_KEY")

# Bot va Gemini Client'ni sozlash
bot = telebot.TeleBot(TOKEN)
client = genai.Client(api_key=API_KEY)

# Render'ni "uxlab qolmasligi" uchun oddiy web server
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlamoqda!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men Gemini asosidagi botman. Savollaringizni yozing.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Gemini modelidan javob olish
        response = client.models.generate_content(
           model="gemini-1.5-flash",
            contents=message.text,
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Xatolik yuz berdi: {str(e)}")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    # Flask va Botni bir vaqtda ishga tushirish
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
