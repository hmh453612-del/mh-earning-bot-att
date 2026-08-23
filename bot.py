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

# টেলিগ্রাম বট ইঞ্জিন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

# =================================================================
# 🌐 Render Keep-Alive Web Server
# =================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "👑 MH Earning Bot Ultra Master Engine is Running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# =================================================================
# 🔥 Firebase Engine & System Settings
# =================================================================
def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def get_system_settings():
    default_settings = {
        "ad_reward": 10.00,
        "refer_reward": 50.00,
        "maintenance_mode": False
    }
    try:
        url = f"{FIREBASE_DB_URL}/settings.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return {**default_settings, **res.json()}
    except Exception as e:
        print(f"Settings Fetch Error: {e}")
    return default_settings

def update_system_settings(data):
    try:
        url = f"{FIREBASE_DB_URL}/settings.json"
        requests.patch(url, json=data, timeout=5)
        return True
    except Exception as e:
        print(f"Settings Update Error: {e}")
        return False

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
    try:
        url = f"{FIREBASE_DB_URL}/users.json"
        res = requests.get(url, timeout=8)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase All Users Error: {e}")
    return {}

def get_all_tasks_from_db():
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

def get_all_withdrawals_from_db():
    """মিনি অ্যাপের transactions ডাটাবেজ থেকে রিকোয়েস্ট পড়া"""
    try:
        url = f"{FIREBASE_DB_URL}/transactions.json"
        res = requests.get(url, timeout=6)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Transactions Fetch Error: {e}")
    return {}

def update_withdrawal_in_db(tx_id, data):
    try:
        url = f"{FIREBASE_DB_URL}/transactions/{tx_id}.json"
        requests.patch(url, json=data, timeout=5)
        return True
    except Exception as e:
        print(f"Firebase Transaction Update Error: {e}")
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

# =================================================================
# 🛡️ সিকিউরিটি ও রক্ষণাবেক্ষণ ফিল্টার
# =================================================================
def check_user_access(user_id):
    if is_admin(user_id):
        return True, ""
    
    settings = get_system_settings()
    if settings.get("maintenance_mode", False):
        return False, "🛠️ <b>বটে সিস্টেম রক্ষণাবেক্ষণ চলছে!</b>\n\nকিছুক্ষণের জন্য সেবা স্থগিত আছে। কাজ শেষ হলে স্বয়ংক্রিয়ভাবে চালু হবে।"

    user_data = get_user_from_db(str(user_id))
    if user_data and user_data.get("isBanned", False):
        return False, "🚫 <b>আপনার অ্যাকাউন্টটি স্থগিত (Banned) করা হয়েছে!</b>\n\nসহায়তার জন্য অফিসিয়াল সাপোর্টে কথা বলুন।"

    return True, ""

# =================================================================
# 👥 রেফারেল ও মেম্বারশিপ ইঞ্জিন (মিনি অ্যাপের সাথে ১০০% সিঙ্ক)
# =================================================================
def handle_referral_and_user_creation(user_id, full_name, username, referrer_id):
    user_id_str = str(user_id)
    user_data = get_user_from_db(user_id_str)
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    formatted_time = now.strftime("%I:%M %p | %d/%m/%Y")
    settings = get_system_settings()
    refer_reward = float(settings.get("refer_reward", 50.00))

    if not user_data:
        new_user = {
            "telegramId": user_id_str,
            "name": full_name,
            "username": f"@{username}" if username else "N/A",
            "balance": 0.00,
            "withdrawn": 0.00,
            "totalEarned": 0.00,
            "lifetimeEarnings": 0.00,
            "lifetimeBalance": 0.00,
            "totalIncome": 0.00,
            "referrals": 0,
            "adsWatched": 0,
            "lastAdDate": today_date,
            "completedTasksCount": 0,
            "rejectedCount": 0,
            "isBanned": False,
            "completedTasksList": {},
            "joinedAt": int(now.timestamp() * 1000),
            "referredBy": referrer_id if (referrer_id and referrer_id != user_id_str) else None
        }
        update_user_in_db(user_id_str, new_user)

        if referrer_id and referrer_id != user_id_str and referrer_id != "guest_12345678":
            referrer_data = get_user_from_db(referrer_id)
            if referrer_data:
                cur_bal = float(referrer_data.get("balance", 0.0))
                cur_tot = float(referrer_data.get("totalEarned", referrer_data.get("lifetimeEarnings", cur_bal)))
                cur_ref = int(referrer_data.get("referrals", 0))

                new_balance = cur_bal + refer_reward
                new_total = cur_tot + refer_reward
                new_ref_count = cur_ref + 1

                update_user_in_db(referrer_id, {
                    "balance": new_balance,
                    "totalEarned": new_total,
                    "lifetimeEarnings": new_total,
                    "lifetimeBalance": new_total,
                    "totalIncome": new_total,
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

                    notify_kb = types.InlineKeyboardMarkup(row_width=1)
                    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={referrer_id}"
                    btn_wallet = types.InlineKeyboardButton(text="💳 ওয়ালেট ব্যালেন্স দেখুন", web_app=types.WebAppInfo(url=webapp_url))
                    
                    share_link = f"https://t.me/{BOT_USERNAME}?start={referrer_id}"
                    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম করুন!\n👉 জয়েন লিংক: {share_link}"
                    share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_link)}&text={urllib.parse.quote(share_text)}"
                    btn_more_ref = types.InlineKeyboardButton(text="📢 বন্ধুদের শেয়ার করুন", url=share_url)

                    notify_kb.add(btn_wallet, btn_more_ref)

                    notify_text = f"""🎉 <b>অভিনন্দন! সফল রেফারেল!</b> 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👤 <b>নতুন সদস্য:</b> {full_name}
🆔 <b>আইডি:</b> <code>{user_id_str}</code>
⏰ <b>সময়:</b> {formatted_time}

💎 <b>রেফার বোনাস:</b> <b>+ ৳ {refer_reward:.2f} টাকা</b>
👥 <b>সর্বমোট রেফার:</b> <b>{new_ref_count} জন</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>বোনাসটি সরাসরি আপনার মূল ওয়ালেট ও মিনি অ্যাপে যুক্ত হয়েছে!</i>"""

                    bot.send_message(int(referrer_id), notify_text, reply_markup=notify_kb, disable_web_page_preview=True)
                except Exception as err:
                    print(f"Referral Notification Error: {err}")
    else:
        update_user_in_db(user_id_str, {
            "name": full_name,
            "username": f"@{username}" if username else "N/A"
        })

