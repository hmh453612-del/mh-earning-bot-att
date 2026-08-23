import os
import threading
import time
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

# 👑 সুপার অ্যাডমিন টেলিগ্রাম আইডি
ADMIN_ID = 8855522653

FIREBASE_DB_URL = "https://mh-earning-bot-default-rtdb.asia-southeast1.firebasedatabase.app"

AD_REWARD = 10.00
REFER_REWARD = 50.00

# টেলিগ্রাম বট ইঞ্জিন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

# =================================================================
# 🌐 Render Keep-Alive Web Server
# =================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "👑 MH Earning Bot Ultra Engine with Admin Panel is Running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# =================================================================
# 🔥 Firebase Helper Engine
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

def get_all_users_from_db():
    """ফায়ারবেজ থেকে সব ইউজারের ডাটা লোড করা"""
    try:
        url = f"{FIREBASE_DB_URL}/users.json"
        res = requests.get(url, timeout=8)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase All Users Error: {e}")
    return {}

def get_all_tasks_from_db():
    """ফায়ারবেজ থেকে টাস্ক লোড করা"""
    try:
        url = f"{FIREBASE_DB_URL}/tasks.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Tasks Fetch Error: {e}")
    return {}

def add_task_to_db(task_id, task_data):
    try:
        url = f"{FIREBASE_DB_URL}/tasks/{task_id}.json"
        requests.put(url, json=task_data, timeout=5)
        return True
    except Exception as e:
        print(f"Firebase Add Task Error: {e}")
        return False

def delete_task_from_db(task_id):
    try:
        url = f"{FIREBASE_DB_URL}/tasks/{task_id}.json"
        requests.delete(url, timeout=5)
        return True
    except Exception as e:
        print(f"Firebase Delete Task Error: {e}")
        return False

def extract_telegram_username(url):
    if not url:
        return None
    if '/+' in url or '/joinchat/' in url or 'joinchat' in url:
        return None
    try:
        url_clean = url.replace("https://", "").replace("http://", "")
        parts = [p for p in url_clean.split('/') if p]
        if len(parts) > 1 and parts[0] in ['t.me', 'telegram.me']:
            uname = parts[1].replace('@', '')
            if uname.lower() not in ['share', 'addstickers', 'joinchat', 's']:
                return uname
    except Exception:
        pass
    return None

def verify_telegram_membership(channel_username, user_id):
    try:
        chat_member = bot.get_chat_member(f"@{channel_username}", int(user_id))
        if chat_member.status in ['member', 'administrator', 'creator', 'restricted']:
            return True
    except Exception as e:
        print(f"Channel Verify Error: {e}")
    return False

def handle_referral_and_user_creation(user_id, full_name, username, referrer_id):
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
            "completedTasksList": {},
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

