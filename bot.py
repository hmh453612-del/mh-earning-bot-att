import os
import sqlite3
import threading
from datetime import datetime
from flask import Flask
import telebot
from telebot import types

# ==================== BOT CONFIGURATION ====================
BOT_TOKEN = "8389452813:AAHJ5D53i038NEgguYBOriyxuA4noGbHXLM"
BOT_USERNAME = "nh_bd_bot"
# আপনার Render Mini App (ওয়েবসাইট)-এর লিঙ্কটি নিচে দিন:
WEB_APP_URL = "https://your-mini-app.onrender.com"  

REFERRAL_BONUS = 50.00  # প্রতি রেফারে বোনাস (টাকা)
JOIN_BONUS = 0.00       # নতুন ইউজারের জয়েনিং বোনাস

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== SQLITE DATABASE SETUP ====================
DB_FILE = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            balance REAL DEFAULT 0.0,
            total_earned REAL DEFAULT 0.0,
            referrals_count INTEGER DEFAULT 0,
            referred_by INTEGER,
            joined_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_user(user_id, first_name, username, referred_by=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    joined_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, first_name, username, balance, total_earned, referrals_count, referred_by, joined_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?)
    """, (user_id, first_name, username, JOIN_BONUS, JOIN_BONUS, referred_by, joined_date))
    conn.commit()
    conn.close()

def credit_referral(referrer_id, bonus):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET balance = balance + ?, 
            total_earned = total_earned + ?, 
            referrals_count = referrals_count + 1 
        WHERE user_id = ?
    """, (bonus, bonus, referrer_id))
    conn.commit()
    
    # রেফারকারীর বর্তমান তথ্য আনা
    cursor.execute("SELECT referrals_count, balance FROM users WHERE user_id = ?", (referrer_id,))
    res = cursor.fetchone()
    conn.close()
    return res

# ==================== TELEGRAM BOT LOGIC ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    
    # রেফারেল প্যারামিটার চেক করা
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    # চেক করা ইউজার আগে থেকে আছে কি না
    existing_user = get_user(user_id)

    if not existing_user:
        # নতুন ইউজার হলে ডাটাবেজে যুক্ত করা
        if referrer_id and referrer_id != user_id:
            # রেফারকারী আসল কি না যাচাই
            ref_data = get_user(referrer_id)
            if ref_data:
                add_user(user_id, first_name, username, referred_by=referrer_id)
                new_stats = credit_referral(referrer_id, REFERRAL_BONUS)
                
                # 🔥 রেফারকারীর কাছে সুন্দর আকর্ষণীয় নোটিফিকেশন মেসেজ পাঠানো 🔥
                if new_stats:
                    ref_count, ref_bal = new_stats
                    ref_notification = (
                        "🎉 <b>নতুন রেফারেল সফল হয়েছে!</b> 🚀\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        "অভিনন্দন! আপনার রেফারেল লিংক ব্যবহার করে একজন নতুন বন্ধু জয়েন করেছেন।\n\n"
                        f"👤 <b>নতুন মেম্বার:</b> <code>{first_name}</code>\n"
                        f"🆔 <b>আইডি:</b> <code>{user_id}</code>\n"
                        f"🎁 <b>বোনাস যোগ হয়েছে:</b> <code>+ ৳ {REFERRAL_BONUS:.2f}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>আপনার মোট রেফারেল:</b> <b>{ref_count} জন</b>\n"
                        f"💰 <b>বর্তমান মোট ব্যালেন্স:</b> <b>৳ {ref_bal:.2f}</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        "👉 <i>আরও বেশি রেফার করুন এবং আনলিমিটেড ইনকাম করুন!</i>"
                    )
                    try:
                        bot.send_message(referrer_id, ref_notification)
                    except Exception as e:
                        print(f"Failed to notify referrer {referrer_id}: {e}")
            else:
                add_user(user_id, first_name, username)
        else:
            add_user(user_id, first_name, username)
    
    # নতুন বা পুরাতন সকল ইউজারের জন্য ওয়েলকাম মেসেজ
    welcome_text = (
        f"👋 <b>স্বাগতম, {first_name}!</b> 🚀\n\n"
        f"<b>NH EARNING BOT</b>-এ আপনাকে স্বাগতম! এখানে আপনি প্রতিদিন সহজে বিজ্ঞাপন দেখে, "
        f"টাস্ক কমপ্লিট করে এবং বন্ধুদের রেফার করে সরাসরি <b>bKash</b> ও <b>Nagad</b>-এ টাকা আয় করতে পারবেন।\n\n"
        f"🎁 <b>প্রতি রেফারে বোনাস:</b> ৳ {REFERRAL_BONUS:.2f}\n"
        f"📺 <b>প্রতি অ্যাড রিওয়ার্ড:</b> ৳ ১০.০০\n"
        f"⚡ <b>সর্বনিম্ন উইথড্র:</b> ৳ ১০২০.০০\n\n"
        f"👇 <b>আয় শুরু করতে নিচের বাটনে ক্লিক করে মিনি অ্যাপ ওপেন করুন:</b>"
    )

    # ইনলাইন কিবোর্ড বাটন তৈরি
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # ১. Mini App বাটন
    web_app_info = types.WebAppInfo(url=WEB_APP_URL)
    btn_app = types.InlineKeyboardButton("🚀 Open Mini App 🚀", web_app=web_app_info)
    
    # ২. রেফারেল শেয়ার বাটন
    my_refer_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    share_text = f"🚀 NH EARNING BOT-এ প্রতিদিন কাজ করে বিকাশ ও নগদে পেমেন্ট নিন! জয়েন করুন এখনই:\n{my_refer_link}"
    share_url = f"https://t.me/share/url?url={my_refer_link}&text={share_text}"
    btn_share = types.InlineKeyboardButton("👥 বন্ধুদের ইনভাইট করুন", url=share_url)
    
    # ৩. সাপোর্ট বাটন
    btn_support = types.InlineKeyboardButton("💬 Help & Support", url=f"https://t.me/{BOT_USERNAME}")
    
    markup.add(btn_app, btn_share, btn_support)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['mybalance', 'stats'])
def handle_balance(message):
    user = get_user(message.from_user.id)
    if user:
        bal = user[3]
        total = user[4]
        ref_count = user[5]
        msg = (
            "📊 <b>আপনার একাউন্ট তথ্য:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>বর্তমান ব্যালেন্স:</b> ৳ {bal:.2f}\n"
            f"📈 <b>সর্বমোট আয়:</b> ৳ {total:.2f}\n"
            f"👥 <b>মোট রেফারেল:</b> {ref_count} জন\n"
            f"🔗 <b>রেফারেল লিংক:</b>\n<code>https://t.me/{BOT_USERNAME}?start={message.from_user.id}</code>"
        )
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "⚠️ অনুগ্রহ করে প্রথমে /start লিখে বটটি চালু করুন।")

# ==================== 24/7 FLASK SERVER FOR RENDER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return {
        "status": "Online",
        "bot": f"@{BOT_USERNAME}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== MAIN EXECUTION ====================
if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
    
    # Flask ওয়েব সার্ভার আলাদা থ্রেডে চালু করা (Render-এ 24/7 সচল রাখার জন্য)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("Keep-alive Web Server is running...")

    # টেলিগ্রাম বট পোলিং শুরু
    print(f"@{BOT_USERNAME} is now Live & Polling...")
    bot.infinity_polling(skip_pending=True)
