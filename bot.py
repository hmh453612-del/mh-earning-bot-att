from datetime import datetime
import os
import threading
import urllib.parse
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

FIREBASE_DB_URL = (
    "https://mh-earning-bot-default-rtdb.asia-southeast1.firebasedatabase.app"
)

AD_REWARD = 10.00
REFER_REWARD = 50.00

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =================================================================
# 🌐 Render Keep-Alive Server (২৪ ঘণ্টা সচল রাখার জন্য)
# =================================================================
app = Flask(__name__)


@app.route("/")
def home():
    return "MH Earning Bot Premium Engine is Running 24/7!"


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

                    notify_kb = types.InlineKeyboardMarkup(row_width=2)
                    webapp_url = (
                        f"{MINI_APP_URL}#tgWebAppStartParam={referrer_id}"
                    )
                    btn_wallet = types.InlineKeyboardButton(
                        text="💳 ওয়ালেট ব্যালেন্স",
                        web_app=types.WebAppInfo(url=webapp_url),
                    )

                    share_link = (
                        f"https://t.me/{BOT_USERNAME}?start={referrer_id}"
                    )
                    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম করুন!\n👉 জয়েন লিংক: {share_link}"
                    share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_link)}&text={urllib.parse.quote(share_text)}"
                    btn_more_ref = types.InlineKeyboardButton(
                        text="📢 আরও রেফার", url=share_url
                    )

                    notify_kb.add(btn_wallet, btn_more_ref)

                    notify_text = f"""🎉 <b>অভিনন্দন! সফল রেফারেল!</b> 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👤 <b>সদস্য:</b> {full_name}
🆔 <b>আইডি:</b> <code>{user_id_str}</code>
⏰ <b>সময়:</b> {formatted_time}

💎 <b>রেফার বোনাস:</b> <b>+ ৳ {REFER_REWARD:.2f} টাকা</b>
👥 <b>সর্বমোট রেফার:</b> <b>{new_ref_count} জন</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>বোনাসটি মূল একাউন্টে যুক্ত হয়েছে!</i>"""

                    bot.send_message(
                        int(referrer_id),
                        notify_text,
                        reply_markup=notify_kb,
                        disable_web_page_preview=True,
                    )
                except Exception as err:
                    print(f"Referral Notification Error: {err}")
    else:
        update_user_in_db(
            user_id_str,
            {
                "name": full_name,
                "username": f"@{username}" if username else "N/A",
            },
        )


# =================================================================
# ⌨️ প্রিমিয়াম টেলিগ্রাম স্টাইল কাস্টম কিবোর্ড বাটন (Slim & Colorful)
# =================================================================
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=False
    )

    btn_task = types.KeyboardButton("💼 কাজ ⚡")
    btn_balance = types.KeyboardButton("💰 ব্যালেন্স 💎")
    btn_refer = types.KeyboardButton("👥 রেফার 🎁")
    btn_support = types.KeyboardButton("🛠️ সাপোর্ট 💬")

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

    threading.Thread(
        target=handle_referral_and_user_creation,
        args=(user_id, full_name, username, referrer_id),
    ).start()

    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
    btn_webapp = types.InlineKeyboardButton(
        text="🚀 ওপেন আর্নিং অ্যাপ 📱",
        web_app=types.WebAppInfo(url=webapp_url),
    )

    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে প্রতিদিন টাকা ইনকাম করুন!\n\n🚀 প্রতি রেফারে পাবেন ৫০ টাকা!\n\n👉 জয়েন লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"
    btn_share = types.InlineKeyboardButton(
        text="📢 বন্ধুদের শেয়ার করুন 🎁", url=share_url
    )

    inline_kb.add(btn_webapp, btn_share)

    welcome_text = f"""👑 <b>MH EARNING BOT</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>✨ <b>ঘরে বসে সহজ উপায়ে আয় করার মাধ্যম!</b>

✅ <b>ভিডিও বিজ্ঞাপন দেখে ইনকাম</b>
✅ <b>টেলিগ্রাম ও সোশ্যাল টাস্ক</b>
✅ <b>প্রতি রেফারে ইনস্ট্যান্ট ৳ ৫০.০০</b>
✅ <b>বিকাশ ও নগদে সরাসরি উইথড্র</b></blockquote>

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
        "👇 <b>নিচের মেন্যু থেকে অপশন সিলেক্ট করুন:</b>",
        reply_markup=get_main_keyboard(),
    )


# =================================================================
# ২. কাজ বাটন হ্যান্ডলার (Auto-Ad Launch)
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        "💼 কাজ ⚡",
        "💼 কাজ",
        "💼 কাজ করুন",
        "/কাজ",
        "কাজ",
        "/task",
        "task",
    ]
)
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
        text="🎬 ভিডিও অ্যাড দেখুন ⚡",
        web_app=types.WebAppInfo(url=auto_ad_webapp_url),
    )
    btn_social_tasks = types.InlineKeyboardButton(
        text="📋 টাস্ক ড্যাশবোর্ড 🎯",
        web_app=types.WebAppInfo(url=normal_webapp_url),
    )
    task_kb.add(btn_watch_video, btn_social_tasks)

    msg_text = f"""💼 <b>দৈনিক ভিডিও অ্যাড ও ইনকাম টাস্ক</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎬 <b>ভিডিও বিজ্ঞাপন রিওয়ার্ড:</b>