⚡ <i>বোনাসটি সরাসরি আপনার মূল ওয়ালেটে যুক্ত হয়েছে!</i>"""

                    bot.send_message(int(referrer_id), notify_text, reply_markup=notify_kb, disable_web_page_preview=True)
                except Exception as err:
                    print(f"Referral Notification Error: {err}")
    else:
        update_user_in_db(user_id_str, {
            "name": full_name,
            "username": f"@{username}" if username else "N/A"
        })

# =================================================================
# ⌨️ কিবোর্ড লেআউটসমূহ (User Keyboards)
# =================================================================
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_task = types.KeyboardButton("💼 কাজ ⚡")
    btn_balance = types.KeyboardButton("💰 ব্যালেন্স 💎")
    btn_refer = types.KeyboardButton("👥 রেফার 🎁")
    btn_support = types.KeyboardButton("🛠️ সাপোর্ট 💬")

    keyboard.row(btn_task, btn_balance)
    keyboard.row(btn_refer, btn_support)
    return keyboard

def get_work_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_video = types.KeyboardButton("🎬 ভিডিও এড দেখুন")
    btn_tasks = types.KeyboardButton("📋 ট্যাক্স সম্পূর্ণ করুন")
    btn_back = types.KeyboardButton("🔙 ব্যাক")

    keyboard.row(btn_video, btn_tasks)
    keyboard.row(btn_back)
    return keyboard

# =================================================================
# 👑 প্রফেশনাল অ্যাডমিন প্যানেল কিবোর্ড ও ইঞ্জিন
# =================================================================
def get_admin_dashboard_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    b_stats = types.InlineKeyboardButton("📊 লাইভ পরিসংখ্যান", callback_data="adm_stats")
    b_broadcast = types.InlineKeyboardButton("📢 অল ইউজার ব্রডকাস্ট", callback_data="adm_broadcast")
    b_add_task = types.InlineKeyboardButton("➕ নতুন ট্যাক্স যোগ", callback_data="adm_add_task")
    b_del_task = types.InlineKeyboardButton("🗑️ ট্যাক্স ডিলিট / ভিউ", callback_data="adm_view_tasks")
    b_user_ctrl = types.InlineKeyboardButton("👤 ইউজার ব্যালেন্স কন্ট্রোল", callback_data="adm_user_ctrl")
    b_direct_msg = types.InlineKeyboardButton("✉️ নির্দিষ্ট ইউজারকে SMS", callback_data="adm_direct_msg")
    b_close = types.InlineKeyboardButton("❌ প্যানেল বন্ধ করুন", callback_data="adm_close")
    
    markup.row(b_stats, b_broadcast)
    markup.row(b_add_task, b_del_task)
    markup.row(b_user_ctrl, b_direct_msg)
    markup.row(b_close)
    return markup

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        unauth_msg = f"""🚫 <b>অ্যাক্সেস ডিনাইড (Access Denied)!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚠️ এই কমান্ডটি শুধুমাত্র সিস্টেম অ্যাডমিনিস্ট্রেটরের জন্য সংরক্ষিত।</blockquote>

👉 বটের অন্যান্য সুবিধা ব্যবহার করতে নিচের বাটনে চাপ দিন বা /start লিখুন।"""
        bot.send_message(message.chat.id, unauth_msg, reply_markup=get_main_keyboard())
        return

    admin_panel_text = f"""👑 <b>MH EARNING MASTER ADMIN PANEL</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>স্বাগতম অ্যাডমিন! আপনার বট ও মিনি অ্যাপ কন্ট্রোল সিস্টেম পুরোপুরি প্রস্তুত।

👤 <b>অ্যাডমিন আইডি:</b> <code>{ADMIN_ID}</code>
🟢 <b>সিস্টেম স্ট্যাটাস:</b> অনলাইন (Active 24/7)</blockquote>

👇 <i>নিচের অপশনগুলো থেকে প্রয়োজনীয় অ্যাকশন নির্বাচন করুন:</i>"""
    bot.send_message(message.chat.id, admin_panel_text, reply_markup=get_admin_dashboard_markup())

# --- অ্যাডমিন কলব্যাক হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 আপনার এই অ্যাকশন করার অনুমতি নেই!", show_alert=True)
        return

    action = call.data

    # ১. লাইভ পরিসংখ্যান
    if action == "adm_stats":
        bot.answer_callback_query(call.id, "📊 ডাটা লোড হচ্ছে...")
        users = get_all_users_from_db()
        tasks = get_all_tasks_from_db()

        total_users = len(users) if users else 0
        total_balance = sum(float(u.get("balance", 0.0)) for u in users.values()) if users else 0.0
        total_referrals = sum(int(u.get("referrals", 0)) for u in users.values()) if users else 0
        total_tasks = len(tasks) if tasks else 0

        stats_text = f"""📊 <b>লাইভ সিস্টেম পরিসংখ্যান (Analytics)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👥 <b>সর্বমোট ইউজার:</b> <b>{total_users:,}</b> জন
💵 <b>ইউজারদের মোট ব্যালেন্স:</b> <b>৳ {total_balance:,.2f}</b> টাকা
🎁 <b>সর্বমোট রেফারেল:</b> <b>{total_referrals:,}</b> টি
📋 <b>বর্তমানে একটিভ ট্যাক্স:</b> <b>{total_tasks}</b> টি
⚡ <b>সার্ভার পিং:</b> সক্রিয় ও দ্রুততম</blockquote>

