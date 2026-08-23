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

# থ্রেড সেফটি এবং অটো HTML পার্স মোড
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

# =================================================================
# 🌐 Render Keep-Alive Web Server (২৪ ঘণ্টা এক্টিভ রাখার জন্য)
# =================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "MH Earning Bot Ultra Engine is Running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# =================================================================
# 🔥 Firebase Database Helper Engine
# =================================================================
def get_user_from_db(user_id):
    try:
        url = f"{FIREBASE_DB_URL}/users/{user_id}.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Read Error: {e}")
    return None

def update_user_in_db(user_id, data):
    try:
        url = f"{FIREBASE_DB_URL}/users/{user_id}.json"
        requests.patch(url, json=data, timeout=5)
    except Exception as e:
        print(f"Firebase Update Error: {e}")

def get_all_tasks_from_db():
    try:
        url = f"{FIREBASE_DB_URL}/tasks.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Tasks Fetch Error: {e}")
    return {}

def handle_referral_and_user_creation(user_id, full_name, username, referrer_id):
    """ইউজার তৈরি ও রেফারেল অটোমেটেড সিস্টেম"""
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
            "referredBy": referrer_id if (referrer_id and referrer_id != user_id_str) else None
        }
        update_user_in_db(user_id_str, new_user)

        if referrer_id and referrer_id != user_id_str and referrer_id != "guest_12345678":
            referrer_data = get_user_from_db(referrer_id)
            if referrer_data:
                cur_bal = float(referrer_data.get("balance", 0.0))
                cur_ref = int(referrer_data.get("referrals", 0))

                new_balance = cur_bal + REFER_REWARD
                new_ref_count = cur_ref + 1

                update_user_in_db(referrer_id, {
                    "balance": new_balance,
                    "referrals": new_ref_count
                })

                ref_item = {
                    "id": user_id_str,
                    "name": full_name,
                    "joinedAt": int(now.timestamp() * 1000)
                }

                try:
                    ref_list_url = f"{FIREBASE_DB_URL}/users/{referrer_id}/myReferrals/{user_id_str}.json"
                    requests.put(ref_list_url, json=ref_item, timeout=4)

                    notify_kb = types.InlineKeyboardMarkup(row_width=2)
                    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={referrer_id}"
                    btn_wallet = types.InlineKeyboardButton(text="💳 ওয়ালেট ব্যালেন্স", web_app=types.WebAppInfo(url=webapp_url))
                    
                    share_link = f"https://t.me/{BOT_USERNAME}?start={referrer_id}"
                    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম করুন!\n👉 জয়েন লিংক: {share_link}"
                    share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_link)}&text={urllib.parse.quote(share_text)}"
                    btn_more_ref = types.InlineKeyboardButton(text="📢 আরও রেফার", url=share_url)

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

                    bot.send_message(int(referrer_id), notify_text, reply_markup=notify_kb, disable_web_page_preview=True)
                except Exception as err:
                    print(f"Referral Notification Error: {err}")
    else:
        update_user_in_db(user_id_str, {
            "name": full_name,
            "username": f"@{username}" if username else "N/A"
        })

# =================================================================
# ⌨️ কিবোর্ড লেআউটসমূহ (Main & Sub Keyboards)
# =================================================================
def get_main_keyboard():
    """মূল হোম কিবোর্ড"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_task = types.KeyboardButton("💼 কাজ ⚡")
    btn_balance = types.KeyboardButton("💰 ব্যালেন্স 💎")
    btn_refer = types.KeyboardButton("👥 রেফার 🎁")
    btn_support = types.KeyboardButton("🛠️ সাপোর্ট 💬")

    keyboard.row(btn_task, btn_balance)
    keyboard.row(btn_refer, btn_support)
    return keyboard

def get_work_keyboard():
    """কাজের সাব-কিবোর্ড"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_video = types.KeyboardButton("🎬 ভিডিও এড দেখুন")
    btn_tasks = types.KeyboardButton("📋 ট্যাক্স সম্পূর্ণ করুন")
    btn_back = types.KeyboardButton("🔙 ব্যাক")

    keyboard.row(btn_video, btn_tasks)
    keyboard.row(btn_back)
    return keyboard

