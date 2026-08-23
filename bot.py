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
# 🔥 Firebase Helper Functions (ডাটাবেস ইঞ্জিন)
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


def get_all_tasks_from_db():
    """ফায়ারবেজ থেকে এডমিনের সেট করা সকল টাস্ক আনা"""
    try:
        url = f"{FIREBASE_DB_URL}/tasks.json"
        res = requests.get(url, timeout=4)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Tasks Fetch Error: {e}")
    return {}


def handle_referral_and_user_creation(
    user_id, full_name, username, referrer_id
):
    """নতুন ইউজার তৈরি ও ইনস্ট্যান্ট রেফার নোটিফিকেশন"""
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

⚡ <i>বোনাসটি সরাসরি আপনার মূল একাউন্টে যুক্ত হয়েছে!</i>"""

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
# ⌨️ কাস্টম কিবোর্ড লেআউটসমূহ (Main & Sub Keyboards)
# =================================================================
def get_main_keyboard():
    """মূল কিবোর্ড মেন্যু"""
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


def get_work_keyboard():
    """কাজের সাব-কিবোর্ড মেন্যু"""
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=False
    )
    btn_video = types.KeyboardButton("🎬 ভিডিও অ্যাড দেখুন ⚡")
    btn_tasks = types.KeyboardButton("📋 টাস্ক ড্যাশবোর্ড 🎯")
    btn_back = types.KeyboardButton("🔙 মূল মেন্যু")

    keyboard.row(btn_video, btn_tasks)
    keyboard.row(btn_back)
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
<blockquote>✨ <b>ঘরে বসে সহজ উপায়ে আয় করার প্রিমিয়াম প্ল্যাটফর্ম!</b>

✅ <b>ভিডিও বিজ্ঞাপন দেখে ইনকাম</b>
✅ <b>টেলিগ্রাম ও সোশ্যাল টাস্ক কমপ্লিট</b>
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
        "👇 <b>নিচের মেন্যু থেকে আপনার কাঙ্ক্ষিত অপশন বেছে নিন:</b>",
        reply_markup=get_main_keyboard(),
    )


# =================================================================
# ২. কাজ বাটন হ্যান্ডলার (ক্লিক করলে নতুন ২টি বাটন ওপেন হবে)
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in ["💼 কাজ ⚡", "💼 কাজ", "কাজ", "/কাজ", "/task", "task"]
)
def work_options_handler(message):
    reply_text = """💼 <b>কাজের ক্যাটাগরি সিলেক্ট করুন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ আপনি দুইভাবে কাজ করে প্রতিদিন আনলিমিটেড ইনকাম করতে পারবেন:

1️⃣ <b>ভিডিও অ্যাড দেখুন:</b> ছোট ছোট বিজ্ঞাপন দেখে প্রতিটিতে রিওয়ার্ড পান।
2️⃣ <b>টাস্ক ড্যাশবোর্ড:</b> সোশ্যাল চ্যানেল জয়েন এবং টাস্ক পূরণ করে বড় অংকের বোনাস পান।</blockquote>

👇 <i>নিচের কিবোর্ড থেকে অপশন সিলেক্ট করুন:</i>"""

    bot.send_message(
        message.chat.id,
        reply_text,
        reply_markup=get_work_keyboard(),
    )


# =================================================================
# ৩. ভিডিও অ্যাড দেখুন হ্যান্ডলার (প্রিমিয়াম টেক্সট + ওপেন বাটন)
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        "🎬 ভিডিও অ্যাড দেখুন ⚡",
        "ভিডিও অ্যাড দেখুন",
        "ভিডিও এড দেখুন",
        "/ভিডিও এড দেখুন",
        "/ভিডিও অ্যাড দেখুন",
    ]
)
def video_ad_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    ads_watched = int(user_data.get("adsWatched", 0))

    # সরাসরি অ্যাড অটো-রান করার জন্য মিনি অ্যাপের স্পেশাল লিংক
    auto_ad_webapp_url = (
        f"{MINI_APP_URL}#action=watch_ad&tgWebAppStartParam={user_id}"
    )

    ad_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_open_ad = types.InlineKeyboardButton(
        text="🚀 ওপেন (ভিডিও অ্যাড দেখুন) ⚡",
        web_app=types.WebAppInfo(url=auto_ad_webapp_url),
    )
    ad_kb.add(btn_open_ad)

    msg_text = f"""🎬 <b>প্রিমিয়াম ভিডিও অ্যাড জোন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>💎 <b>বিজ্ঞাপন রিওয়ার্ড:</b> <b>৳ {AD_REWARD:.2f} টাকা</b> প্রতি ভিউ!