🔄 <i>প্রতি মুহূর্তের লাইভ রিয়েলটাইম তথ্য।</i>"""
        
        back_kb = types.InlineKeyboardMarkup()
        back_kb.add(types.InlineKeyboardButton("🔙 অ্যাডমিন মেন্যু", callback_data="adm_back_menu"))
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, reply_markup=back_kb)

    # ২. অল ইউজার ব্রডকাস্ট
    elif action == "adm_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📢 <b>ব্রডকাস্ট মেসেজ লিখুন:</b>\n\nআপনি যে মেসেজটি সকল ইউজারকে পাঠাতে চান তা লিখুন (HTML ট্যাগ যেমন <b>bold</b>, <i>italic</i>, <code>code</code> ব্যবহার করতে পারেন)।\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_broadcast_message)

    # ৩. নতুন ট্যাক্স যোগ
    elif action == "adm_add_task":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📋 <b>নতুন ট্যাক্স যোগ করুন</b>\n\nধাপ ১: ট্যাক্সের নাম/টাইটেল লিখুন (যেমন: Join VIP Channel):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_task_title_step)

    # ৪. ট্যাক্স ডিলিট / ভিউ
    elif action == "adm_view_tasks":
        bot.answer_callback_query(call.id)
        tasks = get_all_tasks_from_db()
        if not tasks:
            back_kb = types.InlineKeyboardMarkup()
            back_kb.add(types.InlineKeyboardButton("🔙 ফিরে যান", callback_data="adm_back_menu"))
            bot.edit_message_text("⚠️ ডাটাবেজে বর্তমানে কোনো সক্রিয় ট্যাক্স নেই!", call.message.chat.id, call.message.message_id, reply_markup=back_kb)
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for task_id, task in tasks.items():
            if isinstance(task, dict):
                title = task.get("title", "Unknown")
                reward = task.get("reward", 0.0)
                markup.add(types.InlineKeyboardButton(f"🗑️ ডিলিট: {title} (৳ {reward})", callback_data=f"del_task_{task_id}"))
        
        markup.add(types.InlineKeyboardButton("🔙 ফিরে যান", callback_data="adm_back_menu"))
        bot.edit_message_text("📋 <b>যেকোনো ট্যাক্স মুছে ফেলতে নিচের বাটনে চাপ দিন:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ৫. ইউজার ব্যালেন্স কন্ট্রোল
    elif action == "adm_user_ctrl":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "👤 <b>ইউজার ব্যালেন্স ম্যানেজমেন্ট</b>\n\nযে ইউজারের ব্যালেন্স পরিবর্তন করতে চান তার <b>Telegram User ID</b> লিখুন:\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_user_lookup)

    # ৬. নির্দিষ্ট ইউজারকে মেসেজ
    elif action == "adm_direct_msg":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "✉️ <b>নির্দিষ্ট ইউজারকে মেসেজ পাঠান</b>\n\nইউজারের <b>Telegram User ID</b> লিখুন:\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_direct_msg_id)

    # ৭. ব্যাক মেন্যু
    elif action == "adm_back_menu":
        bot.answer_callback_query(call.id)
        admin_panel_text = f"""👑 <b>MH EARNING MASTER ADMIN PANEL</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>স্বাগতম অ্যাডমিন! আপনার বট ও মিনি অ্যাপ কন্ট্রোল সিস্টেম পুরোপুরি প্রস্তুত।

👤 <b>অ্যাডমিন আইডি:</b> <code>{ADMIN_ID}</code>
🟢 <b>সিস্টেম স্ট্যাটাস:</b> অনলাইন (Active 24/7)</blockquote>