# =================================================================
# ১. /start কমান্ড হ্যান্ডলার
# =================================================================
@bot.message_handler(commands=['start'])
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

    threading.Thread(target=handle_referral_and_user_creation, args=(user_id, full_name, username, referrer_id)).start()

    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
    btn_webapp = types.InlineKeyboardButton(text="🚀 ওপেন আর্নিং অ্যাপ 📱", web_app=types.WebAppInfo(url=webapp_url))
    
    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে প্রতিদিন টাকা ইনকাম করুন!\n\n🚀 প্রতি রেফারে পাবেন ৫০ টাকা!\n\n👉 জয়েন লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"
    btn_share = types.InlineKeyboardButton(text="📢 বন্ধুদের শেয়ার করুন 🎁", url=share_url)

    inline_kb.add(btn_webapp, btn_share)

    welcome_text = f"""👑 <b>MH EARNING BOT PREMIER</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>✨ <b>ঘরে বসে স্মার্ট উপায়ে আয় করার প্রিমিয়াম প্ল্যাটফর্ম!</b>

✅ <b>ভিডিও বিজ্ঞাপন দেখে আনলিমিটেড ইনকাম</b>
✅ <b>সোশ্যাল ট্যাক্স সম্পূর্ণ করে বড় রিওয়ার্ড</b>
✅ <b>প্রতি রেফারে ইনস্ট্যান্ট ৳ ৫০.০০ টাকা</b>
✅ <b>বিকাশ ও নগদে সরাসরি অটো উইথড্র</b></blockquote>

🔗 <b>আপনার পার্সোনাল রেফারেল লিংক:</b>
<code>{referral_link}</code>"""

    bot.send_message(message.chat.id, welcome_text, reply_markup=inline_kb, disable_web_page_preview=True)
    bot.send_message(message.chat.id, "👇 <b>নিচের কিবোর্ড থেকে অপশন সিলেক্ট করুন:</b>", reply_markup=get_main_keyboard())

# =================================================================
# ২. কাজের বাটন হ্যান্ডলার (💼 কাজ ⚡ / /কাজ / কাজ)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["কাজ", "work", "task", "/কাজ", "/task", "/work"]))
def work_options_handler(message):
    reply_text = """💼 <b>কাজের অপশন সিলেক্ট করুন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ আপনি দুইভাবে কাজ করে প্রতিদিন টাকা আয় করতে পারবেন:

🎬 <b>ভিডিও এড দেখুন:</b> ছোট ছোট বিজ্ঞাপন দেখে ইনস্ট্যান্ট ওয়ালেটে টাকা যোগ করুন।
📋 <b>ট্যাক্স সম্পূর্ণ করুন:</b> সোশ্যাল চ্যানেলে যুক্ত হয়ে বড় অংকের রিওয়ার্ড জিতে নিন।</blockquote>

👇 <i>নিচের কিবোর্ড থেকে যেকোনো একটি অপশন বেছে নিন:</i>"""

    bot.send_message(message.chat.id, reply_text, reply_markup=get_work_keyboard())

# =================================================================
# ৩. ভিডিও এড দেখুন হ্যান্ডলার (🎬 ভিডিও এড দেখুন)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["ভিডিও", "video", "/video", "এড"]))
def video_ad_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    ads_watched = int(user_data.get("adsWatched", 0))

    auto_ad_webapp_url = f"{MINI_APP_URL}#action=watch_ad&tgWebAppStartParam={user_id}"

    ad_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_open_ad = types.InlineKeyboardButton(text="🚀 ওপেন (ভিডিও এড দেখুন) ⚡", web_app=types.WebAppInfo(url=auto_ad_webapp_url))
    ad_kb.add(btn_open_ad)

    msg_text = f"""🎬 <b>প্রিমিয়াম ভিডিও বিজ্ঞাপন জোন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>💎 <b>বিজ্ঞাপন রিওয়ার্ড:</b> <b>৳ {AD_REWARD:.2f} টাকা</b> প্রতি ভিডিও!
📊 <b>আজকের দেখা ভিডিও:</b> <b>{ads_watched} / 10</b> টি

⚡ <b>নিয়মাবলী:</b>
১. নিচের <b>'ওপেন'</b> বাটনে চাপ দিলে ফুল-স্ক্রিন ভিডিও চালু হবে।
২. বিজ্ঞাপনটি সম্পূর্ণ শেষ হওয়া পর্যন্ত দেখুন।
৩. দেখা শেষ হওয়ামাত্রই টাকা সরাসরি মূল একাউন্টে যুক্ত হবে।</blockquote>

👇 <i>বিজ্ঞাপন দেখতে নিচের বাটনে ট্যাপ করুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=ad_kb, disable_web_page_preview=True)

# =================================================================
# ৪. ট্যাক্স সম্পূর্ণ করুন হ্যান্ডলার (📋 ট্যাক্স সম্পূর্ণ করুন)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["ট্যাক্স", "টাস্ক", "tasks", "task"]))
def task_dashboard_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    completed_tasks = user_data.get("completedTasks", {})

    all_tasks = get_all_tasks_from_db()

    if not all_tasks:
        normal_webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
        no_task_kb = types.InlineKeyboardMarkup()
        no_task_kb.add(types.InlineKeyboardButton("📱 আর্নিং অ্যাপে টাস্ক দেখুন", web_app=types.WebAppInfo(url=normal_webapp_url)))
        
        bot.send_message(
            message.chat.id,
            """📋 <b>সোশ্যাল ট্যাক্স ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>বর্তমানে বটে কোনো নতুন ট্যাক্স নেই। অ্যাপ থেকে নতুন ট্যাক্স চেক করুন!</blockquote>""",
            reply_markup=no_task_kb
        )
        return

    msg_text = """📋 <b>সোশ্যাল ট্যাক্স ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ <b>কাজের নিয়মাবলী:</b>