# =================================================================
# ⌨️ ইউজার মেন্যু কিবোর্ডসমূহ
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
# 👑 আল্ট্রা প্রফেশনাল অ্যাডমিন প্যানেল ইঞ্জিন
# =================================================================
def get_admin_dashboard_markup():
    settings = get_system_settings()
    m_status = "🔴 বন্ধ করুন" if settings.get("maintenance_mode", False) else "🟢 চালু করুন"
    
    # পেন্ডিং উইথড্র গণনা
    all_wd = get_all_withdrawals_from_db()
    pending_count = 0
    if all_wd:
        for item in all_wd.values():
            if isinstance(item, dict) and item.get("status", "Pending").lower() == "pending":
                pending_count += 1

    wd_badge = f" ({pending_count} টি)" if pending_count > 0 else " (০)"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📊 লাইভ অ্যানালিটিক্স ও ডাটাবেজ সামারি", callback_data="adm_stats"),
        types.InlineKeyboardButton(f"💸 পেন্ডিং উইথড্র রিকোয়েস্ট{wd_badge}", callback_data="adm_withdrawals"),
        types.InlineKeyboardButton("📢 অল ইউজার স্মার্ট ব্রডকাস্ট", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("➕ নতুন সোশ্যাল ট্যাক্স তৈরি করুন", callback_data="adm_add_task"),
        types.InlineKeyboardButton("📋 ট্যাক্স তালিকা ও ডিলিট প্যানেল", callback_data="adm_view_tasks"),
        types.InlineKeyboardButton("🔍 ইউজার সার্চ ও অ্যাকশন (ব্যালেন্স/ব্যান)", callback_data="adm_user_ctrl"),
        types.InlineKeyboardButton("🎁 অল ইউজার স্পেশাল বোনাস (Mass Bonus)", callback_data="adm_mass_bonus"),
        types.InlineKeyboardButton("⚙️ এড ও রেফার বোনাস রেট পরিবর্তন", callback_data="adm_settings"),
        types.InlineKeyboardButton(f"🛠️ রক্ষণাবেক্ষণ মোড ({m_status})", callback_data="adm_toggle_maint"),
        types.InlineKeyboardButton("❌ অ্যাডমিন প্যানেল বন্ধ করুন", callback_data="adm_close")
    )
    return markup

def show_admin_dashboard(chat_id, message_id=None):
    """কোনো বাধা ছাড়া নির্ভরযোগ্যভাবে অ্যাডমিন প্যানেল ওপেন করার ইঞ্জিন"""
    settings = get_system_settings()
    m_state = "সক্রিয় 🔴" if settings.get("maintenance_mode", False) else "স্বাভাবিক 🟢"

    admin_panel_text = f"""👑 <b>MH EARNING ULTRA MASTER ADMIN PANEL</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>স্বাগতম অ্যাডমিন! সিস্টেম পুরোপুরি লাইভ ও আপনার নিয়ন্ত্রণে রয়েছে।

👤 <b>অ্যাডমিন আইডি:</b> <code>{ADMIN_ID}</code>
🟢 <b>সার্ভার স্ট্যাটাস:</b> অনলাইন (Active 24/7)
🛠️ <b>রক্ষণাবেক্ষণ মোড:</b> <b>{m_state}</b>
🎬 <b>ভিডিও এড রিওয়ার্ড:</b> ৳ {settings.get('ad_reward', 10.0):.2f} টাকা
🎁 <b>রেফার বোনাস:</b> ৳ {settings.get('refer_reward', 50.0):.2f} টাকা</blockquote>

👇 <i>যেকোনো অপশন পরিবর্তন বা পরিচালনা করতে নিচের বাটন বেছে নিন:</i>"""

    if message_id:
        try:
            bot.edit_message_text(admin_panel_text, chat_id, message_id, reply_markup=get_admin_dashboard_markup())
            return
        except Exception:
            pass
    bot.send_message(chat_id, admin_panel_text, reply_markup=get_admin_dashboard_markup())

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        unauth_msg = f"""🚫 <b>অ্যাক্সেস ডিনাইড (Access Denied)!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚠️ এই কমান্ডটি শুধুমাত্র সিস্টেম অ্যাডমিনিস্ট্রেটরের জন্য সংরক্ষিত।</blockquote>

👉 বটের অন্যান্য সুবিধা পেতে নিচের মেন্যু ব্যবহার করুন বা /start লিখুন।"""
        bot.send_message(message.chat.id, unauth_msg, reply_markup=get_main_keyboard())
        return

    show_admin_dashboard(message.chat.id)

