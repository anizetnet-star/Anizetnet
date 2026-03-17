import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime
import time
import threading

# ============================================
# SOZLAMALAR
# ============================================

TOKEN = os.environ.get('TOKEN', '8742761350:AAH5wjasaAZkYsOxvPyHC1Nh-MLRB0GfXho')
ADMIN_IDS = [int(os.environ.get('ADMIN_ID', '7991544389'))]

bot = telebot.TeleBot(TOKEN)

# ============================================
# BOT HOLATI (O'CHIRISH/YOQISH)
# ============================================

# Bot holati: True - ishlayapti, False - o'chirilgan
BOT_ACTIVE = True

# Ta'mirlash xabari
MAINTENANCE_MESSAGE = """
Hurmatli Anizet.net foydalanuvchilari! 👥

🤖 @Anizet_netbot botimiz 15.03.2026-soat 22:59 gacha ta'mirlash holatida bo'ladi. 🛠

Sizga sog'lik va omad tilaymiz! 🌟 Keyinchalik bot optimallashtiriladi va xizmatlardan xotirjam foydalanishingiz mumkin bo'ladi. 🚀

Tushunganingiz uchun rahmat! ❤️
"""

# ============================================
# MA'LUMOTLAR BAZASI
# ============================================

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('anime.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.init_sample_data()
    
    def create_tables(self):
        # Anime jadvali
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
        
        # Video fayllar jadvali
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_kod TEXT,
                qism_raqami INTEGER,
                file_id TEXT,
                FOREIGN KEY (anime_kod) REFERENCES anime (kod)
            )
        ''')
        
        # Foydalanuvchilar jadvali
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
        """Namuna ma'lumotlar"""
        anime_list = [
            ("10", "Qora klever", 170, "Jangari, Sarguzasht", "O'zbekcha", 2022, "@ongoing_ozbek"),
            ("20", "Jujutsu Kaisen", 24, "Jangari, Fantastika", "O'zbekcha", 2020, "@anime_uzbek"),
            ("30", "Demon Slayer", 26, "Jangari, Drama", "O'zbekcha", 2019, "@anime_tarjima"),
        ]
        
        for a in anime_list:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO anime (kod, nomi, qismlar_soni, janri, tili, yili, kanal)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', a)
            except:
                pass
        
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
    
    def get_all_users(self):
        self.cursor.execute('SELECT user_id FROM users')
        return self.cursor.fetchall()
    
    def get_users_count(self):
        self.cursor.execute('SELECT COUNT(*) FROM users')
        return self.cursor.fetchone()[0]

db = Database()

# ============================================
# MAJBUR OBUNA KANALLARI
# ============================================

REQUIRED_CHANNELS = [
    {"name": "Anisenpay Kanal", "username": "@anisenpay", "link": "https://t.me/anisenpay"},
    {"name": "Anime Yangiliklar", "username": "@anime_yangilik", "link": "https://t.me/anime_yangilik"},
]

# ============================================
# OBUNANI TEKSHIRISH
# ============================================

def check_subscription(user_id):
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except:
            not_subscribed.append(channel)
    return not_subscribed

def show_subscription_menu(message, not_subscribed=None):
    if not_subscribed is None:
        not_subscribed = check_subscription(message.from_user.id)
    
    if not not_subscribed:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🎬 ASOSIY MENYU", callback_data="main_menu")
        markup.add(btn)
        bot.send_message(message.chat.id, "✅ <b>OBUNA MUVAFFAQIYATLI!</b>", parse_mode='HTML', reply_markup=markup)
        return True
    
    text = "🔒 <b>MAJBURIY OBUNA</b>\n\nBotdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for channel in not_subscribed:
        text += f"• {channel['name']}\n"
        markup.add(types.InlineKeyboardButton(f"📢 {channel['name']}", url=channel['link']))
    
    markup.add(types.InlineKeyboardButton("✅ TEKSHIRISH", callback_data="check_subscription"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    return False

# ============================================
# FILTR - BARCHA XABARLARNI TEKSHIRISH
# ============================================

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Barcha xabarlarni ushlab qolish va bot holatini tekshirish"""
    global BOT_ACTIVE
    
    user_id = message.from_user.id
    
    # Admin uchun maxsus buyruqlar
    if user_id in ADMIN_IDS:
        if message.text == "/admin" or message.text == "/panel":
            show_admin_panel(message)
            return
        elif message.text == "/settings" or message.text == "/sozlamalar":
            show_settings_panel(message)
            return
        elif message.text == "/status":
            check_bot_status(message)
            return
    
    # BOT O'CHIRILGAN BO'LSA
    if not BOT_ACTIVE:
        bot.send_message(user_id, MAINTENANCE_MESSAGE)
        return
    
    # BOT ISHLAYOTGAN BO'LSA - normal ishlash
    process_normal_message(message)

def process_normal_message(message):
    """Oddiy xabarlarni qayta ishlash"""
    user_id = message.from_user.id
    db.update_user_activity(user_id)
    
    text = message.text.strip()
    
    # /start komandasi
    if text == "/start":
        normal_start(message)
        return
    
    # Kod orqali qidirish
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
    
    bot.reply_to(message, "❌ Tushunarsiz buyruq. /start bosing")

# ============================================
# START KOMANDASI
# ============================================

def normal_start(message):
    """Oddiy start funksiyasi"""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or "User"
    
    db.add_user(user_id, username, first_name)
    db.update_user_activity(user_id)
    
    args = message.text.split()
    if len(args) > 1:
        kod = args[1]
        anime = db.get_anime(kod)
        if anime:
            not_subscribed = check_subscription(user_id)
            if not_subscribed:
                show_subscription_menu(message, not_subscribed)
            else:
                show_download_button(message, anime)
            return
    
    not_subscribed = check_subscription(user_id)
    if not_subscribed:
        show_subscription_menu(message, not_subscribed)
    else:
        show_main_menu(message)

@bot.message_handler(commands=['start'])
def start_command_handler(message):
    """Start komandasi handler"""
    handle_all_messages(message)

def show_main_menu(message):
    """Asosiy menyu"""
    text = """
🎬 <b>Anisenpay | Uzbek</b>
👥 <b>42,828 oylik foydalanuvchi</b>

<b>ANIMEDAN KADRLAR KO'RISH 🎮</b>

@Ani_Uzbekistan

Anime kodini yuboring (masalan: 10)
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

def show_download_button(message, anime):
    """Yuklab olish tugmasi"""
    text = f"""
🎬 <b>Anisenpay | Uzbek</b>
👥 <b>42,828 oylik foydalanuvchi</b>

<b>ANIMEDAN KADRLAR KO'RISH 🎮</b>

@Ani_Uzbekistan

<b>{anime[1]}</b>
📺 {anime[2]} qism
    """
    
    markup = types.InlineKeyboardMarkup()
    download_btn = types.InlineKeyboardButton("📥 YUKLAB OLISH", callback_data=f"episodes_{anime[0]}")
    markup.add(download_btn)
    
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
    qismlar = min(anime[2], 25)
    buttons = []
    
    for i in range(1, qismlar + 1):
        buttons.append(types.InlineKeyboardButton(str(i), callback_data=f"video_{kod}_{i}"))
    
    for i in range(0, len(buttons), 5):
        markup.add(*buttons[i:i+5])
    
    markup.add(types.InlineKeyboardButton("🔙 ORQAGA", callback_data=f"back_{kod}"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                          parse_mode='HTML', reply_markup=markup)

# ============================================
# VIDEO YUBORISH
# ============================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("video_"))
def send_video(call):
    parts = call.data.split("_")
    kod = parts[1]
    qism = parts[2]
    
    anime = db.get_anime(kod)
    file_id = db.get_video(kod, qism)
    
    text = f"""
🎬 <b>{anime[1]} - {qism}-QISM</b>
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if int(qism) > 1:
        prev_btn = types.InlineKeyboardButton("⬅️", callback_data=f"video_{kod}_{int(qism)-1}")
    else:
        prev_btn = types.InlineKeyboardButton("⬅️", callback_data="none")
    
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
        # Agar video bo'lmasa
        demo_text = f"{text}\n\n❌ Video hali qo'shilmagan."
        bot.send_message(call.message.chat.id, demo_text, parse_mode='HTML', reply_markup=markup)
    
    bot.answer_callback_query(call.id, f"{qism}-qism")

# ============================================
# ORQAGA QAYTISH
# ============================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
def back_to_download(call):
    kod = call.data.replace("back_", "")
    anime = db.get_anime(kod)
    show_download_button(call.message, anime)

# ============================================
# OBUNA TEKSHIRISH
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
        text = "⚠️ <b>QUYIDAGI KANALLARGA OBUNA BO'LMAGANSIZ:</b>\n\n"
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
    """Admin panelini ko'rsatish"""
    text = """
👑 <b>BOSHQARUV PANELI</b>

Boshqaruv panelidasiz

Quyidagilardan birini tanlang:
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton("⚙️ Tizim sozlamalari", callback_data="settings_menu")
    btn2 = types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
    btn3 = types.InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="user_list")
    btn4 = types.InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast_menu")
    btn5 = types.InlineKeyboardButton("🎬 Anime qo'shish", callback_data="add_anime_menu")
    btn6 = types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

# ============================================
# TIZIM SOZLAMALARI (O'CHIRISH/YOQISH)
# ============================================

def show_settings_panel(message):
    """Sozlamalar panelini ko'rsatish"""
    global BOT_ACTIVE
    
    status_text = "🟢 FAOL" if BOT_ACTIVE else "🔴 O'CHIRILGAN"
    
    text = f"""
⚙️ <b>TIZIM SOZLAMALARI</b>

🤖 Bot holati: {status_text}

Quyidagilardan birini tanlang:
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if BOT_ACTIVE:
        btn1 = types.InlineKeyboardButton("🔴 Botni o'chirish", callback_data="bot_turn_off")
    else:
        btn1 = types.InlineKeyboardButton("🟢 Botni yoqish", callback_data="bot_turn_on")
    
    btn2 = types.InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast_menu")
    btn3 = types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
    btn4 = types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_admin")
    
    markup.add(btn1, btn2, btn3, btn4)
    
    # Agar bot o'chirilgan bo'lsa, xabarni ko'rsatish tugmasi
    if not BOT_ACTIVE:
        markup.add(types.InlineKeyboardButton("✏️ Xabarni o'zgartirish", callback_data="edit_message"))
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "bot_turn_off")
def turn_off_bot(call):
    """Botni o'chirish"""
    global BOT_ACTIVE
    
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    
    BOT_ACTIVE = False
    
    text = f"""
🔴 <b>BOT O'CHIRILDI!</b>

Endi barcha foydalanuvchilarga quyidagi xabar ko'rsatiladi:

{MAINTENANCE_MESSAGE}

✅ Botni qayta yoqish uchun "🟢 Botni yoqish" tugmasini bosing.
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟢 Botni yoqish", callback_data="bot_turn_on"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="settings_menu")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "bot_turn_on")
def turn_on_bot(call):
    """Botni yoqish"""
    global BOT_ACTIVE
    
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    
    BOT_ACTIVE = True
    
    text = """
🟢 <b>BOT YOQILDI!</b>

✅ Endi barcha foydalanuvchilar botdan foydalanishi mumkin.
📊 Normal rejim ishga tushdi.
    """
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings_menu")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_message")
def edit_message_prompt(call):
    """Xabarni o'zgartirish"""
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz admin emassiz!")
        return
    
    text = f"""
✏️ <b>XABARNI O'ZGARTIRISH</b>

Joriy xabar:
{MAINTENANCE_MESSAGE}

Yangi xabarni yozing:
    """
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="settings_menu"))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )
    
    # Keyingi qadam
    bot.register_next_step_handler(call.message, save_new_message)

def save_new_message(message):
    """Yangi xabarni saqlash"""
    global MAINTENANCE_MESSAGE
    
    if message.from_user.id not in ADMIN_IDS:
        return
    
    MAINTENANCE_MESSAGE = message.text
    
    bot.reply_to(
        message,
        "✅ Yangi xabar saqlandi!",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings_menu")
        )
    )

# ============================================
# STATISTIKA
# ============================================

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    """Statistika"""
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "Siz