১. নিচের লিংকগুলোতে ক্লিক করে চ্যানেল/গ্রুপে জয়েন করুন।
২. জয়েন সম্পন্ন হলে <b>'✅ ভেরিফাই করুন'</b> বাটনে চাপ দিন।
৩. ভেরিফাই হওয়ামাত্রই বোনাস ব্যালেন্সে যুক্ত হবে!</blockquote>\n"""

    task_kb = types.InlineKeyboardMarkup(row_width=1)
    
    pending_tasks_count = 0
    for task_id, task in all_tasks.items():
        if isinstance(task, dict):
            if task_id in completed_tasks:
                continue

            pending_tasks_count += 1
            title = task.get("title", f"ট্যাক্স #{task_id}")
            reward = float(task.get("reward", 5.00))
            link = task.get("url", task.get("link", "https://t.me"))

            btn_link = types.InlineKeyboardButton(text=f"👉 {title} (৳ {reward:.2f})", url=link)
            btn_verify = types.InlineKeyboardButton(text=f"✅ ভেরিফাই করুন ({title})", callback_data=f"verify_{task_id}")
            
            task_kb.add(btn_link, btn_verify)

    if pending_tasks_count == 0:
        bot.send_message(message.chat.id, "🎉 <b>অভিনন্দন! আপনি সব ট্যাক্স সম্পূর্ণ করে ফেলেছেন!</b>\nনতুন ট্যাক্স যুক্ত হলে এখানে দেখতে পাবেন।", reply_markup=get_main_keyboard())
    else:
        bot.send_message(message.chat.id, msg_text, reply_markup=task_kb, disable_web_page_preview=True)

# =================================================================
# ৫. ট্যাক্স ভেরিফাই Callback Query
# =================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_task_callback(call):
    user_id = str(call.from_user.id)
    task_id = call.data.replace("verify_", "")

    user_data = get_user_from_db(user_id) or {}
    completed_tasks = user_data.get("completedTasks", {})

    if task_id in completed_tasks:
        bot.answer_callback_query(call.id, "⚠️ আপনি এই ট্যাক্সটি আগেই সম্পূর্ণ করেছেন!", show_alert=True)
        return

    tasks = get_all_tasks_from_db()
    task = tasks.get(task_id)

    if not task:
        bot.answer_callback_query(call.id, "❌ ট্যাক্সটি আর সক্রিয় নেই!", show_alert=True)
        return

    task_reward = float(task.get("reward", 5.00))
    task_title = task.get("title", "ট্যাক্স")
    
    cur_bal = float(user_data.get("balance", 0.0))
    cur_tasks_count = int(user_data.get("completedTasksCount", 0))

    new_balance = cur_bal + task_reward
    new_tasks_count = cur_tasks_count + 1

    update_user_in_db(user_id, {
        "balance": new_balance,
        "completedTasksCount": new_tasks_count,
        f"completedTasks/{task_id}": True
    })

    bot.answer_callback_query(call.id, f"🎉 অভিনন্দন! +৳ {task_reward:.2f} টাকা একাউন্টে যুক্ত হয়েছে!", show_alert=True)

    success_text = f"""✅ <b>ট্যাক্স সফলভাবে সম্পন্ন হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎯 <b>ট্যাক্স:</b> {task_title}