# =================================================================
# ⚙️ অ্যাডমিন ডিসপ্যাচার ও উইথড্রল প্রসেসিং ইঞ্জিন
# =================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 আপনার অনুমতি নেই!", show_alert=True)
        return

    action = call.data

    # ১. লাইভ পরিসংখ্যান
    if action == "adm_stats":
        bot.answer_callback_query(call.id, "📊 ডাটা লোড হচ্ছে...")
        users = get_all_users_from_db()
        tasks = get_all_tasks_from_db()
        all_wd = get_all_withdrawals_from_db()
        settings = get_system_settings()

        total_users = len(users) if users else 0
        total_balance = sum(float(u.get("balance", 0.0)) for u in users.values()) if users else 0.0
        total_referrals = sum(int(u.get("referrals", 0)) for u in users.values()) if users else 0
        banned_users = sum(1 for u in users.values() if u.get("isBanned", False)) if users else 0
        total_tasks = len(tasks) if tasks else 0
        
        pending_wd = 0
        paid_wd_amount = 0.0
        if all_wd:
            for w in all_wd.values():
                if isinstance(w, dict):
                    st = str(w.get("status", "")).lower()
                    if st == "pending":
                        pending_wd += 1
                    elif st in ["approved", "paid"]:
                        paid_wd_amount += float(w.get("amount", 0.0))

        stats_text = f"""📊 <b>লাইভ ডাটাবেজ অ্যানালিটিক্স</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👥 <b>সর্বমোট নিবন্ধিত মেম্বার:</b> <b>{total_users:,}</b> জন
💵 <b>ইউজারদের মূল ব্যালেন্স:</b> <b>৳ {total_balance:,.2f}</b> টাকা
💸 <b>মোট সফল পেইড পেমেন্ট:</b> <b>৳ {paid_wd_amount:,.2f}</b> টাকা
⏳ <b>পেন্ডিং উইথড্র রিকোয়েস্ট:</b> <b>{pending_wd}</b> টি
🎁 <b>সর্বমোট সফল রেফারেল:</b> <b>{total_referrals:,}</b> টি
🚫 <b>স্থগিত (Banned) ইউজার:</b> <b>{banned_users}</b> জন
📋 <b>সক্রিয় সোশ্যাল ট্যাক্স:</b> <b>{total_tasks}</b> টি</blockquote>

🔄 <i>ফায়ারবেজ রিয়েল-টাইম সিঙ্ক সক্রিয় রয়েছে।</i>"""
        
        back_kb = types.InlineKeyboardMarkup(row_width=1)
        back_kb.add(types.InlineKeyboardButton("🔙 ফিরে যান", callback_data="adm_back_menu"))
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, reply_markup=back_kb)

    # ২. উইথড্র রিকোয়েস্ট তালিকা
    elif action == "adm_withdrawals":
        bot.answer_callback_query(call.id, "💸 উইথড্রল লোড হচ্ছে...")
        all_wd = get_all_withdrawals_from_db()
        pending_list = []

        if all_wd:
            for w_id, w_data in all_wd.items():
                if isinstance(w_data, dict) and str(w_data.get("status", "pending")).lower() == "pending":
                    pending_list.append((w_id, w_data))

        if not pending_list:
            back_kb = types.InlineKeyboardMarkup(row_width=1)
            back_kb.add(types.InlineKeyboardButton("🔙 অ্যাডমিন মেন্যু", callback_data="adm_back_menu"))
            bot.edit_message_text("🎉 <b>বর্তমানে কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই!</b>\nসকল পেমেন্ট ক্লিয়ার আছে।", call.message.chat.id, call.message.message_id, reply_markup=back_kb)
            return

        w_id, w_data = pending_list[0]
        display_single_withdrawal(call.message.chat.id, call.message.message_id, w_id, w_data, len(pending_list))

    # ৩. অল ইউজার ব্রডকাস্ট
    elif action == "adm_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📢 <b>স্মার্ট ব্রডকাস্ট বার্তা লিখুন:</b>\n\nআপনি যে নোটিশটি সকল ইউজারের কাছে পাঠাতে চান তা লিখুন (HTML ট্যাগ যেমন <b>bold</b>, <i>italic</i> সমর্থিত)।\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_broadcast_message)

    # ৪. নতুন ট্যাক্স তৈরি
    elif action == "adm_add_task":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📋 <b>নতুন ট্যাক্স যোগ করুন</b>\n\nধাপ ১: ট্যাক্সের নাম লিখুন (যেমন: Join Official VIP Channel):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_task_title_step)

    # ৫. ট্যাক্স ডিলিট / তালিকা
    elif action == "adm_view_tasks":
        bot.answer_callback_query(call.id)
        tasks = get_all_tasks_from_db()
        if not tasks:
            back_kb = types.InlineKeyboardMarkup(row_width=1)
            back_kb.add(types.InlineKeyboardButton("🔙 ফিরে যান", callback_data="adm_back_menu"))
            bot.edit_message_text("⚠️ ডাটাবেজে বর্তমানে কোনো ট্যাক্স সক্রিয় নেই!", call.message.chat.id, call.message.message_id, reply_markup=back_kb)
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for task_id, task in tasks.items():
            if isinstance(task, dict):
                title = task.get("title", "ট্যাক্স")
                reward = task.get("reward", 0.0)
                markup.add(types.InlineKeyboardButton(f"🗑️ ডিলিট: {title} (৳ {reward:.2f})", callback_data=f"del_task_{task_id}"))
        
        markup.add(types.InlineKeyboardButton("🔙 ফিরে যান", callback_data="adm_back_menu"))
        bot.edit_message_text("📋 <b>যেকোনো ট্যাক্স মুছে ফেলতে ট্যাপ করুন:</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ৬. ইউজার সার্চ
    elif action == "adm_user_ctrl":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🔍 <b>ইউজার সার্চ ও প্রোফাইল কন্ট্রোল</b>\n\nটার্গেট ইউজারের <b>Telegram User ID</b> লিখুন:\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_user_search)

    # ৭. অল ইউজার ম্যাস বোনাস
    elif action == "adm_mass_bonus":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🎁 <b>অল ইউজার স্পেশাল বোনাস বিতরণ</b>\n\nসকল ইউজারের ওয়ালেটে একযোগে কত টাকা পাঠাতে চান? টাকার পরিমাণ লিখুন (যেমন: 5 বা 10):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>"
        )
        bot.register_next_step_handler(msg, process_mass_bonus)

    # ৮. রিওয়ার্ড পরিবর্তন
    elif action == "adm_settings":
        bot.answer_callback_query(call.id)
        settings = get_system_settings()
        set_kb = types.InlineKeyboardMarkup(row_width=1)
        set_kb.add(
            types.InlineKeyboardButton(f"🎬 পরিবর্তন: ভিডিও এড রেট (৳ {settings.get('ad_reward', 10.0):.2f})", callback_data="set_ad_reward"),
            types.InlineKeyboardButton(f"🎁 পরিবর্তন: রেফারেল বোনাস (৳ {settings.get('refer_reward', 50.0):.2f})", callback_data="set_refer_reward"),
            types.InlineKeyboardButton("🔙 অ্যাডমিন মেন্যু", callback_data="adm_back_menu")
        )
        bot.edit_message_text("⚙️ <b>সিস্টেম রিওয়ার্ড সেটিংস</b>\n\nযে রিওয়ার্ডটি আপডেট করতে চান তা বেছে নিন:", call.message.chat.id, call.message.message_id, reply_markup=set_kb)

    # ৯. মেইনটেন্যান্স মোড টগল
    elif action == "adm_toggle_maint":
        settings = get_system_settings()
        new_state = not settings.get("maintenance_mode", False)
        update_system_settings({"maintenance_mode": new_state})
        
        status_text = "চালু করা হয়েছে (Active) 🔴" if new_state else "বন্ধ করা হয়েছে (Online) 🟢"
        bot.answer_callback_query(call.id, f"রক্ষণাবেক্ষণ মোড {status_text}", show_alert=True)
        show_admin_dashboard(call.message.chat.id, call.message.message_id)

    # ১০. ব্যাক মেন্যু
    elif action == "adm_back_menu":
        bot.answer_callback_query(call.id)
        show_admin_dashboard(call.message.chat.id, call.message.message_id)

    # ১১. প্যানেল বন্ধ
    elif action == "adm_close":
        bot.answer_callback_query(call.id, "প্যানেল বন্ধ করা হয়েছে")
        bot.delete_message(call.message.chat.id, call.message.message_id)