👇 <i>নিচের অপশনগুলো থেকে প্রয়োজনীয় অ্যাকশন নির্বাচন করুন:</i>"""
        bot.edit_message_text(admin_panel_text, call.message.chat.id, call.message.message_id, reply_markup=get_admin_dashboard_markup())

    # ৮. প্যানেল ক্লোজ
    elif action == "adm_close":
        bot.answer_callback_query(call.id, "প্যানেল বন্ধ করা হয়েছে")
        bot.delete_message(call.message.chat.id, call.message.message_id)

# ট্যাক্স ডিলিট এক্সিকিউশন
@bot.callback_query_handler(func=lambda call: call.data.startswith("del_task_"))
def execute_delete_task(call):
    if call.from_user.id != ADMIN_ID:
        return
    task_id = call.data.replace("del_task_", "")
    if delete_task_from_db(task_id):
        bot.answer_callback_query(call.id, "✅ ট্যাক্স সফলভাবে মুছে ফেলা হয়েছে!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ ট্যাক্স মুছতে সমস্যা হয়েছে!", show_alert=True)
    
    # মেন্যুতে ফেরত নিয়ে যাওয়া
    admin_panel_text = f"""👑 <b>MH EARNING MASTER ADMIN PANEL</b> 👑\n━━━━━━━━━━━━━━━━━━━━━━━━━\nট্যাক্স মুছে ফেলা হয়েছে। অন্য কাজ নির্বাচন করুন:"""
    bot.edit_message_text(admin_panel_text, call.message.chat.id, call.message.message_id, reply_markup=get_admin_dashboard_markup())

# =================================================================
# 📢 অ্যাডমিন স্টেপ হ্যান্ডলারস (Admin Next Step Handlers)
# =================================================================

# --- ১. ব্রডকাস্ট ইঞ্জিন ---
def process_broadcast_message(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ ব্রডকাস্ট বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return

    broadcast_content = message.text
    users = get_all_users_from_db()
    if not users:
        bot.send_message(message.chat.id, "⚠️ ডাটাবেজে কোনো ইউজার পাওয়া যায়নি!")
        return

    status_msg = bot.send_message(message.chat.id, "⏳ <b>ব্রডকাস্ট শুরু হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।</b>")

    sent = 0
    failed = 0

    def run_broadcast():
        nonlocal sent, failed
        for uid in users.keys():
            try:
                bot.send_message(int(uid), broadcast_content, disable_web_page_preview=True)
                sent += 1
                time.sleep(0.05) # Rate limit protection
            except Exception:
                failed += 1

        summary = f"""🎉 <b>ব্রডকাস্ট সম্পন্ন হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>✅ <b>সফলভাবে পাঠানো হয়েছে:</b> {sent} জন
❌ <b>ব্যর্থ (ব্লক/আনইনস্টল):</b> {failed} জন
👥 <b>সর্বমোট টার্গেট:</b> {len(users)} জন</blockquote>"""
        bot.send_message(ADMIN_ID, summary, reply_markup=get_main_keyboard())

    threading.Thread(target=run_broadcast).start()

# --- ২. ট্যাক্স অ্যাড ইঞ্জিন ---
def process_task_title_step(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ টাস্ক তৈরি বাতিল করা হয়েছে।")
        return

    title = message.text.strip()
    msg = bot.send_message(
        message.chat.id,
        f"🎯 <b>ট্যাক্স:</b> {title}\n\nধাপ ২: এই ট্যাক্সের রিওয়ার্ড বা টাকার পরিমাণ লিখুন (যেমন: 5 বা 10):"
    )
    bot.register_next_step_handler(msg, process_task_reward_step, title)

def process_task_reward_step(message, title):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ টাস্ক তৈরি বাতিল করা হয়েছে।")
        return

    try:
        reward = float(message.text.strip())
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা লিখুন (যেমন: 5.00):")
        bot.register_next_step_handler(msg, process_task_reward_step, title)
        return

    msg = bot.send_message(
        message.chat.id,
        f"🎯 <b>ট্যাক্স:</b> {title}\n💰 <b>রিওয়ার্ড:</b> ৳ {reward:.2f}\n\nধাপ ৩: টেলিগ্রাম চ্যানেল/গ্রুপ বা ওয়েবসাইটের লিংক দিন (যেমন: https://t.me/yourchannel):"
    )
    bot.register_next_step_handler(msg, process_task_link_step, title, reward)

def process_task_link_step(message, title, reward):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ টাস্ক তৈরি বাতিল করা হয়েছে।")
        return

    link = message.text.strip()
    task_id = f"task_{int(time.time())}"

    new_task = {
        "title": title,
        "reward": reward,
        "link": link,
        "createdAt": int(time.time() * 1000)
    }

    if add_task_to_db(task_id, new_task):
        succ_text = f"""🎉 <b>নতুন ট্যাক্স সফলভাবে যোগ হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>📋 <b>টাইটেল:</b> {title}