💰 <b>রিওয়ার্ড:</b> <b>+ ৳ {task_reward:.2f} টাকা</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>টাকাটি সরাসরি আপনার ওয়ালেটে যুক্ত হয়েছে!</i>"""

    bot.send_message(call.message.chat.id, success_text)

# =================================================================
# ৬. ব্যালেন্স বাটন হ্যান্ডলার (💰 ব্যালেন্স 💎 / ব্যালেন্স)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["ব্যালেন্স", "balance", "/balance"]))
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
    btn_open_wallet = types.InlineKeyboardButton(text="💳 ওয়ালেট ও টাকা উইথড্র 💸", web_app=types.WebAppInfo(url=webapp_url))
    bal_kb.add(btn_open_wallet)

    msg_text = f"""👤 <b>লাইভ একাউন্ট ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🏷️ <b>নাম:</b> {user_name}
🆔 <b>আইডি:</b> <code>{user_id}</code>

💵 <b>মূল ব্যালেন্স:</b> <b>৳ {balance:.2f}</b> টাকা
👥 <b>মোট সফল রেফার:</b> <b>{referrals}</b> জন
🎬 <b>আজকের দেখা ভিডিও:</b> <b>{ads_watched}</b> টি
✅ <b>ট্যাক্স সম্পন্ন:</b> <b>{tasks_done}</b> টি</blockquote>

📌 <i>বিকাশ বা নগদে টাকা তুলতে নিচের বাটনে চাপুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=bal_kb)

# =================================================================
# ৭. রেফার বাটন হ্যান্ডলার (👥 রেফার 🎁 / রেফার)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["রেফার", "refer", "/refer"]))
def refer_handler(message):
    user_id = str(message.from_user.id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    user_data = get_user_from_db(user_id) or {}
    total_refs = int(user_data.get("referrals", 0))
    earned_from_refs = total_refs * REFER_REWARD

    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম শুরু করুন!\n\n👉 রেফারেল লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"

    ref_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_share = types.InlineKeyboardButton(text="📢 রেফার লিংক বন্ধুদের শেয়ার 🚀", url=share_url)
    ref_kb.add(btn_share)

    msg_text = f"""👥 <b>রেফারেল ইনকাম সেন্টার</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎁 <b>প্রতি রেফারে বোনাস:</b> <b>৳ {REFER_REWARD:.2f}</b> টাকা!
📊 <b>সর্বমোট রেফারেল:</b> <b>{total_refs}</b> জন
💰 <b>রেফার থেকে আয়:</b> <b>৳ {earned_from_refs:.2f}</b> টাকা</blockquote>

🔗 <b>আপনার পার্সোনাল রেফার লিংক:</b>
<code>{referral_link}</code>

<i>(লিংকটিতে একবার ট্যাপ করলেই কপি হয়ে যাবে)</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=ref_kb, disable_web_page_preview=True)

# =================================================================
# ৮. সাপোর্ট বাটন হ্যান্ডলার (🛠️ সাপোর্ট 💬 / সাপোর্ট)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["সাপোর্ট", "support", "/support"]))
def support_handler(message):
    sup_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_admin = types.InlineKeyboardButton(text="👨‍💻 এডমিন লাইভ সাপোর্ট 💬", url=f"https://t.me/{SUPPORT_USERNAME}")
    sup_kb.add(btn_admin)

    msg_text = f"""🛠️ <b>হেল্প ও সাপোর্ট সেন্টার</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>পেমেন্ট বা কাজ সংক্রান্ত যেকোনো সহায়তার জন্য সরাসরি আমাদের অফিসিয়াল এডমিনের সাথে কথা বলুন।

⏰ <b>সাপোর্ট সময়:</b> সকাল ৯:০০ টা - রাত ১১:০০ টা
👤 <b>অফিসিয়াল এডমিন:</b> @{SUPPORT_USERNAME}</blockquote>

👇 <i>এডমিনকে মেসেজ দিতে নিচের বাটনে ট্যাপ করুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=sup_kb)

# =================================================================
# ৯. ব্যাক বাটন হ্যান্ডলার (🔙 ব্যাক / মূল মেন্যু)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["ব্যাক", "back", "/back", "মেন্যু"]))
def back_to_main_menu(message):
    bot.send_message(message.chat.id, "🏠 <b>মূল মেন্যুতে ফিরে আসা হয়েছে:</b>", reply_markup=get_main_keyboard())

# =================================================================
# 🚀 মেইন রানার (Keep-Alive + Polling Engine)
# =================================================================
if __name__ == "__main__":
    print("🌐 Keep-Alive Server চালু হচ্ছে...")
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("✅ MH Earning Bot Ultra Engine সফলভাবে চালু হয়েছে...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
