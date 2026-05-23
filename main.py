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

# Foydalanuvchilar suhbatini saqlash uchun lug'at (Memory)
user_histories = {}

@app.route('/')
def home():
    return "Bot ishlamoqda!"

def openrouter_so_rov(chat_id, messages):
    # Har doim o'zbek tilida gapirishni buyuramiz
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": "Sen foydali AI yordamchisan. Har doim o'zbek tilida javob ber."}]
    
    # Yangi xabarni tarixga qo'shish
    user_histories[chat_id].extend(messages)
    
    # Tarixni oxirgi 10 ta xabar bilan cheklash (xotira to'lib ketmasligi uchun)
    if len(user_histories[chat_id]) > 10:
        user_histories[chat_id] = [user_histories[chat_id][0]] + user_histories[chat_id][-9:]
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me",
        },
        json={
            # Iltimos, OpenRouter'dan aniq "Free" model ID sini tekshirib qo'ying
            "model": "google/gemini-flash-1.5-free", 
            "messages": user_histories[chat_id]
        }
    )
    
    data = response.json()
    if "error" in data:
        raise Exception(f"API xato: {data['error'].get('message', data['error'])}")
    
    javob = data["choices"][0]["message"]["content"]
    
    # Javobni tarixga qo'shish
    user_histories[chat_id].append({"role": "assistant", "content": javob})
    return javob

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_histories[message.chat.id] = [{"role": "system", "content": "Sen foydali AI yordamchisan. Har doim o'zbek tilida javob ber."}]
    bot.reply_to(message, "Salom! Men AI botman 🤖. Endi men suhbatni eslab qolaman!")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        javob = openrouter_so_rov(message.chat.id, [{"role": "user", "content": message.text}])
        
        if len(javob) > 4000:
            for i in range(0, len(javob), 4000):
                bot.reply_to(message, javob[i:i+4000])
        else:
            bot.reply_to(message, javob)
    except Exception as e:
        bot.reply_to(message, f"❌ Xato: {str(e)}")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