# =================================================================
# 💸 উইথড্রল ভিউ, অ্যাপ্রুভ ও রিজেক্ট কন্ট্রোল
# =================================================================
def display_single_withdrawal(chat_id, message_id, w_id, w_data, total_pending):
    user_id = str(w_data.get("userId", "N/A"))
    user_name = w_data.get("userName", "N/A")
    method = w_data.get("method", "বিকাশ/নগদ")
    number = w_data.get("number", w_data.get("account", "N/A"))
    amount = float(w_data.get("amount", 0.0))
    time_str = w_data.get("date", datetime.now().strftime("%I:%M %p | %d/%m/%Y"))

    wd_text = f"""💸 <b>পেন্ডিং উইথড্র রিকোয়েস্ট ({total_pending} টির মধ্যে ১টি)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👤 <b>সদস্য:</b> {user_name}
🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>
💳 <b>পেমেন্ট মেথড:</b> <b>{method}</b>
📱 <b>একাউন্ট নাম্বার:</b> <code>{number}</code>
💰 <b>উইথড্রল পরিমাণ:</b> <b>৳ {amount:.2f} টাকা</b>
⏰ <b>আবেদনের সময়:</b> {time_str}</blockquote>

👇 <i>টাকা পাঠিয়ে থাকলে অ্যাপ্রুভ করুন অথবা রিজেক্ট করে ব্যালেন্স রিফান্ড দিন:</i>"""

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✅ পেমেন্ট সম্পন্ন হয়েছে (Approve)", callback_data=f"wdapp_{w_id}"),
        types.InlineKeyboardButton("❌ বাতিল ও টাকা রিফান্ড দিন (Reject)", callback_data=f"wdrej_{w_id}"),
        types.InlineKeyboardButton("🔙 অ্যাডমিন মেন্যু", callback_data="adm_back_menu")
    )

    bot.edit_message_text(wd_text, chat_id, message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wdapp_"))
def approve_withdrawal(call):
    if not is_admin(call.from_user.id):
        return
    w_id = call.data.replace("wdapp_", "")
    all_wd = get_all_withdrawals_from_db()
    w_data = all_wd.get(w_id, {})

    if not w_data:
        bot.answer_callback_query(call.id, "❌ উইথড্র রেকর্ড পাওয়া যায়নি!", show_alert=True)
        return

    update_withdrawal_in_db(w_id, {"status": "Approved", "processedAt": int(time.time() * 1000)})
    bot.answer_callback_query(call.id, "✅ পেমেন্ট সফলভাবে অনুমোদিত হয়েছে!", show_alert=True)

    u_id = w_data.get("userId")
    amt = float(w_data.get("amount", 0.0))
    method = w_data.get("method", "Bkash/Nagad")
    num = w_data.get("number", w_data.get("account", "N/A"))

    if u_id:
        try:
            bot.send_message(
                int(u_id),
                f"""🎉 <b>অভিনন্দন! আপনার পেমেন্ট পাঠানো হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>💰 <b>টাকার পরিমাণ:</b> <b>৳ {amt:.2f} টাকা</b>
💳 <b>মেথড:</b> {method}
📱 <b>নাম্বার:</b> <code>{num}</code>
🟢 <b>স্ট্যাটাস:</b> সম্পূর্ণ পরিশোধিত (Paid)</blockquote>

⚡ <i>MH EARNING BOT-এর সাথে থাকার জন্য ধন্যবাদ!</i>"""
            )
        except Exception:
            pass

    # উইথড্রল তালিকা রিফ্রেশ
    admin_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, data="adm_withdrawals", message=call.message, chat_instance=""))

