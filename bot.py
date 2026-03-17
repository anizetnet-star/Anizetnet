import telebot
from telebot import types
import sqlite3

# =====================
# TOKEN (SENIKI QO‘SHILDI)
# =====================
TOKEN = "8742761350:AAFj8G3cdf1xcCOeivEpNoAtHJhJJovOHqY"

# ADMIN
ADMIN_IDS = [7991544389]

bot = telebot.TeleBot(TOKEN)

# =====================
# DATABASE
# =====================
conn = sqlite3.connect("anime.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS anime(
    code TEXT PRIMARY KEY,
    name TEXT,
    video TEXT
)
""")

conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES(?)", (user_id,))
    conn.commit()

def add_anime(code, name, video):
    cursor.execute("INSERT OR REPLACE INTO anime VALUES(?,?,?)", (code, name, video))
    conn.commit()

# TEST anime
add_anime("10", "Naruto 1-qism", "https://www.w3schools.com/html/mov_bbb.mp4")

# =====================
# START
# =====================
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)
    bot.send_message(message.chat.id, "🎬 Anime botga xush kelibsiz!\nKod yuboring (10)")

# =====================
# ANIME
# =====================
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
        bot.send_message(message.chat.id, "❌ Topilmadi")

# =====================
# VIDEO
# =====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("watch_"))
def send_video(call):
    code = call.data.split("_")[1]

    cursor.execute("SELECT * FROM anime WHERE code=?", (code,))
    data = cursor.fetchone()

    if data:
        bot.send_video(call.message.chat.id, data[2])

# =====================
# ADMIN
# =====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    bot.send_message(message.chat.id,
                     "👑 Anime qo‘shish:\ncode|nomi|video")

@bot.message_handler(func=lambda m: m.text and "|" in m.text)
def add(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        code, name, video = message.text.split("|")
        add_anime(code.strip(), name.strip(), video.strip())
        bot.send_message(message.chat.id, "✅ Qo‘shildi")
    except:
        bot.send_message(message.chat.id, "❌ Xato format")

# =====================
# RUN
# =====================
print("Bot ishga tushdi")
bot.infinity_polling()