প্রতিটি ভিডিও দেখলে পাবেন <b>৳ {AD_REWARD:.2f}</b> টাকা!

📊 <b>আজকের দেখা অ্যাড:</b> <b>{ads_watched} / 10</b> টি
⚡ <b>নিয়ম:</b> নিচের <b>'ভিডিও অ্যাড দেখুন'</b> বাটনে চাপ দিলেই ফুল-স্ক্রিন ভিডিও ওপেন হবে। দেখা শেষ হলে সরাসরি একাউন্টে টাকা যোগ হবে।</blockquote>

👇 <i>বিজ্ঞাপন দেখতে নিচের বাটনে ট্যাপ করুন:</i>"""

    bot.send_message(
        message.chat.id,
        msg_text,
        reply_markup=task_kb,
        disable_web_page_preview=True,
    )


# =================================================================
# ৩. ব্যালেন্স বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        "💰 ব্যালেন্স 💎",
        "💰 ব্যালেন্স",
        "/ব্যালেন্স",
        "ব্যালেন্স",
        "/balance",
        "balance",
    ]
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
    # স্লিম ও সুন্দর সাইজের বাটন যাতে মেসেজের বাইরে চওড়া না হয়
    btn_open_wallet = types.InlineKeyboardButton(
        text="💳 ওয়ালেট ও উইথড্র 💸",
        web_app=types.WebAppInfo(url=webapp_url),
    )
    bal_kb.add(btn_open_wallet)

    msg_text = f"""👤 <b>লাইভ একাউন্ট ব্যালেন্স ও রিপোর্ট</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🏷️ <b>নাম:</b> {user_name}
🆔 <b>আইডি:</b> <code>{user_id}</code>

💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {balance:.2f}</b> টাকা
👥 <b>মোট সফল রেফার:</b> <b>{referrals}</b> জন
🎬 <b>আজকের দেখা অ্যাড:</b> <b>{ads_watched}</b> টি
✅ <b>টাস্ক সম্পন্ন:</b> <b>{tasks_done}</b> টি</blockquote>

📌 <i>টাকা তুলতে নিচের ওয়ালেট বাটনে চাপুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=bal_kb)


# =================================================================
# ৪. রেফার বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        "👥 রেফার 🎁",
        "👥 রেফার",
        "/রেফার",
        "রেফার",
        "/refer",
        "refer",
    ]
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
        text="📢 রেফার লিংক শেয়ার 🚀", url=share_url
    )
    ref_kb.add(btn_share)

    msg_text = f"""👥 <b>রেফারেল ইনকাম ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎁 <b>প্রতি রেফারে বোনাস:</b> <b>৳ {REFER_REWARD:.2f}</b> টাকা!
📊 <b>মোট রেফারেল:</b> <b>{total_refs}</b> জন
💰 <b>রেফার থেকে আয়:</b> <b>৳ {earned_from_refs:.2f}</b> টাকা</blockquote>

🔗 <b>আপনার পার্সোনাল রেফার লিংক:</b>
<code>{referral_link}</code>

<i>(লিংকটিতে একবার ট্যাপ করলেই কপি হয়ে যাবে)</i>"""

    bot.send_message(
        message.chat.id,
        msg_text,
        reply_markup=ref_kb,
        disable_web_page_preview=True,
    )


# =================================================================
# ৫. সাপোর্ট বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        "🛠️ সাপোর্ট 💬",
        "🛠️ সাপোর্ট",
        "/সাপোর্ট",
        "সাপোর্ট",
        "/support",
        "support",
    ]
)
def support_handler(message):
    sup_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_admin = types.InlineKeyboardButton(
        text="👨‍💻 এডমিন সাপোর্ট 💬",
        url=f"https://t.me/{SUPPORT_USERNAME}",
    )
    sup_kb.add(btn_admin)

    msg_text = f"""🛠️ <b>হেল্প ও সাপোর্ট সেন্টার</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>বট বা পেমেন্ট সংক্রান্ত যেকোনো প্রয়োজনে সরাসরি এডমিনের সাথে যোগাযোগ করুন।

⏰ <b>সাপোর্ট সময়:</b> সকাল ৯:০০ টা - রাত ১১:০০ টা
👤 <b>অফিসিয়াল এডমিন:</b> @{SUPPORT_USERNAME}</blockquote>

👇 <i>এডমিনকে মেসেজ দিতে নিচের বাটনে চাপুন:</i>"""

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