@bot.callback_query_handler(func=lambda call: call.data.startswith("wdrej_"))
def reject_withdrawal(call):
    if not is_admin(call.from_user.id):
        return
    w_id = call.data.replace("wdrej_", "")
    all_wd = get_all_withdrawals_from_db()
    w_data = all_wd.get(w_id, {})

    if not w_data:
        bot.answer_callback_query(call.id, "❌ উইথড্র রেকর্ড পাওয়া যায়নি!", show_alert=True)
        return

    u_id = str(w_data.get("userId"))
    amt = float(w_data.get("amount", 0.0))

    u_data = get_user_from_db(u_id) or {}
    cur_bal = float(u_data.get("balance", 0.0))
    cur_tot = float(u_data.get("totalEarned", u_data.get("lifetimeEarnings", cur_bal)))
    rej_cnt = int(u_data.get("rejectedCount", 0)) + 1
    new_bal = cur_bal + amt

    update_user_in_db(u_id, {
        "balance": new_bal,
        "totalEarned": cur_tot,
        "lifetimeEarnings": cur_tot,
        "rejectedCount": rej_cnt
    })
    update_withdrawal_in_db(w_id, {"status": "Rejected", "processedAt": int(time.time() * 1000)})
    
    bot.answer_callback_query(call.id, "❌ উইথড্র বাতিল এবং ব্যালেন্স রিফান্ড করা হয়েছে!", show_alert=True)

    if u_id:
        try:
            bot.send_message(
                int(u_id),
                f"""⚠️ <b>উইথড্র রিকোয়েস্ট বাতিল ও রিফান্ড নোটিশ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>❌ তথ্যের অমিলের কারণে আপনার <b>৳ {amt:.2f} টাকার</b> উইথড্রল বাতিল করা হয়েছে।
💵 টাকাটি আপনার মূল ওয়ালেটে পুনরায় যোগ করা হয়েছে।
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_bal:.2f} টাকা</b></blockquote>

💬 <i>কোনো সমস্যা থাকলে অ্যাডমিন সাপোর্টে কথা বলুন।</i>"""
            )
        except Exception:
            pass

    admin_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, data="adm_withdrawals", message=call.message, chat_instance=""))

# =================================================================
# 🔍 ইউজার প্রোফাইল ও ব্যালেন্স/লাইফটাইম কন্ট্রোল
# =================================================================
def render_user_profile(user_id_str, chat_id, message_id=None):
    u_data = get_user_from_db(user_id_str)
    if not u_data:
        text = f"❌ আইডি: <code>{user_id_str}</code> দিয়ে কোনো ইউজার পাওয়া যায়নি!"
        if message_id:
            bot.edit_message_text(text, chat_id, message_id)
        else:
            bot.send_message(chat_id, text)
            show_admin_dashboard(chat_id)
        return

    name = u_data.get("name", "N/A")
    username = u_data.get("username", "N/A")
    balance = float(u_data.get("balance", 0.0))
    total_earned = float(u_data.get("totalEarned", u_data.get("lifetimeEarnings", balance)))
    referrals = int(u_data.get("referrals", 0))
    ads_watched = int(u_data.get("adsWatched", 0))
    tasks_done = int(u_data.get("completedTasksCount", 0))
    is_banned = u_data.get("isBanned", False)
    ban_badge = "🚫 সাময়িকভাবে স্থগিত (BANNED)" if is_banned else "🟢 নিয়মিত ও সক্রিয় (ACTIVE)"

    profile_text = f"""👤 <b>ইউজার বিস্তারিত প্রোফাইল</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🆔 <b>ইউজার আইডি:</b> <code>{user_id_str}</code>
🏷️ <b>নাম:</b> {name} ({username})
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {balance:.2f}</b> টাকা
📈 <b>লাইফটাইম আর্নিং:</b> <b>৳ {total_earned:.2f}</b> টাকা
👥 <b>সর্বমোট রেফার:</b> <b>{referrals}</b> জন
🎬 <b>মোট এড দর্শন:</b> <b>{ads_watched}</b> বার
✅ <b>ট্যাক্স সম্পন্ন:</b> <b>{tasks_done}</b> টি
🛡️ <b>অ্যাকাউন্ট স্ট্যাটাস:</b> {ban_badge}</blockquote>

👇 <i>এই ইউজারের একাউন্টে প্রয়োজনীয় অ্যাকশন নিন:</i>"""

    act_kb = types.InlineKeyboardMarkup(row_width=1)
    act_kb.add(
        types.InlineKeyboardButton("➕ ব্যালেন্স ও লাইফটাইম যোগ করুন", callback_data=f"uact_add_{user_id_str}"),
        types.InlineKeyboardButton("➖ ব্যালেন্স কর্তন করুন (- টাকা)", callback_data=f"uact_cut_{user_id_str}"),
        types.InlineKeyboardButton("🚫 ব্যান/আনব্যান টগল করুন", callback_data=f"uact_ban_{user_id_str}"),
        types.InlineKeyboardButton("✉️ সরাসরি মেসেজ পাঠান", callback_data=f"uact_msg_{user_id_str}"),
        types.InlineKeyboardButton("🔙 অ্যাডমিন মেন্যুতে ফিরে যান", callback_data="adm_back_menu")
    )

    if message_id:
        bot.edit_message_text(profile_text, chat_id, message_id, reply_markup=act_kb)
    else:
        bot.send_message(chat_id, profile_text, reply_markup=act_kb)

def process_user_search(message):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    target_uid = message.text.strip()
    render_user_profile(target_uid, message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("uact_"))
def user_action_callback(call):
    if not is_admin(call.from_user.id):
        return
    
    parts = call.data.split("_")
    action_type = parts[1]
    target_uid = parts[2]

    if action_type == "add":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"➕ <b>আইডি {target_uid} এর একাউন্টে কত টাকা যোগ করবেন?</b>\nটাকার পরিমাণ লিখুন (যেমন: 50):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
        bot.register_next_step_handler(msg, process_add_balance_step, target_uid)

    elif action_type == "cut":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"➖ <b>আইডি {target_uid} এর একাউন্ট থেকে কত টাকা কর্তন করবেন?</b>\nটাকার পরিমাণ লিখুন (যেমন: 20):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
        bot.register_next_step_handler(msg, process_cut_balance_step, target_uid)

    elif action_type == "ban":
        u_data = get_user_from_db(target_uid) or {}
        new_ban = not u_data.get("isBanned", False)
        update_user_in_db(target_uid, {"isBanned": new_ban})
        res_text = "ব্যান করা হয়েছে 🚫" if new_ban else "আনব্যান করা হয়েছে 🟢"
        bot.answer_callback_query(call.id, f"ইউজারকে {res_text}", show_alert=True)
        render_user_profile(target_uid, call.message.chat.id, call.message.message_id)

    elif action_type == "msg":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"✉️ <b>আইডি {target_uid} এর কাছে যে বার্তা পাঠাবেন তা লিখুন:</b>\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
        bot.register_next_step_handler(msg, process_send_user_dm, target_uid)

