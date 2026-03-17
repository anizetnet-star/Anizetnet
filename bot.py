import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime
import time
import threading
import logging

# ============================================
# SOZLAMALAR (o‘zgartirish shart emas)
# ============================================
TOKEN = os.environ.get('8742761350:AAH5wjasaAZkYsOxvPyHC1Nh-MLRB0GfXho')
ADMIN_IDS = [int(os.environ.get('7991544389'))]

bot = telebot.TeleBot(TOKEN)

# Logging (xatolarni kuzatish uchun)
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# ============================================
# MAJBURIY KANAL – FAQAT @Anizet
# ============================================
REQUIRED_CHANNELS = [
    {"name": "ANIZET.UZ", "username": "@Anizet", "link": "https://t.me/Anizet"}
]

# Bot holati (o‘chirish/yoqish)
BOT_ACTIVE = True
MAINTENANCE_MESSAGE = """
⚠️ Bot texnik ishlar tufayli vaqtincha ishlamaydi.
Iltimos, keyinroq urinib ko‘ring.
"""

# ============================================
# MAʼLUMOTLAR BAZASI (SQLite)
# ============================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('anime.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TEXT,
                last_active TEXT
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username, first_name):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date, last_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Foydalanuvchi qo‘shishda xatolik: {e}")

    def update_user_activity(self, user_id):
        try:
            self.cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?',
                                (datetime.now().isoformat(), user_id))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Faollikni yangilashda xatolik: {e}")

    def get_users_count(self):
        try:
            self.cursor.execute('SELECT COUNT(*) FROM users')
            return self.cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Statistika olishda xatolik: {e}")
            return 0

    def get_all_users(self):
        try:
            self.cursor.execute('SELECT user_id FROM users')
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Foydalanuvchilar ro‘yxatini olishda xatolik: {e}")
            return []

db = Database()

# ============================================
# OBUNANI TEKSHIRISH FUNKSIYALARI
# ============================================
def check_subscription(user_id):
    """Foydalanuvchi @Anizet kanaliga obuna bo‘lganmi?"""
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except Exception as e:
            logging.error(f"Kanal tekshirishda xatolik: {e}")
            not_subscribed.append(channel)  # Xatolik bo‘lsa, obuna talab qilish
    return not_subscribed

