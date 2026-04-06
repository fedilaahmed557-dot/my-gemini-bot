import os
import telebot
from telebot import types
import sqlite3
import google.generativeai as genai
import PIL.Image
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_KEY = os.getenv("GEMINI_API_KEY") 
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
ADMIN_ID = 7268036089  
ID_PRICE = 30 

# --- UPTIME SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Eza AI Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT SETUP ---
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')
bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE ---
def db_query(query, params=(), fetch=False):
    conn = sqlite3.connect('national_id.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

db_query('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)''')

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    db_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🪪 መታወቂያ ቀይር (30 ብር)", "💰 ሂሳብ ማሳያ")
    markup.add("💳 ብር መሙያ (Deposit)", "📞 ድጋፍ")
    bot.send_message(user_id, "ሰላም! እንኳን ወደ ኢዛ ሊጋል አይ በሰላም መጡ። 👋", reply_markup=markup)

# ... (ሌሎች Handlers እዚህ ይቀጥላሉ)

if __name__ == "__main__":
    keep_alive()
    print("ቦቱ ስራ ጀምሯል...")
    bot.infinity_polling()