💎 <b>রিওয়ার্ড:</b> ৳ {reward:.2f} টাকা
🔗 <b>লিংক:</b> {link}</blockquote>

⚡ <i>ইউজাররা এখন এটি বট ও মিনি অ্যাপ উভয় স্থানে দেখতে পাবে।</i>"""
        bot.send_message(message.chat.id, succ_text, reply_markup=get_main_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ ট্যাক্স ডাটাবেজে সংরক্ষণ করতে ব্যর্থ হয়েছে!", reply_markup=get_main_keyboard())

# --- ৩. ইউজার ব্যালেন্স কন্ট্রোল ইঞ্জিন ---
def process_user_lookup(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ অপারেশন বাতিল।")
        return

    target_uid = message.text.strip()
    u_data = get_user_from_db(target_uid)

    if not u_data:
        bot.send_message(message.chat.id, f"❌ আইডি: <code>{target_uid}</code> দিয়ে কোনো ইউজার পাওয়া যায়নি!", reply_markup=get_main_keyboard())
        return

    u_name = u_data.get("name", "N/A")
    u_bal = float(u_data.get("balance", 0.0))
    u_ref = u_data.get("referrals", 0)

    u_info = f"""👤 <b>ইউজার প্রোফাইল বিবরণী</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🆔 <b>ইউজার আইডি:</b> <code>{target_uid}</code>
🏷️ <b>নাম:</b> {u_name}
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {u_bal:.2f}</b> টাকা
👥 <b>রেফার সংখ্যা:</b> {u_ref} জন</blockquote>

👇 <i>ব্যালেন্স পরিবর্তন করতে নতুন ব্যালেন্সের পরিমাণ লিখুন (যেমন: ১০০ করার জন্য 100 বা যোগ/বিয়োগ করার জন্য সরাসরি নতুন ব্যালেন্স সংখ্যাটি লিখুন):</i>"""
    
    msg = bot.send_message(message.chat.id, u_info)
    bot.register_next_step_handler(msg, process_update_balance, target_uid, u_name)

def process_update_balance(message, target_uid, u_name):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ ব্যালেন্স পরিবর্তন বাতিল।")
        return

    try:
        new_balance = float(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা গ্রহণযোগ্য। বাতিল করা হলো।")
        return

    update_user_in_db(target_uid, {"balance": new_balance})

    bot.send_message(
        message.chat.id,
        f"✅ <b>ব্যালেন্স সফলভাবে আপডেট হয়েছে!</b>\n\n👤 ইউজার: {u_name}\n🆔 আইডি: <code>{target_uid}</code>\n💵 নতুন ব্যালেন্স: <b>৳ {new_balance:.2f} টাকা</b>",
        reply_markup=get_main_keyboard()
    )

    try:
        bot.send_message(
            int(target_uid),
            f"🔔 <b>অ্যাডমিন নোটিফিকেশন:</b>\nআপনার ওয়ালেট ব্যালেন্স অ্যাডমিন কর্তৃক আপডেট করা হয়েছে।\n💵 বর্তমান ওয়ালেট ব্যালেন্স: <b>৳ {new_balance:.2f} টাকা</b>"
        )
    except Exception:
        pass

# --- ৪. নির্দিষ্ট ইউজারকে SMS পাঠানো ইঞ্জিন ---
def process_direct_msg_id(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।")
        return

    target_uid = message.text.strip()
    msg = bot.send_message(
        message.chat.id,
        f"✉️ <b>টার্গেট আইডি:</b> <code>{target_uid}</code>\n\nএখন মেসেজটি লিখুন যা এই ইউজারের কাছে পাঠানো হবে:"
    )
    bot.register_next_step_handler(msg, process_send_direct_msg, target_uid)

def process_send_direct_msg(message, target_uid):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।")
        return

    user_msg = message.text
    try:
        bot.send_message(
            int(target_uid),
            f"""📩 <b>এডমিনের পক্ষ থেকে সরাসরি বার্তা</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>{user_msg}</blockquote>

