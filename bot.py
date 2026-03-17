import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime
import time
import threading

# ============================================
# SOZLAMALAR (OʻZINGIZNING MAʼLUMOTLARINGIZ)
# ============================================
TOKEN = os.environ.get('TOKEN', '8742761350:AAH5wjasaAZkYsOxvPyHC1Nh-MLRB0GfXho')
ADMIN_IDS = [int(os.environ.get('ADMIN_ID', '7991544389'))]  # Sizning ID

bot = telebot.TeleBot(TOKEN)

# ============================================
# MAJBURIY KANAL – FAQAT @Anizet
# ============================================
REQUIRED_CHANNELS = [
    {
        "name": "ANIZET.UZ",
        "username": "@Anizet",
        "link": "https://t.me/Anizet"
    }
]

# ============================================
# BOT HOLATI (OʻCHIRISH/YOQISH)
# ============================================
BOT_ACTIVE = True
MAINTENANCE_MESSAGE = """
Hurmatli ANIZET.UZ foydalanuvchilari! 👥

🤖 @Anizet_netbot botimiz 15.03.2026-soat 22:59 gacha ta'mirlash holatida bo'ladi. 🛠

Sizga sogʻlik va omad tilaymiz! 🌟
Keyinchalik bot optimallashtiriladi va xizmatlardan xotirjam foydalanishingiz mumkin boʻladi. 🚀

Tushunganingiz uchun rahmat! ❤️
"""

# ============================================
# MAʼLUMOTLAR BAZASI
# ============================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('anime.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.init_sample_data()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS anime (
                kod TEXT PRIMARY KEY,
                nomi TEXT NOT NULL,
                qismlar_soni INTEGER DEFAULT 0,
                janri TEXT,
                tili TEXT DEFAULT "O'zbekcha",
                yili INTEGER,
                kanal TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_kod TEXT,
                qism_raqami INTEGER,
                file_id TEXT,
                FOREIGN KEY (anime_kod) REFERENCES anime (kod)
            )
        ''')
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

    def init_sample_data(self):
        anime_list = [
            ("10", "Qora klever", 170, "Jangari, Sarguzasht", "O'zbekcha", 2022, "@Anizet"),
            ("20", "Jujutsu Kaisen", 24, "Jangari, Fantastika", "O'zbekcha", 2020, "@Anizet"),
            ("30", "Demon Slayer", 26, "Jangari, Drama", "O'zbekcha", 2019, "@Anizet"),
        ]
        for a in anime_list:
            self.cursor.execute('''
                INSERT OR IGNORE INTO anime (kod, nomi, qismlar_soni, janri, tili, yili, kanal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', a)
        self.conn.commit()

    def get_anime(self, kod):
        self.cursor.execute('SELECT * FROM anime WHERE kod = ?', (kod,))
        return self.cursor.fetchone()

    def get_all_anime(self):
        self.cursor.execute('SELECT * FROM anime ORDER BY qismlar_soni DESC')
        return self.cursor.fetchall()

    def add_user(self, user_id, username, first_name):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date, last_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
            self.conn.commit()
        except:
            pass

    def update_user_activity(self, user_id):
        self.cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?',
                           (datetime.now().isoformat(), user_id))
        self.conn.commit()

    def save_video(self, kod, qism, file_id):
        self.cursor.execute('''
            INSERT OR REPLACE INTO videos (anime_kod, qism_raqami, file_id)
            VALUES (?, ?, ?)
        ''', (kod, qism, file_id))
        self.conn.commit()

    def get_video(self, kod, qism):
        self.cursor.execute('SELECT file_id FROM videos WHERE anime_kod = ? AND qism_raqami = ?', (kod, qism))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_users_count(self):
        self.cursor.execute('SELECT COUNT(*) FROM users')
        return self.cursor.fetchone()[0]

db = Database()

# ============================================
# OBUNANI TEKSHIRISH FUNKSIYASI (MAJBURIY)
# ============================================
def check_subscription(user_id):
    """Foydalanuvchi @Anizet kanaliga obuna bo'lganmi?"""
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except Exception as e:
            # Agar bot kanalda admin bo'lmasa, xatolik yuz beradi – bu holatda obunani talab qilamiz
            print(f"Kanalni tekshirishda xatolik: {e}")
            not_subscribed.append(channel)
    return not_subscribed