def process_add_balance_step(message, target_uid):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    try:
        amount = float(message.text.strip())
        u_data = get_user_from_db(target_uid) or {}
        cur_bal = float(u_data.get("balance", 0.0))
        cur_tot = float(u_data.get("totalEarned", u_data.get("lifetimeEarnings", cur_bal)))
        
        new_bal = cur_bal + amount
        new_tot = cur_tot + amount

        update_user_in_db(target_uid, {
            "balance": new_bal,
            "totalEarned": new_tot,
            "lifetimeEarnings": new_tot,
            "lifetimeBalance": new_tot,
            "totalIncome": new_tot
        })

        bot.send_message(
            message.chat.id,
            f"✅ সফলভাবে <b>৳ {amount:.2f}</b> টাকা যোগ হয়েছে!\n💵 বর্তমান ব্যালেন্স: <b>৳ {new_bal:.2f}</b> টাকা\n📈 লাইফটাইম আর্নিং: <b>৳ {new_tot:.2f}</b> টাকা"
        )
        try:
            bot.send_message(
                int(target_uid),
                f"🎉 <b>অ্যাডমিন ক্রেডিট বোনাস:</b>\nআপনার ওয়ালেটে <b>+ ৳ {amount:.2f} টাকা</b> যুক্ত করা হয়েছে!\n💵 বর্তমান ব্যালেন্স: <b>৳ {new_bal:.2f} টাকা</b>"
            )
        except Exception:
            pass
        show_admin_dashboard(message.chat.id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা লিখুন।")
        show_admin_dashboard(message.chat.id)

def process_cut_balance_step(message, target_uid):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    try:
        amount = float(message.text.strip())
        u_data = get_user_from_db(target_uid) or {}
        cur_bal = float(u_data.get("balance", 0.0))
        new_bal = max(0.0, cur_bal - amount)
        update_user_in_db(target_uid, {"balance": new_bal})

        bot.send_message(message.chat.id, f"✅ সফলভাবে <b>৳ {amount:.2f}</b> টাকা কর্তন করা হয়েছে!\n💵 বর্তমান ব্যালেন্স: <b>৳ {new_bal:.2f}</b> টাকা")
        try:
            bot.send_message(int(target_uid), f"⚠️ <b>ওয়ালেট নোটিশ:</b>\nআপনার ওয়ালেট থেকে <b>৳ {amount:.2f} টাকা</b> কর্তন করা হয়েছে।\n💵 বর্তমান ব্যালেন্স: <b>৳ {new_bal:.2f} টাকা</b>")
        except Exception:
            pass
        show_admin_dashboard(message.chat.id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা গ্রহণযোগ্য।")
        show_admin_dashboard(message.chat.id)

def process_send_user_dm(message, target_uid):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    user_msg = message.text
    try:
        bot.send_message(
            int(target_uid),
            f"""📩 <b>এডমিনের পক্ষ থেকে অফিসিয়াল বার্তা</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>{user_msg}</blockquote>

💬 <i>যেকোনো প্রয়োজনে সাপোর্ট সেন্টারে যোগাযোগ করুন।</i>"""
        )
        bot.send_message(message.chat.id, f"✅ ইউজার <code>{target_uid}</code> এর কাছে বার্তা সফলভাবে পৌঁছেছে!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ বার্তা পাঠানো ব্যর্থ হয়েছে: {e}")
    show_admin_dashboard(message.chat.id)

# =================================================================
# 📢 ব্রডকাস্ট ও ম্যাস বোনাস বিতরণ
# =================================================================
def process_broadcast_message(message):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return

    broadcast_content = message.text
    users = get_all_users_from_db()
    if not users:
        bot.send_message(message.chat.id, "⚠️ ডাটাবেজে কোনো ইউজার নেই!")
        show_admin_dashboard(message.chat.id)
        return

    bot.send_message(message.chat.id, "⏳ <b>সবার কাছে ব্রডকাস্ট পাঠানো শুরু হয়েছে...</b>")

    def run_broadcast():
        sent = 0
        failed = 0
        for uid in users.keys():
            try:
                bot.send_message(int(uid), broadcast_content, disable_web_page_preview=True)
                sent += 1
                time.sleep(0.05)
            except Exception:
                failed += 1

        summary = f"""🎉 <b>ব্রডকাস্ট সম্পূর্ণ হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>✅ <b>সফলভাবে প্রেরিত:</b> {sent} জন
❌ <b>ব্যর্থ হয়েছে:</b> {failed} জন
👥 <b>মোট ইউজার টার্গেট:</b> {len(users)} জন</blockquote>"""
        bot.send_message(ADMIN_ID, summary)
        show_admin_dashboard(ADMIN_ID)

    threading.Thread(target=run_broadcast).start()

def process_mass_bonus(message):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    try:
        bonus_amt = float(message.text.strip())
        users = get_all_users_from_db()
        if not users:
            bot.send_message(message.chat.id, "⚠️ কোনো ইউজার পাওয়া যায়নি!")
            show_admin_dashboard(message.chat.id)
            return

        bot.send_message(message.chat.id, f"⏳ <b>সকল ইউজারের ওয়ালেটে ৳ {bonus_amt:.2f} টাকা যোগ করা হচ্ছে...</b>")

        def run_mass_bonus():
            count = 0
            for uid, data in users.items():
                try:
                    c_bal = float(data.get("balance", 0.0))
                    c_tot = float(data.get("totalEarned", data.get("lifetimeEarnings", c_bal)))
                    
                    update_user_in_db(uid, {
                        "balance": c_bal + bonus_amt,
                        "totalEarned": c_tot + bonus_amt,
                        "lifetimeEarnings": c_tot + bonus_amt,
                        "lifetimeBalance": c_tot + bonus_amt,
                        "totalIncome": c_tot + bonus_amt
                    })
                    try:
                        bot.send_message(int(uid), f"🎁 <b>ঈদ / স্পেশাল মেগা বোনাস!</b>\n\nএডমিনের পক্ষ থেকে আপনার ওয়ালেটে <b>+ ৳ {bonus_amt:.2f} টাকা</b> যোগ হয়েছে!")
                    except Exception:
                        pass
                    count += 1
                    time.sleep(0.05)
                except Exception:
                    pass

            bot.send_message(ADMIN_ID, f"🎉 <b>সফল!</b> মোট <b>{count}</b> জন ইউজারের ওয়ালেটে <b>৳ {bonus_amt:.2f} টাকা</b> করে যুক্ত করা হয়েছে!")
            show_admin_dashboard(ADMIN_ID)

        threading.Thread(target=run_mass_bonus).start()
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা গ্রহণযোগ্য।")
        show_admin_dashboard(message.chat.id)

# ডাইনামিক রিওয়ার্ড পরিবর্তন
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def settings_callback(call):
    if not is_admin(call.from_user.id):
        return
    
    if call.data == "set_ad_reward":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🎬 <b>নতুন ভিডিও এড রিওয়ার্ডের পরিমাণ লিখুন (যেমন: 10 বা 15):</b>\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
        bot.register_next_step_handler(msg, lambda m: update_reward_field(m, "ad_reward", "ভিডিও এড"))

    elif call.data == "set_refer_reward":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🎁 <b>নতুন রেফারেল বোনাসের পরিমাণ লিখুন (যেমন: 50 বা 60):</b>\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
        bot.register_next_step_handler(msg, lambda m: update_reward_field(m, "refer_reward", "রেফারেল"))

def update_reward_field(message, field_key, field_name_bn):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    try:
        val = float(message.text.strip())
        update_system_settings({field_key: val})
        bot.send_message(message.chat.id, f"✅ <b>{field_name_bn} রিওয়ার্ড সফলভাবে পরিবর্তন হয়ে ৳ {val:.2f} টাকা হয়েছে!</b>")
        show_admin_dashboard(message.chat.id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা লিখুন।")
        show_admin_dashboard(message.chat.id)

# সোশ্যাল ট্যাক্স স্টেপ হ্যান্ডলার
def process_task_title_step(message):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    title = message.text.strip()
    msg = bot.send_message(message.chat.id, f"🎯 <b>ট্যাক্স:</b> {title}\n\nধাপ ২: এই ট্যাক্সের রিওয়ার্ডের পরিমাণ লিখুন (যেমন: 5 বা 10):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
    bot.register_next_step_handler(msg, process_task_reward_step, title)

def process_task_reward_step(message, title):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
        return
    try:
        reward = float(message.text.strip())
        msg = bot.send_message(message.chat.id, f"🎯 <b>ট্যাক্স:</b> {title}\n💰 <b>রিওয়ার্ড:</b> ৳ {reward:.2f}\n\nধাপ ৩: চ্যানেল/গ্রুপ বা ওয়েবসাইটের লিংক দিন (যেমন: https://t.me/yourchannel):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
        bot.register_next_step_handler(msg, process_task_link_step, title, reward)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা দিন।")
        show_admin_dashboard(message.chat.id)

def process_task_link_step(message, title, reward):
    if message.text and message.text.strip() == "/cancel":
        show_admin_dashboard(message.chat.id)
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
        bot.send_message(message.chat.id, f"🎉 <b>নতুন ট্যাক্স সফলভাবে যোগ হয়েছে!</b>\n\n📋 টাইটেল: {title}\n💎 রিওয়ার্ড: ৳ {reward:.2f} টাকা\n🔗 লিংক: {link}")
    else:
        bot.send_message(message.chat.id, "❌ ট্যাক্স ডাটাবেজে সেভ করতে সমস্যা হয়েছে।")
    show_admin_dashboard(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_task_"))
def execute_delete_task(call):
    if not is_admin(call.from_user.id):
        return
    task_id = call.data.replace("del_task_", "")
    if delete_task_from_db(task_id):
        bot.answer_callback_query(call.id, "✅ ট্যাক্স মুছে ফেলা হয়েছে!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ ট্যাক্স মুছতে সমস্যা হয়েছে!", show_alert=True)
    
    show_admin_dashboard(call.message.chat.id, call.message.message_id)

# =================================================================
# ১. /start কমান্ড হ্যান্ডলার
# =================================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    allowed, alert_msg = check_user_access(message.from_user.id)
    if not allowed:
        bot.send_message(message.chat.id, alert_msg)
        return

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
    settings = get_system_settings()
    refer_reward = float(settings.get("refer_reward", 50.00))

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
    btn_webapp = types.InlineKeyboardButton(text="🚀 ওপেন আর্নিং অ্যাপ 📱", web_app=types.WebAppInfo(url=webapp_url))
    
    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে প্রতিদিন টাকা ইনকাম করুন!\n\n🚀 প্রতি রেফারে পাবেন ৫০ টাকা!\n\n👉 জয়েন লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"
    btn_share = types.InlineKeyboardButton(text="📢 বন্ধুদের শেয়ার করুন 🎁", url=share_url)

    inline_kb.add(btn_webapp, btn_share)

    welcome_text = f"""👑 <b>MH EARNING BOT PREMIER</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>✨ <b>ঘরে বসে সহজে আয় করার সবচেয়ে বিশ্বস্ত প্ল্যাটফর্ম!</b>

✅ <b>ভিডিও বিজ্ঞাপন দেখে আনলিমিটেড ইনকাম</b>
✅ <b>সোশ্যাল ট্যাক্স সম্পূর্ণ করে বড় রিওয়ার্ড</b>
✅ <b>প্রতি রেফারে ইনস্ট্যান্ট ৳ {refer_reward:.2f} টাকা</b>
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
    allowed, alert_msg = check_user_access(message.from_user.id)
    if not allowed:
        bot.send_message(message.chat.id, alert_msg)
        return

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
    allowed, alert_msg = check_user_access(message.from_user.id)
    if not allowed:
        bot.send_message(message.chat.id, alert_msg)
        return

    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    ads_watched = int(user_data.get("adsWatched", 0))
    settings = get_system_settings()
    ad_reward = float(settings.get("ad_reward", 10.00))

    auto_ad_webapp_url = f"{MINI_APP_URL}#action=watch_ad&tgWebAppStartParam={user_id}"

    ad_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_open_ad = types.InlineKeyboardButton(text="🚀 ওপেন (ভিডিও এড দেখুন) ⚡", web_app=types.WebAppInfo(url=auto_ad_webapp_url))
    ad_kb.add(btn_open_ad)

    msg_text = f"""🎬 <b>প্রিমিয়াম ভিডিও বিজ্ঞাপন জোন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>💎 <b>বিজ্ঞাপন রিওয়ার্ড:</b> <b>৳ {ad_reward:.2f} টাকা</b> প্রতি ভিডিও!
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
    allowed, alert_msg = check_user_access(message.from_user.id)
    if not allowed:
        bot.send_message(message.chat.id, alert_msg)
        return

    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    completed_tasks_list = user_data.get("completedTasksList", {}) or {}

    all_tasks = get_all_tasks_from_db()

    if not all_tasks:
        normal_webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"
        no_task_kb = types.InlineKeyboardMarkup(row_width=1)
        no_task_kb.add(types.InlineKeyboardButton("📱 আর্নিং অ্যাপে টাস্ক দেখুন", web_app=types.WebAppInfo(url=normal_webapp_url)))
        
        bot.send_message(
            message.chat.id,
            """📋 <b>সোশ্যাল ট্যাক্স ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>বর্তমানে কোনো নতুন ট্যাক্স নেই। অ্যাপ থেকে নতুন ট্যাক্স চেক করুন!</blockquote>""",
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
            "🎉 <b>অভিনন্দন! আপনি সবগুলো ট্যাক্স সম্পূর্ণ করে ফেলেছেন!</b>\nনতুন ট্যাক্স যুক্ত হলে এখানে আবার দেখতে পাবেন।", 
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(message.chat.id, msg_text, reply_markup=task_kb, disable_web_page_preview=True)

# =================================================================
# ৫. ট্যাক্স ভেরিফাই Callback Query
# =================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_task_callback(call):
    allowed, alert_msg = check_user_access(call.from_user.id)
    if not allowed:
        bot.answer_callback_query(call.id, "🚫 আপনার অ্যাকাউন্টে অ্যাক্সেস বন্ধ রয়েছে!", show_alert=True)
        return

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
    cur_tot = float(user_data.get("totalEarned", user_data.get("lifetimeEarnings", cur_bal)))
    cur_tasks_count = int(user_data.get("completedTasksCount", 0))

    new_balance = cur_bal + task_reward
    new_total = cur_tot + task_reward
    new_tasks_count = cur_tasks_count + 1

    update_user_in_db(user_id, {
        "balance": new_balance,
        "totalEarned": new_total,
        "lifetimeEarnings": new_total,
        "lifetimeBalance": new_total,
        "totalIncome": new_total,
        "completedTasksCount": new_tasks_count,
        f"completedTasksList/{task_id}": True
    })

    bot.answer_callback_query(call.id, f"🎉 অভিনন্দন! +৳ {task_reward:.2f} টাকা যোগ হয়েছে!", show_alert=True)

    success_text = f"""✅ <b>ট্যাক্স সফলভাবে সম্পন্ন হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎯 <b>ট্যাক্স:</b> {task_title}
💰 <b>রিওয়ার্ড:</b> <b>+ ৳ {task_reward:.2f} টাকা</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

⚡ <i>টাকাটি সরাসরি আপনার মিনি অ্যাপ ও ওয়ালেটে যুক্ত হয়েছে!</i>"""

    bot.send_message(call.message.chat.id, success_text)

# =================================================================
# ৬. ব্যালেন্স বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text for w in ["💰 ব্যালেন্স 💎", "ব্যালেন্স", "balance", "/balance"]))
def balance_handler(message):
    allowed, alert_msg = check_user_access(message.from_user.id)
    if not allowed:
        bot.send_message(message.chat.id, alert_msg)
        return

    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name or "User"
    webapp_url = f"{MINI_APP_URL}#tgWebAppStartParam={user_id}"

    user_data = get_user_from_db(user_id) or {}
    balance = float(user_data.get("balance", 0.00))
    total_earned = float(user_data.get("totalEarned", user_data.get("lifetimeEarnings", balance)))
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
📈 <b>লাইফটাইম আর্নিং:</b> <b>৳ {total_earned:.2f}</b> টাকা
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
    allowed, alert_msg = check_user_access(message.from_user.id)
    if not allowed:
        bot.send_message(message.chat.id, alert_msg)
        return

    user_id = str(message.from_user.id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    settings = get_system_settings()
    refer_reward = float(settings.get("refer_reward", 50.00))

    user_data = get_user_from_db(user_id) or {}
    total_refs = int(user_data.get("referrals", 0))
    earned_from_refs = total_refs * refer_reward

    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম শুরু করুন!\n\n👉 রেফারেল লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"

    ref_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_share = types.InlineKeyboardButton(text="📢 রেফার লিংক বন্ধুদের শেয়ার 🚀", url=share_url)
    ref_kb.add(btn_share)

    msg_text = f"""👥 <b>রেফারেল ইনকাম সেন্টার</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎁 <b>প্রতি রেফারে বোনাস:</b> <b>৳ {refer_reward:.2f}</b> টাকা!
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
# ❓ স্মার্ট ফলব্যাক হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: True)
def fallback_handler(message):
    if is_admin(message.from_user.id):
        show_admin_dashboard(message.chat.id)
        return

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

    print("👑 MH Earning Bot Ultra Master Engine সফলভাবে চালু হয়েছে...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
