import os
import requests
import base64
import telebot
from flask import Flask
import threading

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlamoqda!"

def openrouter_matn(matn):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {"role": "user", "content": matn}
            ]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

def openrouter_rasm(rasm_bytes, caption="Bu rasmda nima bor?"):
    rasm_base64 = base64.b64encode(rasm_bytes).decode("utf-8")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{rasm_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": caption
                        }
                    ]
                }
            ]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "Salom! Men AI botman 🤖\n\n"
        "✍️ Matn yozing — javob beraman\n"
        "🖼 Rasm yuboring — tahlil qilaman"
    )

# Matn xabarlar
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        javob = openrouter_matn(message.text)
        bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

# Rasm xabarlar
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Eng sifatli rasmni olish
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        rasm_bytes = requests.get(file_url).content
        
        # Caption (izoh) bo'lsa uni, bo'lmasa standart savol
        caption = message.caption if message.caption else "Bu rasmda nima bor? Batafsil tushuntir."
        
        javob = openrouter_rasm(rasm_bytes, caption)
        bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