📊 <b>আজকের সম্পন্ন অ্যাড:</b> <b>{ads_watched} / 10</b> টি

⚡ <b>নিয়মাবলী:</b>
• নিচের <b>'ওপেন (ভিডিও অ্যাড দেখুন)'</b> বাটনে ট্যাপ করুন।
• মিনি অ্যাপে ফুল-স্ক্রিন ভিডিও প্লে হবে।
• সম্পূর্ণ বিজ্ঞাপন দেখার পর সরাসরি আপনার মেইন ওয়ালেটে টাকা যুক্ত হবে।</blockquote>

👇 <i>ভিডিও শুরু করতে নিচের বাটনে চাপ দিন:</i>"""

    bot.send_message(
        message.chat.id,
        msg_text,
        reply_markup=ad_kb,
        disable_web_page_preview=True,
    )


# =================================================================
# ৪. টাস্ক ড্যাশবোর্ড ও লাইভ ভেরিফিকেশন সিস্টেম
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in [
        "📋 টাস্ক ড্যাশবোর্ড 🎯",
        "টাস্ক ড্যাশবোর্ড",
        "/টাস্ক ড্যাশবোর্ড",
        "/tasks",
        "টাস্ক",
    ]
)
def task_dashboard_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    completed_tasks = user_data.get("completedTasks", {})

    all_tasks = get_all_tasks_from_db()

    if not all_tasks:
        # যদি কোন টাস্ক না থাকে, নরমাল মিনি অ্যাপ ড্যাশবোর্ড ওপেন করবে
        normal_webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
        no_task_kb = types.InlineKeyboardMarkup()
        no_task_kb.add(
            types.InlineKeyboardButton(
                "📱 অ্যাপে টাস্ক দেখুন",
                web_app=types.WebAppInfo(url=normal_webapp_url),
            )
        )

        bot.send_message(
            message.chat.id,
            """📋 <b>সোশ্যাল টাস্ক ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>বর্তমানে সরাসরি বটে কোনো নতুন টাস্ক নেই অথবা সব টাস্ক সম্পন্ন হয়েছে। অ্যাপ থেকে নতুন টাস্ক চেক করুন!</blockquote>""",
            reply_markup=no_task_kb,
        )
        return

    # টাস্কগুলোর তালিকা তৈরি
    msg_text = """📋 <b>সোশ্যাল আর্নিং টাস্ক ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ <b>কাজের নিয়ম:</b>