def show_subscription_menu(message, not_subscribed=None):
    """Obuna talab qilinadigan menyuni ko‘rsatish"""
    if not_subscribed is None:
        not_subscribed = check_subscription(message.from_user.id)

    if not not_subscribed:
        # Hammasi obuna – asosiy menyuga o‘tish
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🎬 ASOSIY MENYU", callback_data="main_menu")
        markup.add(btn)
        bot.send_message(message.chat.id, "✅ <b>OBUNA MUVAFFAQIYATLI!</b>", parse_mode='HTML', reply_markup=markup)
        return True

    # Obuna bo‘lmagan kanallar bor
    text = "🔒 <b>MAJBURIY OBUNA</b>\n\nBotdan foydalanish uchun quyidagi kanalga obuna bo'ling:\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in not_subscribed:
        text += f"• {channel['name']}\n"
        markup.add(types.InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link']))
    markup.add(types.InlineKeyboardButton("✅ TEKSHIRISH", callback_data="check_subscription"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    return False

# ============================================
# BARCHA XABARLARNI FILTRLASH
# ============================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global BOT_ACTIVE
    user_id = message.from_user.id

    # Admin maxsus buyruqlari – har doim ishlaydi
    if user_id in ADMIN_IDS:
        if message.text in ['/admin', '/panel']:
            show_admin_panel(message)
            return
        elif message.text in ['/settings', '/sozlamalar']:
            show_settings_panel(message)
            return
        elif message.text == '/status':
            status = "🟢 FAOL" if BOT_ACTIVE else "🔴 O'CHIRILGAN"
            bot.reply_to(message, f"🤖 Bot holati: {status}")
            return

    # Bot o‘chirilgan bo‘lsa, faqat xabar chiqarish
    if not BOT_ACTIVE:
        bot.send_message(user_id, MAINTENANCE_MESSAGE)
        return

    # Normal ishlash – avval obunani tekshirish
    db.update_user_activity(user_id)
    text = message.text.strip()

    # Har qanday xabar kelganda obunani tekshiramiz (startdan tashqari)
    # Agar /start bo‘lsa, alohida ishlaymiz
    if text == '/start':
        args = message.text.split()
        if len(args) > 1:  # start kodi bilan kelgan bo‘lsa
            kod = args[1]
            anime = db.get_anime(kod)
            if anime:
                not_subscribed = check_subscription(user_id)
                if not_subscribed:
                    show_subscription_menu(message, not_subscribed)
                else:
                    show_download_button(message, anime)
                return
        # Oddiy start
        not_subscribed = check_subscription(user_id)
        if not_subscribed:
            show_subscription_menu(message, not_subscribed)
        else:
            show_main_menu(message)
        return

    # Agar foydalanuvchi raqam (kod) yozsa
    if text.isdigit():
        kod = text
        anime = db.get_anime(kod)
        if anime:
            not_subscribed = check_subscription(user_id)
            if not_subscribed:
                show_subscription_menu(message, not_subscribed)
            else:
                show_download_button(message, anime)
            return

    # Agar boshqa matn bo‘lsa
    not_subscribed = check_subscription(user_id)
    if not_subscribed:
        show_subscription_menu(message, not_subscribed)
    else:
        bot.reply_to(message, "❌ Tushunarsiz buyruq. /start bosing")

# ============================================
# ASOSIY MENYU
# ============================================
def show_main_menu(message):
    text = """
🎬 <b>ANIZETNET | Uzbek</b>
👥 <b>42,828 oylik foydalanuvchi</b>

<b>ANIMEDAN KADRLAR KO'RISH 🎮</b>

@Anizet

Anime kodini yuboring (masalan: 10)
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

def show_download_button(message, anime):
    text = f"""
🎬 <b>ANIZETNET | Uzbek</b>
👥 <b>42,828 oylik foydalanuvchi</b>

<b>ANIMEDAN KADRLAR KO'RISH 🎮</b>

@Anizet

<b>{anime[1]}</b>
📺 {anime[2]} qism
    """
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📥 YUKLAB OLISH", callback_data=f"episodes_{anime[0]}")
    markup.add(btn)
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ============================================
# QISMLAR RO'YXATI
# ============================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("episodes_"))
def show_episodes(call):
    kod = call.data.replace("episodes_", "")
    anime = db.get_anime(kod)
    text = f"""
🎬 <b>{anime[1]}</b>
📺 <b>{anime[2]} QISM</b>

Qismni tanlang:
    """
    markup = types.InlineKeyboardMarkup(row_width=5)
    qismlar = min(anime[2], 25)  # Eng ko‘pi 25 ta qism ko‘rsatiladi
    buttons = []
    for i in range(1, qismlar + 1):
        buttons.append(types.InlineKeyboardButton(str(i), callback_data=f"video_{kod}_{i}"))
    # 5 tadan qilib joylash
    for i in range(0, len(buttons), 5):
        markup.add(*buttons[i:i+5])
    markup.add(types.InlineKeyboardButton("🔙 ORQAGA", callback_data=f"back_{kod}"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("video_"))
def send_video(call):
    parts = call.data.split("_")
    kod = parts[1]
    qism = parts[2]
    anime = db.get_anime(kod)
    file_id = db.get_video(kod, qism)
    text = f"🎬 <b>{anime[1]} - {qism}-QISM</b>"

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Oldingi qism tugmasi
    if int(qism) > 1:
        prev_btn = types.InlineKeyboardButton("⬅️", callback_data=f"video_{kod}_{int(qism)-1}")
    else:
        prev_btn = types.InlineKeyboardButton("⬅️", callback_data="none")

    # Keyingi qism tugmasi
    if int(qism) < anime[2]:
        next_btn = types.InlineKeyboardButton("➡️", callback_data=f"video_{kod}_{int(qism)+1}")
    else:
        next_btn = types.InlineKeyboardButton("➡️", callback_data="none")

    back_btn = types.InlineKeyboardButton("📋 QISMLAR", callback_data=f"episodes_{kod}")

    markup.add(prev_btn, next_btn)
    markup.add(back_btn)

    if file_id:
        bot.send_video(call.message.chat.id, file_id, caption=text, parse_mode='HTML', reply_markup=markup)
    else:
        # Video hali qo‘shilmagan bo‘lsa
        demo_text = f"{text}\n\n❌ Video hali qo'shilmagan. Admin tez orada qo'shadi."
        bot.send_message(call.message.chat.id, demo_text, parse_mode='HTML', reply_markup=markup)

    bot.answer_callback_query(call.id, f"{qism}-qism")

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
def back_to_download(call):
    kod = call.data.replace("back_", "")
    anime = db.get_anime(kod)
    show_download_button(call.message, anime)

# ============================================
# OBUNA TEKSHIRISH CALLBACK
# ============================================
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    not_subscribed = check_subscription(user_id)

    if not not_subscribed:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🎬 ASOSIY MENYU", callback_data="main_menu")
        markup.add(btn)
        bot.edit_message_text("✅ <b>OBUNA MUVAFFAQIYATLI!</b>", call.message.chat.id,
                             call.message.message_id, parse_mode='HTML', reply_markup=markup)
    else:
        text = "⚠️ <b>QUYIDAGI KANALGA OBUNA BO'LMAGANSIZ:</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for channel in not_subscribed:
            text += f"❌ {channel['name']}\n"
            markup.add(types.InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link']))
        markup.add(types.InlineKeyboardButton("✅ QAYTA TEKSHIRISH", callback_data="check_subscription"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_callback(call):
    show_main_menu(call.message)

# ============================================
# ADMIN PANELI
# ============================================
def show_admin_panel(message):
    text = "👑 <b>ADMIN PANELI</b>\n\nBoshqaruv panelidasiz"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚙️ Tizim sozlamalari", callback_data="settings_menu"),
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="user_list"),
        types.InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast_menu"),
        types.InlineKeyboardButton("🎬 Anime qo'shish", callback_data="add_anime_menu"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "settings_menu")
def settings_menu(call):
    show_settings_panel(call.message)

def show_settings_panel(message):
    global BOT_ACTIVE
    status = "🟢 FAOL" if BOT_ACTIVE else "🔴 O'CHIRILGAN"
    text = f"⚙️ <b>TIZIM SOZLAMALARI</b>\n\n🤖 Bot holati: {status}"
    markup = types.InlineKeyboardMarkup(row_width=2)

    if BOT_ACTIVE:
        markup.add(types.InlineKeyboardButton("🔴 Botni o'chirish", callback_data="bot_turn_off"))
    else:
        markup.add(types.InlineKeyboardButton("🟢 Botni yoqish", callback_data="bot_turn_on"))

    markup.add(
        types.InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast_menu"),
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_admin")
    )
    if not BOT_ACTIVE:
        markup.add(types.InlineKeyboardButton("✏️ Xabarni o'zgartirish", callback_data="edit_message"))

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "bot_turn_off")
def turn_off_bot(call):
    global BOT_ACTIVE
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    BOT_ACTIVE = False
    text = f"🔴 <b>BOT O'CHIRILDI!</b>\n\nEndi barcha foydalanuvchilarga quyidagi xabar ko'rsatiladi:\n\n{MAINTENANCE_MESSAGE}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🟢 Botni yoqish", callback_data="bot_turn_on"))
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="settings_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "bot_turn_on")
def turn_on_bot(call):
    global BOT_ACTIVE
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    BOT_ACTIVE = True
    text = "🟢 <b>BOT YOQILDI!</b>\n\n✅ Endi barcha foydalanuvchilar botdan foydalanishi mumkin."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_message")
def edit_message_prompt(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    text = f"✏️ <b>XABARNI O'ZGARTIRISH</b>\n\nJoriy xabar:\n{MAINTENANCE_MESSAGE}\n\nYangi xabarni yozing:"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="settings_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode='HTML', reply_markup=markup)
    bot.register_next_step_handler(call.message, save_new_message)

def save_new_message(message):
    global MAINTENANCE_MESSAGE
    if message.from_user.id not in ADMIN_IDS:
        return
    MAINTENANCE_MESSAGE = message.text
    bot.reply_to(message, "✅ Yangi xabar saqlandi!",
                 reply_markup=types.InlineKeyboardMarkup().add(
                     types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings_menu")))

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    users_count = db.get_users_count()
    text = f"📊 <b>BOT STATISTIKASI</b>\n\n👥 Foydalanuvchilar: {users_count}\n🤖 Bot holati: {'🟢 FAOL' if BOT_ACTIVE else '🔴 O\'CHIRILGAN'}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="settings_menu"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def back_to_admin(call):
    show_admin_panel(call.message)

# ============================================
# (Qolgan admin funksiyalari – broadcast, add_anime – qisqartirildi, ammo to‘liq botda bo‘lishi kerak)
# ============================================

# ============================================
# FLASK SERVER (HOSTING UCHUN)
# ============================================
try:
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "AnizetNet Bot ishlayapti! 🤖"

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
    print("