def show_subscription_menu(message, not_subscribed):
    """Obuna talab qilish menyusini ko‘rsatish"""
    text = "🔒 <b>MAJBURIY OBUNA</b>\n\nBotdan foydalanish uchun quyidagi kanalga obuna bo'ling:\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in not_subscribed:
        text += f"• {channel['name']}\n"
        markup.add(types.InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link']))
    markup.add(types.InlineKeyboardButton("✅ TEKSHIRISH", callback_data="check_subscription"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ============================================
# ASOSIY MENYU (foydalanuvchi uchun)
# ============================================
def show_main_menu(message):
    text = """
🎬 <b>ANIZETNET | Uzbek</b>
👥 <b>42,828 oylik foydalanuvchi</b>

<b>ANIMEDAN KADRLAR KO'RISH 😊</b>

@Anizet

Anime kodini yuboring (masalan: 10)
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

def show_download_button(message, anime_code):
    # Bu yerda anime nomini bazadan olish kerak, hozircha placeholder
    text = f"🎬 {anime_code} kodli anime tanlandi.\nQismlarni yuklab olish uchun tugmani bosing."
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📥 YUKLAB OLISH", callback_data=f"episodes_{anime_code}")
    markup.add(btn)
    bot.send_message(message.chat.id, text, reply_markup=markup)

# ============================================
# ADMIN PANELI (6 TA TUGMA)
# ============================================
def show_admin_panel(message):
    text = "👑 <b>Admin paneliga xush kelibsiz!</b>"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast"),
        types.InlineKeyboardButton("🔒 Majburiy obunalar", callback_data="forced_subs"),
        types.InlineKeyboardButton("👥 Adminlar", callback_data="admins"),
        types.InlineKeyboardButton("💎 VIP", callback_data="vip"),
        types.InlineKeyboardButton("⚙️ Tizim sozlamalari", callback_data="settings_menu"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ============================================
# CALLBACK HANDLER (barcha tugmalar uchun)
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    # Admin panel tugmalari faqat admin uchun
    if call.data in ["admin_stats", "broadcast", "forced_subs", "admins", "vip", "settings_menu"]:
        if user_id not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Siz admin emassiz!", show_alert=True)
            return

    # Statistika
    if call.data == "admin_stats":
        count = db.get_users_count()
        bot.answer_callback_query(call.id, f"👥 Foydalanuvchilar soni: {count}", show_alert=True)

    # Xabar yuborish
    elif call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 Yubormoqchi bo‘lgan xabarni kiriting:")
        bot.register_next_step_handler(msg, process_broadcast)

    # Majburiy obunalar ro‘yxati
    elif call.data == "forced_subs":
        text = "🔒 Majburiy obuna kanallari:\n"
        for ch in REQUIRED_CHANNELS:
            text += f"• {ch['name']} ({ch['username']})\n"
        bot.send_message(call.message.chat.id, text)

    # Adminlar ro‘yxati
    elif call.data == "admins":
        text = "👥 Adminlar:\n" + "\n".join(str(a) for a in ADMIN_IDS)
        bot.send_message(call.message.chat.id, text)

    # VIP (placeholder)
    elif call.data == "vip":
        bot.send_message(call.message.chat.id, "💎 VIP funksiyasi keyinroq qo'shiladi.")

    # Sozlamalar menyusi
    elif call.data == "settings_menu":
        show_settings_menu(call.message)

    # Orqaga (asosiy menyu)
    elif call.data == "back_to_main":
        show_main_menu(call.message)

    # Obuna tekshirish tugmasi
    elif call.data == "check_subscription":
        check_subscription_callback(call)

    # Anime qismlar (placeholder)
    elif call.data.startswith("episodes_"):
        bot.answer_callback_query(call.id, "Bu funksiya hozircha ishga tushmagan.")

# ============================================
# XABAR YUBORISH (BROADCAST)
# ============================================
def process_broadcast(message):
    text = message.text
    users = db.get_all_users()
    sent = 0
    for user in users:
        try:
            bot.send_message(user[0], text)
            sent += 1
            time.sleep(0.05)  # 1 sekundda 20 ta xabar
        except Exception as e:
            logging.warning(f"Xabar yuborilmadi {user[0]}: {e}")
            continue
    bot.reply_to(message, f"✅ Xabar {sent} foydalanuvchiga yuborildi.")

# ============================================
# SOZLAMALAR MENYUSI (botni o‘chirish/yoqish)
# ============================================
def show_settings_menu(message):
    global BOT_ACTIVE
    status = "🟢 FAOL" if BOT_ACTIVE else "🔴 O'CHIRILGAN"
    text = f"⚙️ Tizim sozlamalari\n\nHolat: {status}"
    markup = types.InlineKeyboardMarkup()
    if BOT_ACTIVE:
        markup.add(types.InlineKeyboardButton("🔴 Botni o'chirish", callback_data="turn_off"))
    else:
        markup.add(types.InlineKeyboardButton("🟢 Botni yoqish", callback_data="turn_on"))
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="admin_panel"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["turn_off", "turn_on", "admin_panel"])
def settings_actions(call):
    global BOT_ACTIVE
    if call.data == "turn_off":
        BOT_ACTIVE = False
        bot.answer_callback_query(call.id, "Bot o‘chirildi")
    elif call.data == "turn_on":
        BOT_ACTIVE = True
        bot.answer_callback_query(call.id, "Bot yoqildi")
    elif call.data == "admin_panel":
        show_admin_panel(call.message)
        return
    show_settings_menu(call.message)

# ============================================
# OBUNA TEKSHIRISH CALLBACK
# ============================================
def check_subscription_callback(call):
    user_id = call.from_user.id
    not_sub = check_subscription(user_id)
    if not not_sub:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎬 ASOSIY MENYU", callback_data="back_to_main"))
        bot.edit_message_text("✅ <b>OBUNA MUVAFFAQIYATLI!</b>",
                              call.message.chat.id, call.message.message_id,
                              parse_mode='HTML', reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "Siz hali kanalga obuna bo‘lmagansiz!", show_alert=True)

# ============================================
# BARCHA XABARLARNI QAYTA ISHLASH
# ============================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global BOT_ACTIVE
    user_id = message.from_user.id
    text = message.text.strip()

    # Foydalanuvchini bazaga qo‘shish (har qanday xabar kelganda)
    db.add_user(user_id, message.from_user.username, message.from_user.first_name)

    # Admin panelga kirish
    if user_id in ADMIN_IDS and text in ['/admin', '/panel']:
        show_admin_panel(message)
        return

    # Bot o‘chirilgan bo‘lsa
    if not BOT_ACTIVE and user_id not in ADMIN_IDS:
        bot.send_message(user_id, MAINTENANCE_MESSAGE)
        return

    # /start komandasi
    if text == '/start':
        # Obunani tekshirish
        not_sub = check_subscription(user_id)
        if not_sub:
            show_subscription_menu(message, not_sub)
        else:
            show_main_menu(message)
        return

    # Raqamli kod (10,20,30...)
    if text.isdigit():
        # Obunani tekshirish
        not_sub = check_subscription(user_id)
        if not_sub:
            show_subscription_menu(message, not_sub)
        else:
            # Kodni qabul qilish (hozircha faqat 10,20,30)
            if text in ['10', '20', '30']:
                show_download_button(message, text)
            else:
                bot.reply_to(message, "❌ Noto‘g‘ri kod. Mavjud kodlar: 10, 20, 30")
        return

    # Boshqa xabarlar
    bot.reply_to(message, "❌ Tushunarsiz buyruq. /start bosing")

# ============================================
# FLASK SERVER (HOSTING UCHUN)
# ============================================
try:
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "AnizetNet Bot ishlayapti!"

    @app.route('/health')
    def health():
        return "OK", 200

    def run_flask():
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
except ImportError:
    pass

# ============================================
# BOTNI ISHGA TUSHIRISH
# ============================================
if __name__ == "__main__":
    print("🚀 AnizetNet Bot ishga tushdi!")
    print(f"Admin panel: /admin yoki /panel")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logging.error(f"Bot to‘xtadi: {e}")
            print(f"Xatolik: {e}, 5 soniyadan so‘ng qayta ishga tushiriladi...")
            time.sleep(5)
