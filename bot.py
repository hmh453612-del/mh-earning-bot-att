import os
import threading
import urllib.parse
from datetime import datetime
from flask import Flask
import requests
import telebot
from telebot import types

# =================================================================
# ⚙️ কনফিগারেশন সেটিংস (Configuration)
# =================================================================
BOT_TOKEN = "8862120350:AAGAbapwq17iwwGGuTbTjW8COWskalp2EKE"
BOT_USERNAME = "mhearningxl_bot"
MINI_APP_URL = "https://mhearningbot.blogspot.com/?m=1"
SUPPORT_USERNAME = "mh_earning_bot_admin"

FIREBASE_DB_URL = "https://mh-earning-bot-default-rtdb.asia-southeast1.firebasedatabase.app"

AD_REWARD = 10.00
REFER_REWARD = 50.00

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =================================================================
# 🌐 Render Keep-Alive Server (২৪ ঘণ্টা সচল রাখার জন্য)
# =================================================================
app = Flask(__name__)


@app.route("/")
def home():
    return "MH Earning Bot Instant Referral Engine is Running 24/7!"


def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# =================================================================
# 🔥 Firebase Helper Functions (ডাটাবেস সিঙ্ক ইঞ্জিন)
# =================================================================
def get_user_from_db(user_id):
    try:
        url = f"{FIREBASE_DB_URL}/users/{user_id}.json"
        res = requests.get(url, timeout=4)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Read Error: {e}")
    return None


def update_user_in_db(user_id, data):
    try:
        url = f"{FIREBASE_DB_URL}/users/{user_id}.json"
        requests.patch(url, json=data, timeout=4)
    except Exception as e:
        print(f"Firebase Update Error: {e}")