💬 <i>যেকোনো প্রয়োজনে সাপোর্টে যোগাযোগ করুন।</i>"""
        )
        bot.send_message(message.chat.id, f"✅ ইউজার <code>{target_uid}</code> এর কাছে সফলভাবে বার্তা পাঠানো হয়েছে!", reply_markup=get_main_keyboard())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ বার্তা পাঠানো যায়নি! ত্রুটি: {e}", reply_markup=get_main_keyboard())

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
<blockquote>✨ <b>ঘরে বসে সহজ উপায়ে আয় করার প্রিমিয়াম প্ল্যাটফর্ম!</b>

✅ <b>ভিডিও বিজ্ঞাপন দেখে আনলিমিটেড ইনকাম</b>
✅ <b>সোশ্যাল ট্যাক্স সম্পূর্ণ করে বড় রিওয়ার্ড</b>
✅ <b>প্রতি রেফারে ইনস্ট্যান্ট ৳ ৫০.০০ টাকা</b>
✅ <b>বিকাশ ও নগদে সরাসরি অটো উইথড্র</b></blockquote>

🔗 <b>আপনার পার্সোনাল রেফারেল লিংক:</b>
<code>{referral_link}</code>"""

    bot.send_message(message.chat.id, welcome_text, reply_markup=inline_kb, disable_web_page_preview=True)
    bot.send_message(message.chat.id, "👇 <b>নিচের মেন্যু থেকে অপশন বেছে নিন:</b>", reply_markup=get_main_keyboard())

# =================================================================
# ২. কাজের বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["💼 কাজ ⚡", "কাজ", "work", "task", "/কাজ", "/task", "/work"]))
def work_options_handler(message):
    reply_text = """💼 <b>কাজের অপশন সিলেক্ট করুন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ আপনি দুইভাবে কাজ করে প্রতিদিন টাকা আয় করতে পারবেন:

🎬 <b>ভিডিও এড দেখুন:</b> ছোট ছোট বিজ্ঞাপন দেখে ইনস্ট্যান্ট ওয়ালেটে টাকা যোগ করুন।
📋 <b>ট্যাক্স সম্পূর্ণ করুন:</b> সোশ্যাল চ্যানেলে যুক্ত হয়ে বড় অংকের রিওয়ার্ড জিতে নিন।</blockquote>

👇 <i>নিচের কিবোর্ড থেকে যেকোনো একটি অপশন বেছে নিন:</i>"""

    bot.send_message(message.chat.id, reply_text, reply_markup=get_work_keyboard())

# =================================================================
# ৩. ভিডিও এড দেখুন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["🎬 ভিডিও এড দেখুন", "ভিডিও", "video", "/video", "এড"]))
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
৩. দেখা শেষ হওয়ামাত্রই টাকা সরাসরি মূল ওয়ালেটে যুক্ত হবে।</blockquote>

👇 <i>বিজ্ঞাপন দেখতে নিচের বাটনে ট্যাপ করুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=ad_kb, disable_web_page_preview=True)