১. নিচের টাস্ক লিংকগুলোতে ক্লিক করে চ্যানেল/গ্রুপে জয়েন করুন।
২. জয়েন শেষ হলে নিচের <b>'✅ ভেরিফাই'</b> বাটনে ক্লিক করুন।
৩. সাথে সাথে টাকা আপনার একাউন্টে যুক্ত হবে!</blockquote>\n"""

    task_kb = types.InlineKeyboardMarkup(row_width=1)

    pending_tasks_count = 0
    for task_id, task in all_tasks.items():
        if isinstance(task, dict):
            # যদি ইতিমধ্যে কমপ্লিট হয়ে থাকে তাহলে স্কিপ করবে
            if task_id in completed_tasks:
                continue

            pending_tasks_count += 1
            title = task.get("title", f"টাস্ক #{task_id}")
            reward = float(task.get("reward", 5.00))
            link = task.get("url", task.get("link", "https://t.me"))

            btn_link = types.InlineKeyboardButton(
                text=f"👉 {title} (৳ {reward:.2f})", url=link
            )
            btn_verify = types.InlineKeyboardButton(
                text=f"✅ ভেরিফাই করুন ({title})",
                callback_data=f"verify_{task_id}",
            )

            task_kb.add(btn_link, btn_verify)

    if pending_tasks_count == 0:
        bot.send_message(
            message.chat.id,
            "🎉 <b>অভিনন্দন! আপনি আজকের সব টাস্ক সম্পন্ন করে ফেলেছেন!</b>\nনতুন টাস্ক আসলে এখানে দেখতে পাবেন।",
            reply_markup=get_main_keyboard(),
        )
    else:
        bot.send_message(
            message.chat.id,
            msg_text,
            reply_markup=task_kb,
            disable_web_page_preview=True,
        )


# =================================================================
# ৫. টাস্ক ইনস্ট্যান্ট ভেরিফাই Callback Query
# =================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_task_callback(call):
    user_id = str(call.from_user.id)
    task_id = call.data.replace("verify_", "")

    user_data = get_user_from_db(user_id) or {}
    completed_tasks = user_data.get("completedTasks", {})

    if task_id in completed_tasks:
        bot.answer_callback_query(
            call.id,
            "⚠️ আপনি এই টাস্কটি আগেই সম্পন্ন করেছেন!",
            show_alert=True,
        )
        return

    # ফায়ারবেজ থেকে টাস্কের তথ্য আনা
    tasks = get_all_tasks_from_db()
    task = tasks.get(task_id)

    if not task:
        bot.answer_callback_query(
            call.id, "❌ টাস্কটি আর সক্রিয় নেই!", show_alert=True
        )
        return

    task_reward = float(task.get("reward", 5.00))
    task_title = task.get("title", "টাস্ক")

    # ইউজারের ব্যালেন্স এবং সম্পন্ন টাস্ক আপডেট
    cur_bal = float(user_data.get("balance", 0.0))
    cur_tasks_count = int(user_data.get("completedTasksCount", 0))

    new_balance = cur_bal + task_reward
    new_tasks_count = cur_tasks_count + 1

    # Firebase এ ডাটা সেভ
    update_user_in_db(
        user_id,
        {
            "balance": new_balance,
            "completedTasksCount": new_tasks_count,
            f"completedTasks/{task_id}": True,
        },
    )

    bot.answer_callback_query(
        call.id,
        f"🎉 অভিনন্দন! টাস্ক সফলভাবে ভেরিফাই হয়েছে। +৳ {task_reward:.2f} যোগ হয়েছে!",
        show_alert=True,
    )

    success_text = f"""✅ <b>টাস্ক সম্পন্ন ও রিওয়ার্ড যুক্ত!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎯 <b>টাস্ক:</b> {task_title}
💰 <b>যোগ হয়েছে:</b> <b>+ ৳ {task_reward:.2f} টাকা</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>ব্যালেন্স আপনার ওয়ালেটে ইনস্ট্যান্ট আপডেট হয়েছে!</i>"""

    bot.send_message(call.message.chat.id, success_text)


# =================================================================
# ৬. মূল মেন্যুতে ফিরে আসার বাটন
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["🔙 মূল মেন্যু", "মূল মেন্যু"])
def back_to_main_menu(message):
    bot.send_message(
        message.chat.id,
        "🏠 <b>মূল মেন্যুতে ফিরে আসা হয়েছে:</b>",
        reply_markup=get_main_keyboard(),
    )


# =================================================================
# ৭. ব্যালেন্স বাটন হ্যান্ডলার
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
# ৮. রেফার বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(
    func=lambda msg: msg.text
    in ["👥 রেফার 🎁", "👥 রেফার", "/রেফার", "রেফার", "/refer", "refer"]
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
━━━━━━━━