def handle_referral_and_user_creation(
    user_id, full_name, username, referrer_id
):
    """নতুন ইউজার তৈরি ও সাথে সাথে রেফারকারীকে ইনস্ট্যান্ট নোটিফিকেশন পাঠানো"""
    user_id_str = str(user_id)
    user_data = get_user_from_db(user_id_str)
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    formatted_time = now.strftime("%I:%M %p | %d/%m/%Y")

    # যদি ইউজার পূর্বে জয়েন না করে থাকে (একদম নতুন)
    if not user_data:
        new_user = {
            "telegramId": user_id_str,
            "name": full_name,
            "username": f"@{username}" if username else "N/A",
            "balance": 0.00,
            "referrals": 0,
            "adsWatched": 0,
            "lastAdDate": today_date,
            "completedTasksCount": 0,
            "rejectedCount": 0,
            "joinedAt": int(now.timestamp() * 1000),
            "referredBy": (
                referrer_id
                if (referrer_id and referrer_id != user_id_str)
                else None
            ),
        }
        update_user_in_db(user_id_str, new_user)

        # রেফারকারী থাকলে তাকে তাৎক্ষণিক টাকা যোগ করা ও মেসেজ দেওয়া
        if (
            referrer_id
            and referrer_id != user_id_str
            and referrer_id != "guest_12345678"
        ):
            referrer_data = get_user_from_db(referrer_id)
            if referrer_data:
                cur_bal = float(referrer_data.get("balance", 0.0))
                cur_ref = int(referrer_data.get("referrals", 0))

                new_balance = cur_bal + REFER_REWARD
                new_ref_count = cur_ref + 1

                # ফায়ারবেস আপডেট
                update_user_in_db(
                    referrer_id,
                    {"balance": new_balance, "referrals": new_ref_count},
                )

                ref_item = {
                    "id": user_id_str,
                    "name": full_name,
                    "joinedAt": int(now.timestamp() * 1000),
                }

                try:
                    ref_list_url = f"{FIREBASE_DB_URL}/users/{referrer_id}/myReferrals/{user_id_str}.json"
                    requests.put(ref_list_url, json=ref_item, timeout=4)

                    # 🌟 রেফারকারীর জন্য আকর্ষণীয় বাটন
                    notify_kb = types.InlineKeyboardMarkup(row_width=2)
                    webapp_url = (
                        f"{MINI_APP_URL}#tgWebAppStartParam={referrer_id}"
                    )
                    btn_wallet = types.InlineKeyboardButton(
                        text="💳 ওয়ালেট ও ব্যালেন্স দেখুন",
                        web_app=types.WebAppInfo(url=webapp_url),
                    )

                    share_link = f"https://t.me/{BOT_USERNAME}?start={referrer_id}"
                    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম করুন!\n👉 জয়েন লিংক: {share_link}"
                    share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_link)}&text={urllib.parse.quote(share_text)}"
                    btn_more_ref = types.InlineKeyboardButton(
                        text="📢 আরও রেফার করুন", url=share_url
                    )

                    notify_kb.add(btn_wallet, btn_more_ref)

                    # 🌟 প্রফেশনাল ও আকর্ষণীয় রেফারেল মেসেজ
                    notify_text = f"""🎊 <b>অভিনন্দন! আপনি সফলভাবে রেফার করেছেন!</b> 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👤 <b>নতুন সদস্য:</b> {full_name}
🆔 <b>ইউজার আইডি:</b> <code>{user_id_str}</code>
📅 <b>রেফারের সময়:</b> {formatted_time}

💰 <b>অর্জিত রেফারেল বোনাস:</b> <b>+ ৳ {REFER_REWARD:.2f} টাকা</b>
👥 <b>আপনার সর্বমোট রেফার:</b> <b>{new_ref_count} জন</b>
💵 <b>বর্তমান মোট ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>আপনার রেফারেল বোনাসের টাকা মূল ব্যালেন্সে স্বয়ংক্রিয়ভাবে যোগ করা হয়েছে। বন্ধুদের সাথে লিংক শেয়ার করে আরও বেশি আয় করুন!</i>"""

                    # সাথে সাথে টেলিগ্রামে মেসেজ পাঠানো
                    bot.send_message(
                        int(referrer_id),
                        notify_text,
                        reply_markup=notify_kb,
                        disable_web_page_preview=True,
                    )
                except Exception as err:
                    print(f"Referral Notification Error: {err}")
    else:
        # পুরনো ইউজার হলে নাম ডাটাবেসে আপডেট করা
        update_user_in_db(
            user_id_str,
            {
                "name": full_name,
                "username": f"@{username}" if username else "N/A",
            },
        )


# =================================================================
# ⌨️ কাস্টম কিবোর্ড বাটন (Custom Reply Keyboard)
# =================================================================
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # সারি ১: [ কাজ | ব্যালেন্স ]
    btn_task = types.KeyboardButton("💼 কাজ")
    btn_balance = types.KeyboardButton("💰 ব্যালেন্স")

    # সারি ২: [ রেফার | সাপোর্ট ]
    btn_refer = types.KeyboardButton("👥 রেফার")
    btn_support = types.KeyboardButton("🛠️ সাপোর্ট")

    keyboard.row(btn_task, btn_balance)
    keyboard.row(btn_refer, btn_support)
    return keyboard


