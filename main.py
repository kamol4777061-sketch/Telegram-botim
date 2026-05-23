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

def openrouter_so_rov(messages):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me",
        },
        json={
            # Eng sodda va universal model
            "model": "openai/gpt-3.5-turbo", 
            "messages": messages
        }
    )
    
    # Nima javob kelayotganini terminalda ko'rish uchun:
    print(f"DEBUG: Status kod: {response.status_code}")
    print(f"DEBUG: Javob matni: {response.text}")
    
    data = response.json()
    if "error" in data:
        raise Exception(f"API xato: {data['error'].get('message', data['error'])}")
    
    return data["choices"][0]["message"]["content"]

# /start komandasi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men AI botman 🤖\nMatn yozing yoki rasm yuboring.")

# Barcha matnli xabarlar uchun handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        javob = openrouter_so_rov([{"role": "user", "content": message.text}])
        
        # Uzun javobni bo'lish
        if len(javob) > 4000:
            for i in range(0, len(javob), 4000):
                bot.reply_to(message, javob[i:i+4000])
        else:
            bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ Xato: {str(e)}")

# Rasm xabarlar uchun handler
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        rasm_bytes = requests.get(file_url).content
        rasm_base64 = base64.b64encode(rasm_bytes).decode("utf-8")
        caption = message.caption if message.caption else "Bu rasmda nima bor?"

        javob = openrouter_so_rov([
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{rasm_base64}"}},
                {"type": "text", "text": caption}
            ]}
        ])
        bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ Xato: {str(e)}")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
