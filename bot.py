import os
import telebot
from telebot import types
import sqlite3
import google.generativeai as genai
import PIL.Image
from flask import Flask
from threading import Thread

# --- CONFIG (እነዚህን ቁጥሮች በ Render Dashboard ላይ ነው የምንሞላቸው) ---
API_KEY = os.getenv("GEMINI_API_KEY") 
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
ADMIN_ID = 7268036089  
ID_PRICE = 30 

# --- ሰርቨሩ እንዳይተኛ (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Eza AI Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ቦት እና Gemini ዝግጅት ---
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
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

# --- ዋና ሜኑ (Buttons) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🪪 መታወቂያ ቀይር (30 ብር)", "💰 ሂሳብ ማሳያ")
    markup.add("💳 ብር መሙያ (Deposit)", "📞 ድጋፍ")
    return markup

# --- ቦት ትዕዛዞች (Handlers) ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    db_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    bot.send_message(user_id, "ሰላም! እንኳን ወደ ኢዛ ሊጋል አይ (Eza Legal AI) በሰላም መጡ። 👋", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "💰 ሂሳብ ማሳያ")
def show_balance(message):
    res = db_query("SELECT balance FROM users WHERE user_id=?", (message.chat.id,), fetch=True)
    balance = res[0][0] if res else 0
    bot.reply_to(message, f"💳 ያሎት ቀሪ ሂሳብ፦ {balance} ብር")

@bot.message_handler(func=lambda m: m.text == "💳 ብር መሙያ (Deposit)")
def deposit_info(message):
    msg = f"📍 ብር ለመሙላት፦\n\n1. በቴሌብር ወደ ስልክ፦ `0929277255` ይላኩ።\n2. የላኩበትን ደረሰኝ ለአድሚን ይላኩ።\n\nየእርስዎ መለያ (ID)፦ `{message.chat.id}`"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🪪 መታወቂያ ቀይር (30 ብር)")
def ask_id(message):
    bot.reply_to(message, "እባክዎ የመታወቂያውን ፎቶ በጥራት ይላኩ።")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    res = db_query("SELECT balance FROM users WHERE user_id=?", (user_id,), fetch=True)
    balance = res[0][0] if res else 0

    if balance < ID_PRICE:
        bot.reply_to(message, f"⚠️ ይቅርታ፣ አገልግሎቱን ለመጠቀም {ID_PRICE} ብር ያስፈልጋል።")
        return

    bot.reply_to(message, "🔄 Gemini መረጃውን እያነበበ ነው... ጥቂት ይጠብቁ።")

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        path = "id_image.jpg"
        with open(path, 'wb') as f: f.write(downloaded_file)

        img = PIL.Image.open(path)
        prompt = "Extract Name, ID number, and Birth Date from this card clearly in Amharic or English as seen."
        response = model.generate_content([prompt, img])
        
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (ID_PRICE, user_id))
        bot.send_message(user_id, f"✅ የተገኘ መረጃ፦\n\n{response.text}")
        bot.send_message(ADMIN_ID, f"🔔 አዲስ ስራ ተሰርቷል (ID: {user_id})")
        if os.path.exists(path): os.remove(path)
    except Exception as e:
        bot.reply_to(message, "❌ ስህተት ተፈጥሯል! እባክዎ ድጋሚ ይሞክሩ።")

@bot.message_handler(commands=['add'])
def add_money(message):
    if message.chat.id == ADMIN_ID:
        try:
            _, t_id, amount = message.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(amount), int(t_id)))
            bot.send_message(t_id, f"🎉 ሂሳብዎ በ {amount} ብር ታድሷል!")
            bot.reply_to(message, "✅ ተሳክቷል!")
        except:
            bot.reply_to(message, "አጠቃቀም፦ /add [ID] [Amount]")

if __name__ == "__main__":
    keep_alive()
    print("ቦቱ ስራ ጀምሯል...")
    bot.infinity_polling()