# =================================================================
# ৪. ট্যাক্স সম্পূর্ণ করুন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["📋 ট্যাক্স সম্পূর্ণ করুন", "ট্যাক্স", "টাস্ক", "tasks", "task"]))
def task_dashboard_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    completed_tasks_list = user_data.get("completedTasksList", {}) or {}

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
            if completed_tasks_list.get(str(task_id)) is True:
                continue

            pending_tasks_count += 1
            title = task.get("title", f"ট্যাক্স #{task_id}")
            reward = float(task.get("reward", 5.00))
            link = task.get("link", task.get("url", "https://t.me"))

            btn_link = types.InlineKeyboardButton(text=f"👉 {title} (৳ {reward:.2f})", url=link)
            btn_verify = types.InlineKeyboardButton(text=f"✅ ভেরিফাই করুন ({title})", callback_data=f"verify_{task_id}")
            
            task_kb.add(btn_link, btn_verify)

    if pending_tasks_count == 0:
        bot.send_message(
            message.chat.id, 
            "🎉 <b>অভিনন্দন! আপনি অ্যাপ ও বটের সব ট্যাক্স সম্পন্ন করে ফেলেছেন!</b>\nনতুন ট্যাক্স যুক্ত হলে এখানে আবার দেখতে পাবেন।", 
            reply_markup=get_main_keyboard()
        )
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
    completed_tasks_list = user_data.get("completedTasksList", {}) or {}

    if completed_tasks_list.get(str(task_id)) is True:
        bot.answer_callback_query(call.id, "⚠️ আপনি এই ট্যাক্সটি আগেই সম্পূর্ণ করেছেন!", show_alert=True)
        return

    tasks = get_all_tasks_from_db()
    task = tasks.get(task_id)

    if not task:
        bot.answer_callback_query(call.id, "❌ ট্যাক্সটি আর সক্রিয় নেই!", show_alert=True)
        return

    task_reward = float(task.get("reward", 5.00))
    task_title = task.get("title", "ট্যাক্স")
    task_link = task.get("link", task.get("url", ""))

    channel_username = extract_telegram_username(task_link)
    
    if channel_username:
        is_member = verify_telegram_membership(channel_username, user_id)
        if not is_member:
            bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি! আগে জয়েন করুন, তারপর ভেরিফাই বাটনে চাপুন।", show_alert=True)
            return

    cur_bal = float(user_data.get("balance", 0.0))
    cur_tasks_count = int(user_data.get("completedTasksCount", 0))

    new_balance = cur_bal + task_reward
    new_tasks_count = cur_tasks_count + 1

    update_user_in_db(user_id, {
        "balance": new_balance,
        "completedTasksCount": new_tasks_count,
        f"completedTasksList/{task_id}": True
    })

    bot.answer_callback_query(call.id, f"🎉 অভিনন্দন! +৳ {task_reward:.2f} টাকা ওয়ালেটে যোগ হয়েছে!", show_alert=True)

    success_text = f"""✅ <b>ট্যাক্স সফলভাবে সম্পন্ন হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎯 <b>ট্যাক্স:</b> {task_title}
💰 <b>রিওয়ার্ড:</b> <b>+ ৳ {task_reward:.2f} টাকা</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>টাকাটি সরাসরি আপনার মিনি অ্যাপ ও বটের ওয়ালেটে যুক্ত হয়েছে!</i>"""

    bot.send_message(call.message.chat.id, success_text)

# =================================================================
# ৬. ব্যালেন্স বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["💰 ব্যালেন্স 💎", "ব্যালেন্স", "balance", "/balance"]))
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
# ৭. রেফার বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["👥 রেফার 🎁", "রেফার", "refer", "/refer"]))
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
# ৮. সাপোর্ট বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["🛠️ সাপোর্ট 💬", "সাপোর্ট", "support", "/support"]))
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
# ৯. ব্যাক বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["🔙 ব্যাক", "ব্যাক", "back", "/back", "মেন্যু"]))
def back_to_main_menu(message):
    bot.send_message(message.chat.id, "🏠 <b>মূল মেন্যুতে ফিরে আসা হয়েছে:</b>", reply_markup=get_main_keyboard())

# =================================================================
# ❓ স্মার্ট ফলব্যাক হ্যান্ডলার (Catch-all for invalid commands/text)
# =================================================================
@bot.message_handler(func=lambda msg: True)
def fallback_handler(message):
    fallback_text = f"""🤖 <b>দুঃখিত! আমি আপনার মেসেজটি বুঝতে পারিনি।</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ আপনি যা করতে পারেন:
• বট রিস্টার্ট করতে <b>/start</b> কমান্ড দিন।
• নিচে দেওয়া মেন্যু কিবোর্ড বাটনগুলো ব্যবহার করুন।
• কোনো সমস্যায় পড়লে <b>সাপোর্ট</b> বাটনে যোগাযোগ করুন।</blockquote>

👇 <i>নিচের কিবোর্ড থেকে আপনার পছন্দের অপশন বেছে নিন:</i>"""
    bot.send_message(message.chat.id, fallback_text, reply_markup=get_main_keyboard())

# =================================================================
# 🚀 মেইন রানার
# =================================================================
if __name__ == "__main__":
    print("🌐 Keep-Alive Server চালু হচ্ছে...")
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("👑 MH Earning Bot Ultra Admin Engine সফলভাবে চালু হয়েছে...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
