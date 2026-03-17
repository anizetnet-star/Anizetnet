import telebot
from telebot import types
import sqlite3
import time
import threading
import os
from flask import Flask

# ===================== TOKEN VA ADMIN =====================
# Replit Secrets da saqlash tavsiya etiladi, lekin to‘g‘ridan-to‘g‘ri ham yozish mumkin
TOKEN = os.environ.get("TOKEN", "8742761350:AAFj8G3cdf1xcCOeivEpNoAtHJhJJovOHqY")
ADMIN_IDS = [int(os.environ.get("ADMIN_ID", "7991544389"))]

bot = telebot.TeleBot(TOKEN)

# ===================== DATABASE =====================
conn = sqlite3.connect("anime.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS anime(code TEXT PRIMARY KEY, name TEXT, video TEXT)")
conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

def add_anime(code, name, video):
    cursor.execute("INSERT OR REPLACE INTO anime VALUES(?,?,?)", (code, name, video))
    conn.commit()

# Test anime (o‘chirib tashlashingiz mumkin)
add_anime("10", "Naruto 1-qism", "https://www.w3schools.com/html/mov_bbb.mp4")

# ===================== START (INLINE MENYU) =====================
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 Anime izlash", callback_data="search"),
        types.InlineKeyboardButton("👑 VIP", callback_data="vip"),
        types.InlineKeyboardButton("📋 Maʼlumot", callback_data="info"),
        types.InlineKeyboardButton("📢 Reklama", callback_data="ads")
    )
    
    bot.send_message(
        message.chat.id,
        "🎬 Anime botga xush kelibsiz!\nQuyidagi tugmalardan birini tanlang:",
        reply_markup=markup
    )

# ===================== INLINE TUGMALAR JAVOBI =====================
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "search":
        bot.send_message(call.message.chat.id, "🔍 Anime kodini yozing (masalan: 10)")
    elif call.data == "vip":
        bot.send_message(call.message.chat.id, "👑 VIP funksiyasi keyinroq qo‘shiladi.")
    elif call.data == "info":
        bot.send_message(call.message.chat.id, "📋 Bu bot orqali siz anime kodlarini yuborib, videolarni yuklab olishingiz mumkin.")
    elif call.data == "ads":
        bot.send_message(call.message.chat.id, "📢 Reklama va hamkorlik: @admin")
    
    bot.answer_callback_query(call.id)

# ===================== ANIME KODLARINI QABUL QILISH =====================
@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def get_anime(message):
    code = message.text
    cursor.execute("SELECT * FROM anime WHERE code=?", (code,))
    data = cursor.fetchone()
    if data:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Yuklash", callback_data=f"watch_{code}"))
        bot.send_message(message.chat.id, f"🎬 {data[1]}", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Bunday kod topilmadi")

# ===================== VIDEO YUBORISH =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("watch_"))
def send_video(call):
    code = call.data.split("_")[1]
    cursor.execute("SELECT video FROM anime WHERE code=?", (code,))
    video_url = cursor.fetchone()
    if video_url:
        bot.send_video(call.message.chat.id, video_url[0])
    bot.answer_callback_query(call.id)

# ===================== ADMIN PANELI =====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(message.chat.id, "👑 Anime qo‘shish: format: code|nomi|video")

@bot.message_handler(func=lambda m: m.text and "|" in m.text)
def add_anime_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        code, name, video = message.text.split("|")
        add_anime(code.strip(), name.strip(), video.strip())
        bot.send_message(message.chat.id, "✅ Qo‘shildi")
    except:
        bot.send_message(message.chat.id, "❌ Xato format")

# ===================== FLASK SERVER (REPLIT UCHUN) =====================
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot ishlayapti!"

def run_bot():
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"Bot xatosi: {e}, qayta ishga tushirilmoqda...")
            time.sleep(5)

# Botni alohida threadda ishga tushirish
threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
