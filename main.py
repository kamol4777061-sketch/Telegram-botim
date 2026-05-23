import os
import requests
import base64
import telebot
from flask import Flask
import threading

# API kalitlarini muhit o'zgaruvchilaridan (Environment variables) oladi
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlamoqda!"

def openrouter_so_rov(messages):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me",
        },
        json={
            # Xatolik shu yerda edi, model nomi yangilandi:
        
            # Bu ID hozirda eng ko'p ishlatiladigan va bepul modellardan biri:
            "model": "google/gemini-2.0-flash-lite-preview",
            "messages": messages
    
        }
    )
    data = response.json()
    
    if "error" in data:
        raise Exception(f"API xato: {data['error'].get('message', data['error'])}")
    
    if "choices" not in data or len(data["choices"]) == 0:
        raise Exception(f"Bo'sh javob: {data}")
    
    return data["choices"][0]["message"]["content"]

# /start komandasi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
        "Salom! Men AI botman 🤖\n\n"
        "✍️ Matn yozing — javob beraman\n"
        "🖼 Rasm yuboring — tahlil qilaman"
    )

# Matn xabarlar uchun
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        javob = openrouter_so_rov([
            {"role": "user", "content": message.text}
        ])
        bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ {str(e)}")

# Rasm xabarlar uchun
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        rasm_bytes = requests.get(file_url).content
        rasm_base64 = base64.b64encode(rasm_bytes).decode("utf-8")

        caption = message.caption if message.caption else "Bu rasmda nima bor? Batafsil tushuntir."

        javob = openrouter_so_rov([
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{rasm_base64}"}
                    },
                    {"type": "text", "text": caption}
                ]
            }
        ])
        bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ {str(e)}")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    # Flask serverini orqa fonda ishga tushirish
    threading.Thread(target=run_flask).start()
    # Botni ishga tushirish
    bot.infinity_polling()