# =================================================================
# ১. /start কমান্ড হ্যান্ডলার
# =================================================================
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = str(message.from_user.id)
    full_name = message.from_user.first_name or "User"
    if message.from_user.last_name:
        full_name += f" {message.from_user.last_name}"
    username = message.from_user.username or ""

    referrer_id = None
    args = message.text.split()
    if len(args) > 1:
        referrer_id = args[1].strip()

    # ব্যাকগ্রাউন্ডে রেফার প্রসেস ও সাথে সাথে নোটিফিকেশন পাঠানো
    threading.Thread(
        target=handle_referral_and_user_creation,
        args=(user_id, full_name, username, referrer_id),
    ).start()

    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
    btn_webapp = types.InlineKeyboardButton(
        text="Open MH Earning Bot 📱", web_app=types.WebAppInfo(url=webapp_url)
    )

    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে প্রতিদিন টাকা ইনকাম করুন!\n\n🚀 প্রতি রেফারে পাবেন ৫০ টাকা!\n\n👉 জয়েন লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"
    btn_share = types.InlineKeyboardButton(
        text="রেফার শেয়ার করুন 📢", url=share_url
    )

    inline_kb.add(btn_webapp, btn_share)

    welcome_text = f"""🔥 <b>MH EARNING BOT</b> 🔥
📋 <b>এখন ঘরে বসেই ইনকাম করুন সহজে!</b>

<blockquote>✅ YouTube Subscribe Task
✅ Telegram Join Task
✅ Referral Income System
✅ Daily Bonus
✅ Instant Withdraw

🏆 Trusted & Professional Telegram Earning Platform
🎯 <b>আজই জয়েন করুন এবং ইনকাম শুরু করুন!</b> 🚀</blockquote>

🔗 <b>আপনার রেফারেল লিংক:</b>
<code>{referral_link}</code>"""

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=inline_kb,
        disable_web_page_preview=True,
    )
    bot.send_message(
        message.chat.id,
        "👇 <b>নিচের বাটনগুলো ব্যবহার করে কাজ ও ব্যালেন্স চেক করুন:</b>",
        reply_markup=get_main_keyboard(),
    )


# =================================================================
# ২. /কাজ এবং '💼 কাজ' বাটন হ্যান্ডলার (Auto-Ad Launch)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["💼 কাজ", "/কাজ", "কাজ"])
def task_handler(message):
    user_id = str(message.from_user.id)

    auto_ad_webapp_url = (
        f"{MINI_APP_URL}#action=watch_ad&tgWebAppStartParam={user_id}"
    )
    normal_webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"

    user_data = get_user_from_db(user_id) or {}
    ads_watched = int(user_data.get("adsWatched", 0))

    task_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_watch_video = types.InlineKeyboardButton(
        text="🎬 সরাসরি ভিডিও অ্যাড দেখুন (৳ ১০.০০)",
        web_app=types.WebAppInfo(url=auto_ad_webapp_url),
    )
    btn_social_tasks = types.InlineKeyboardButton(
        text="📋 অন্যান্য সোশ্যাল টাস্ক ড্যাশবোর্ড",
        web_app=types.WebAppInfo(url=normal_webapp_url),
    )
    task_kb.add(btn_watch_video, btn_social_tasks)

    msg_text = f"""💼 <b>দৈনিক ভিডিও অ্যাড ও ইনকাম টাস্ক</b>
━━━━━━━━━━━━━━━━━━━━
<blockquote>🎬 <b>ভিডিও বিজ্ঞাপন রিওয়ার্ড:</b>
প্রতিটি ভিডিও সম্পূর্ণ দেখলে পাবেন <b>৳ {AD_REWARD:.2f}</b> টাকা!

📊 <b>আজ সম্পন্ন করেছেন:</b> <b>{ads_watched} / 10</b> টি অ্যাড
⚡ <b>নিয়ম:</b> নিচের <b>"সরাসরি ভিডিও অ্যাড দেখুন"</b> বাটনে চাপ দিলেই সাথে সাথে ফুল-স্ক্রিন ভিডিও চালু হবে। দেখা শেষ হলে স্বয়ংক্রিয়ভাবে ব্যালেন্সে টাকা যোগ হবে।</blockquote>

👇 <i>বিজ্ঞাপন দেখতে নিচের বাটনে ট্যাপ করুন:</i>"""

    bot.send_message(
        message.chat.id,
        msg_text,
        reply_markup=task_kb,
        disable_web_page_preview=True,
    )


# =================================================================
# ৩. /ব্যালেন্স এবং '💰 ব্যালেন্স' বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text in ["💰 ব্যালেন্স", "/ব্যালেন্স", "ব্যালেন্স"]
)
def balance_handler(message):
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name or "User"
    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"

    user_data = get_user_from_db(user_id) or {}
    balance = float(user_data.get("balance", 0.00))
    ads_watched = int(user_data.get("adsWatched", 0))
    referrals = int(user_data.get("referrals", 0))
    tasks_done = int(user_data.get("completedTasksCount", 0))

    bal_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_open_wallet = types.InlineKeyboardButton(
        text="💳 ওয়ালেট ওপেন ও টাকা তুলুন (bKash/Nagad)",
        web_app=types.WebAppInfo(url=webapp_url),
    )
    bal_kb.add(btn_open_wallet)

    msg_text = f"""👤 <b>লাইভ অ্যাকাউন্ট ব্যালেন্স ও রিপোর্ট</b>
━━━━━━━━━━━━━━━━━━━━
<blockquote>🏷️ <b>নাম:</b> {user_name}
🆔 <b>আইডি:</b> <code>{user_id}</code>

💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {balance:.2f}</b> টাকা
👥 <b>মোট সফল রেফার:</b> <b>{referrals}</b> জন
🎬 <b>আজকের দেখা অ্যাড:</b> <b>{ads_watched}</b> টি
✅ <b>টাস্ক সম্পন্ন:</b> <b>{tasks_done}</b> টি</blockquote>

📌 <i>ব্যালেন্স উইথড্র করতে নিচের বাটনে চাপুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=bal_kb)


# =================================================================
# ৪. /রেফার এবং '👥 রেফার' বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text in ["👥 রেফার", "/রেফার", "রেফার"]
)
def refer_handler(message):
    user_id = str(message.from_user.id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    user_data = get_user_from_db(user_id) or {}
    total_refs = int(user_data.get("referrals", 0))
    earned_from_refs = total_refs * REFER_REWARD

    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম শুরু করুন!\n\n👉 রেফারেল লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"

    ref_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_share = types.InlineKeyboardButton(
        text="📢 বন্ধুদের সাথে শেয়ার করুন", url=share_url
    )
    ref_kb.add(btn_share)

    msg_text = f"""👥 <b>রেফারেল ইনকাম ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━
<blockquote>🎁 <b>প্রতি রেফারে বোনাস:</b> <b>৳ {REFER_REWARD:.2f}</b> টাকা!
📊 <b>মোট রেফারেল:</b> <b>{total_refs}</b> জন
💰 <b>রেফার থেকে আয়:</b> <b>৳ {earned_from_refs:.2f}</b> টাকা</blockquote>

🔗 <b>আপনার পার্সোনাল রেফার লিংক:</b>
<code>{referral_link}</code>

<i>(লিংকটিতে একবার চাপ দিলেই কপি হয়ে যাবে)</i>"""

    bot.send_message(
        message.chat.id,
        msg_text,
        reply_markup=ref_kb,
        disable_web_page_preview=True,
    )


# =================================================================
# ৫. /সাপোর্ট এবং '🛠️ সাপোর্ট' বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text in ["🛠️ সাপোর্ট", "/সাপোর্ট", "সাপোর্ট"]
)
def support_handler(message):
    sup_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_admin = types.InlineKeyboardButton(
        text="👨‍💻 এডমিনের সাথে যোগাযোগ করুন",
        url=f"https://t.me/{SUPPORT_USERNAME}",
    )
    sup_kb.add(btn_admin)

    msg_text = f"""🛠️ <b>হেল্প ও সাপোর্ট সেন্টার</b>
━━━━━━━━━━━━━━━━━━━━
<blockquote>বট বা পেমেন্ট সংক্রান্ত যেকোনো প্রয়োজনে সরাসরি এডমিনের সাথে কথা বলুন।

⏰ <b>সাপোর্ট সময়:</b> প্রতিদিন সকাল ৯:০০ টা - রাত ১১:০০ টা
👤 <b>অফিসিয়াল এডমিন:</b> @{SUPPORT_USERNAME}</blockquote>

👇 <i>এডমিনের ইনবক্সে যেতে নিচের বাটনে চাপুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=sup_kb)


# =================================================================
# 🚀 মেইন রানার
# =================================================================
if __name__ == "__main__":
    print("🌐 Keep-Alive Server চালু হচ্ছে...")
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("✅ MH Earning Bot সফলভাবে চালু হয়েছে...")
    bot.infinity_polling()
