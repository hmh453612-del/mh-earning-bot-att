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
# ⚙️ কনফিগারেশন ও অ্যাডমিন সেটিংস (Configuration)
# =================================================================
BOT_TOKEN = "8862120350:AAGAbapwq17iwwGGuTbTjW8COWskalp2EKE"
BOT_USERNAME = "mhearningxl_bot"
MINI_APP_URL = "https://mhearningbot.blogspot.com/?m=1"
SUPPORT_USERNAME = "mh_earning_bot_admin"

# ✅ লাইভ Firebase Realtime DB URL
FIREBASE_DB_URL = "https://mh-earning-bot-all-default-rtdb.asia-southeast1.firebasedatabase.app"

# 👑 অ্যাডমিন এক্সেস আইডি
ADMIN_IDS = ["8855522653"]

AD_REWARD = 10.00
REFER_REWARD = 50.00

# টেলিগ্রাম বট ইঞ্জিন
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

# অ্যাডমিন অ্যাকশন ও স্টেট ট্র্যাকার
admin_states = {}

# =================================================================
# 🌐 Render Keep-Alive Web Server
# =================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "MH Earning Bot Ultra Pro Engine is Running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# =================================================================
# 🛡️ পারমিশন ও ফায়ারবেস ইঞ্জিন
# =================================================================
def is_admin(user_id):
    return str(user_id).strip() in ADMIN_IDS

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
        res = requests.get(url, timeout=6)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Fetch Users Error: {e}")
    return {}

def get_settings_from_db():
    try:
        url = f"{FIREBASE_DB_URL}/settings.json"
        res = requests.get(url, timeout=4)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception:
        pass
    return {}

def update_settings_in_db(data):
    try:
        url = f"{FIREBASE_DB_URL}/settings.json"
        requests.patch(url, json=data, timeout=5)
        requests.patch(f"{FIREBASE_DB_URL}/config.json", json=data, timeout=3)
        return True
    except Exception as e:
        print(f"Settings Update Error: {e}")
        return False

def get_all_tasks_from_db():
    try:
        url = f"{FIREBASE_DB_URL}/tasks.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception as e:
        print(f"Firebase Tasks Fetch Error: {e}")
    return {}

def add_task_to_db(task_data):
    try:
        url = f"{FIREBASE_DB_URL}/tasks.json"
        res = requests.post(url, json=task_data, timeout=5)
        return res.status_code == 200
    except Exception as e:
        print(f"Add Task Error: {e}")
        return False

def delete_task_from_db(task_id):
    try:
        url = f"{FIREBASE_DB_URL}/tasks/{task_id}.json"
        requests.delete(url, timeout=5)
        return True
    except Exception as e:
        print(f"Delete Task Error: {e}")
        return False

def get_all_transactions_from_db():
    try:
        url = f"{FIREBASE_DB_URL}/transactions.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and res.json():
            return res.json()
    except Exception:
        pass
    return {}

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
# 👥 রেফারেল ও একাউন্ট হ্যান্ডলার
# =================================================================
def handle_referral_and_user_creation(user_id, full_name, username, referrer_id):
    user_id_str = str(user_id)
    user_data = get_user_from_db(user_id_str)
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    formatted_time = now.strftime("%I:%M %p | %d/%m/%Y")

    cfg = get_settings_from_db()
    current_refer_reward = float(cfg.get("referReward") or cfg.get("refer_reward") or REFER_REWARD)

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

                new_balance = cur_bal + current_refer_reward
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

💎 <b>রেফার বোনাস:</b> <b>+ ৳ {current_refer_reward:.2f} টাকা</b>
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
# ⌨️ কিবোর্ড লেআউটসমূহ (Reply Keyboards)
# =================================================================
def get_main_keyboard(user_id=None):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_task = types.KeyboardButton("💼 কাজ ⚡")
    btn_balance = types.KeyboardButton("💰 ব্যালেন্স 💎")
    btn_refer = types.KeyboardButton("👥 রেফার 🎁")
    btn_leaderboard = types.KeyboardButton("🏆 লিডারবোর্ড")
    btn_support = types.KeyboardButton("🛠️ সাপোর্ট 💬")

    keyboard.row(btn_task, btn_balance)
    keyboard.row(btn_refer, btn_leaderboard)
    keyboard.row(btn_support)

    if user_id and is_admin(user_id):
        btn_admin = types.KeyboardButton("👑 Admin Panel ⚙️")
        keyboard.row(btn_admin)

    return keyboard

def get_leaderboard_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_top10 = types.KeyboardButton("🏆 টপ ১০ লিডারবোর্ড")
    btn_my_refs = types.KeyboardButton("👥 আমার রেফারেল")
    btn_back = types.KeyboardButton("🔙 ব্যাক")

    keyboard.row(btn_top10, btn_my_refs)
    keyboard.row(btn_back)
    return keyboard

def get_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    
    btn_stats = types.KeyboardButton("📊 লাইভ ড্যাশবোর্ড")
    btn_withdraw = types.KeyboardButton("💸 উইথড্র রিকোয়েস্ট")
    
    btn_settings = types.KeyboardButton("⚙️ অ্যাপ সেটিংস")
    btn_balance = types.KeyboardButton("💰 ব্যালেন্স পরিবর্তন")
    
    btn_add_task = types.KeyboardButton("➕ নতুন টাস্ক যুক্ত")
    btn_manage_tasks = types.KeyboardButton("📋 টাস্ক ম্যানেজমেন্ট")
    
    btn_search_user = types.KeyboardButton("🔍 ইউজার তথ্য খুঁজুন")
    btn_broadcast = types.KeyboardButton("📢 অল ব্রডকাস্ট")
    
    btn_back_user = types.KeyboardButton("🏠 ইউজার মেন্যুতে যান")

    keyboard.row(btn_stats, btn_withdraw)
    keyboard.row(btn_settings, btn_balance)
    keyboard.row(btn_add_task, btn_manage_tasks)
    keyboard.row(btn_search_user, btn_broadcast)
    keyboard.row(btn_back_user)
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
    bot.send_message(message.chat.id, "👇 <b>নিচের মেন্যু থেকে অপশন বেছে নিন:</b>", reply_markup=get_main_keyboard(user_id))

# =================================================================
# 👑 অ্যাডমিন প্যানেল ওপেন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text and any(w in msg.text.lower() for w in ["👑 admin panel ⚙️", "/admin", "admin panel"]))
def admin_panel_open(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "⛔ <b>অননুমোদিত অ্যাক্সেস!</b> আপনি এই বটের অ্যাডমিন নন।")
        return

    admin_text = """👑 <b>MH EARNING - আলটিমেট অ্যাডমিন কন্ট্রোল প্যানেল</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>⚡ <i>স্বাগতম অ্যাডমিন! নিচের কিবোর্ড বাটনগুলো চেপে অ্যাপ ও বটের সবকিছু নিয়ন্ত্রণ করুন:</i>

📊 <b>লাইভ ড্যাশবোর্ড:</b> সকল ইউজার ও পেমেন্ট হিস্ট্রি
💸 <b>উইথড্র রিকোয়েস্ট:</b> পেমেন্ট অ্যাপ্রুভ বা রিজেক্ট
⚙️ <b>অ্যাপ সেটিংস:</b> রিওয়ার্ড ও উইথড্র লিমিট চেঞ্জ
💰 <b>ব্যালেন্স পরিবর্তন:</b> ইউজার ব্যালেন্স যোগ/বিয়োগ
➕ <b>নতুন টাস্ক:</b> সরাসরি চ্যানেল টাস্ক এড করুন
📋 <b>টাস্ক ডিলিট:</b> সক্রিয় টাস্ক তালিকা ও মুছে ফেলা
🔍 <b>ইউজার সার্চ:</b> ইউজারের বিস্তারিত একাউন্ট তথ্য
📢 <b>অল ব্রডকাস্ট:</b> সকল ইউজারকে নোটিফিকেশন পাঠানো</blockquote>

👇 <i>যেকোনো একটি বাটন চেপে কাজ শুরু করুন:</i>"""

    bot.send_message(message.chat.id, admin_text, reply_markup=get_admin_keyboard())

# =================================================================
# 👑 অ্যাডমিন কিবোর্ড বাটন হ্যান্ডলারসমূহ
# =================================================================
@bot.message_handler(func=lambda msg: msg.text == "📊 লাইভ ড্যাশবোর্ড")
def admin_dashboard_handler(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    all_users = get_all_users_from_db()
    all_tx = get_all_transactions_from_db()
    all_tasks = get_all_tasks_from_db()

    total_users = len(all_users)
    total_balance = sum(float(u.get("balance", 0.0)) for u in all_users.values() if isinstance(u, dict))
    
    pending_withdraws = sum(1 for tx in all_tx.values() if isinstance(tx, dict) and tx.get("status") == "Pending")
    total_paid = sum(float(tx.get("amount", 0.0)) for tx in all_tx.values() if isinstance(tx, dict) and tx.get("status") == "Approved")

    now = datetime.now()
    start_of_today = datetime(now.year, now.month, now.day).timestamp() * 1000
    today_users = sum(1 for u in all_users.values() if isinstance(u, dict) and float(u.get("joinedAt", 0)) >= start_of_today)

    stats_text = f"""📊 <b>বট ও মিনি অ্যাপের লাইভ স্ট্যাটিস্টিকস</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👥 <b>মোট ইউজার:</b> <b>{total_users} জন</b>
🆕 <b>আজকের নতুন ইউজার:</b> <b>{today_users} জন</b>
💰 <b>ইউজারদের মোট ব্যালেন্স:</b> <b>৳ {total_balance:.2f} টাকা</b>
💸 <b>পেমেন্ট সম্পন্ন:</b> <b>৳ {total_paid:.2f} টাকা</b>
⏳ <b>পেন্ডিং উইথড্র:</b> <b>{pending_withdraws} টি</b>
📋 <b>সচল টাস্ক সংখ্যা:</b> <b>{len(all_tasks)} টি</b></blockquote>"""

    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(func=lambda msg: msg.text == "💸 উইথড্র রিকোয়েস্ট")
def admin_withdraws_handler(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    all_tx = get_all_transactions_from_db()
    pending_list = [(k, v) for k, v in all_tx.items() if isinstance(v, dict) and v.get("status") == "Pending"]

    if not pending_list:
        bot.send_message(message.chat.id, "✅ <b>বর্তমানে কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই!</b>")
        return

    bot.send_message(message.chat.id, f"⏳ <b>মোট {len(pending_list)} টি পেন্ডিং উইথড্র পাওয়া গেছে:</b>")

    for tx_id, tx in pending_list[:5]:
        w_text = f"""💸 <b>পেন্ডিং উইথড্র রিকোয়েস্ট</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👤 <b>ইউজার:</b> {tx.get('userName', 'User')}
🆔 <b>আইডি:</b> <code>{tx.get('userId')}</code>
💳 <b>মেথড:</b> <b>{tx.get('method')}</b>
📱 <b>নাম্বার:</b> <code>{tx.get('account') or tx.get('number')}</code>
💰 <b>পরিমাণ:</b> <b>৳ {float(tx.get('amount', 0.0)):.2f} টাকা</b>
⏰ <b>সময়:</b> {tx.get('date', '')} {tx.get('time', '')}</blockquote>"""

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"tx_app_{tx_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"tx_rej_{tx_id}")
        )
        bot.send_message(message.chat.id, w_text, reply_markup=kb)

@bot.message_handler(func=lambda msg: msg.text == "⚙️ অ্যাপ সেটিংস")
def admin_settings_menu_handler(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    cfg = get_settings_from_db()
    ad_rew = float(cfg.get("adReward") or cfg.get("ad_reward") or AD_REWARD)
    ref_rew = float(cfg.get("referReward") or cfg.get("refer_reward") or REFER_REWARD)
    min_w = float(cfg.get("minWithdraw") or cfg.get("min_withdraw") or 1020)
    daily_l = int(cfg.get("dailyAdLimit") or cfg.get("daily_ad_limit") or 10)

    settings_text = f"""⚙️ <b>অ্যাপ সেটিংস ড্যাশবোর্ড</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎬 <b>প্রতি অ্যাড রিওয়ার্ড:</b> <b>৳ {ad_rew:.2f}</b>
👥 <b>রেফারেল বোনাস:</b> <b>৳ {ref_rew:.2f}</b>
💳 <b>সর্বনিম্ন উইথড্র:</b> <b>৳ {min_w:.2f}</b>
📊 <b>দৈনিক অ্যাড লিমিট:</b> <b>{daily_l} টি</b></blockquote>

👇 <i>যেকোনো মান পরিবর্তন করতে নিচের অপশন নির্বাচন করুন:</i>"""

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎬 অ্যাড টাকা বদলান", callback_data="adm_set_adreward"),
        types.InlineKeyboardButton("👥 রেফার টাকা বদলান", callback_data="adm_set_referreward"),
        types.InlineKeyboardButton("💳 উইথড্র লিমিট বদলান", callback_data="adm_set_minwithdraw"),
        types.InlineKeyboardButton("📊 অ্যাড লিমিট বদলান", callback_data="adm_set_adlimit")
    )
    bot.send_message(message.chat.id, settings_text, reply_markup=kb)

@bot.message_handler(func=lambda msg: msg.text == "💰 ব্যালেন্স পরিবর্তন")
def admin_balance_edit_handler(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    admin_states[user_id] = "adm_edit_bal_user"
    msg = bot.send_message(message.chat.id, "👤 যে ইউজারের ব্যালেন্স পরিবর্তন করতে চান তার <b>Telegram ID</b> লিখুন:\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
    bot.register_next_step_handler(msg, process_admin_input)

@bot.message_handler(func=lambda msg: msg.text == "➕ নতুন টাস্ক যুক্ত")
def admin_add_task_step1(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    admin_states[user_id] = "adm_task_title"
    msg = bot.send_message(message.chat.id, "📝 <b>টাস্কের নাম বা টাইটেল দিন:</b>\n<i>(যেমন: Join Telegram Channel)</i>\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
    bot.register_next_step_handler(msg, process_admin_input)

@bot.message_handler(func=lambda msg: msg.text == "📋 টাস্ক ম্যানেজমেন্ট")
def admin_manage_tasks_handler(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    all_tasks = get_all_tasks_from_db()
    if not all_tasks:
        bot.send_message(message.chat.id, "📋 <b>বর্তমানে কোনো টাস্ক যুক্ত নেই!</b>")
        return

    bot.send_message(message.chat.id, "📋 <b>বর্তমানে চালু থাকা টাস্ক তালিকা:</b>")
    for tid, t in all_tasks.items():
        if isinstance(t, dict):
            t_text = f"""🔹 <b>{t.get('title')}</b>
💰 <b>রিওয়ার্ড:</b> ৳ {float(t.get('reward', 0)):.2f}
🔗 <b>লিংক:</b> {t.get('link')}"""
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🗑️ এই টাস্কটি মুছে ফেলুন", callback_data=f"del_task_{tid}"))
            bot.send_message(message.chat.id, t_text, reply_markup=kb, disable_web_page_preview=True)

@bot.message_handler(func=lambda msg: msg.text == "🔍 ইউজার তথ্য খুঁজুন")
def admin_search_user_handler(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    admin_states[user_id] = "adm_search_user"
    msg = bot.send_message(message.chat.id, "🔍 যে ইউজারের তথ্য দেখতে চান তার <b>Telegram ID</b> পাঠান:\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
    bot.register_next_step_handler(msg, process_admin_input)

@bot.message_handler(func=lambda msg: msg.text == "📢 অল ব্রডকাস্ট")
def admin_broadcast_prompt(message):
    user_id = str(message.from_user.id)
    if not is_admin(user_id): return

    admin_states[user_id] = "adm_broadcast_msg"
    msg = bot.send_message(message.chat.id, "📢 সব ইউজারের কাছে যে মেসেজটি পাঠাতে চান তা লিখুন (HTML ফরম্যাট সমর্থিত):\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
    bot.register_next_step_handler(msg, process_admin_input)

@bot.message_handler(func=lambda msg: msg.text == "🏠 ইউজার মেন্যুতে যান")
def admin_back_to_user_menu(message):
    user_id = str(message.from_user.id)
    bot.send_message(message.chat.id, "🏠 <b>মূল ইউজার মেন্যুতে ফিরে আসা হয়েছে:</b>", reply_markup=get_main_keyboard(user_id))

# =================================================================
# 👑 অ্যাডমিন ইনপুট প্রসেসিং স্টেপস
# =================================================================
def process_admin_input(message):
    user_id = str(message.from_user.id)
    state = admin_states.get(user_id)
    text = message.text.strip() if message.text else ""

    if text.lower() == "/cancel":
        admin_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ অপারেশন বাতিল করা হয়েছে।", reply_markup=get_admin_keyboard())
        return

    if state == "adm_set_adreward":
        try:
            val = float(text)
            update_settings_in_db({"adReward": val, "ad_reward": val, "adRate": val, "rewardPerAd": val})
            bot.send_message(message.chat.id, f"✅ <b>সফল!</b> প্রতি ভিডিও অ্যাডের টাকা <b>৳ {val:.2f}</b> এ সেট করা হয়েছে।")
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা দিন!")
        admin_states.pop(user_id, None)

    elif state == "adm_set_referreward":
        try:
            val = float(text)
            update_settings_in_db({"referReward": val, "refer_reward": val, "referRate": val})
            bot.send_message(message.chat.id, f"✅ <b>সফল!</b> রেফারেল বোনাস <b>৳ {val:.2f}</b> এ সেট করা হয়েছে।")
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা দিন!")
        admin_states.pop(user_id, None)

    elif state == "adm_set_minwithdraw":
        try:
            val = float(text)
            update_settings_in_db({"minWithdraw": val, "min_withdraw": val})
            bot.send_message(message.chat.id, f"✅ <b>সফল!</b> সর্বনিম্ন উইথড্র <b>৳ {val:.2f}</b> এ সেট করা হয়েছে।")
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা দিন!")
        admin_states.pop(user_id, None)

    elif state == "adm_set_adlimit":
        try:
            val = int(text)
            update_settings_in_db({"dailyAdLimit": val, "daily_ad_limit": val, "adLimit": val})
            bot.send_message(message.chat.id, f"✅ <b>সফল!</b> দৈনিক ভিডিও লিমিট <b>{val} টি</b> সেট করা হয়েছে।")
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক পূর্ণসংখ্যা দিন!")
        admin_states.pop(user_id, None)

    elif state == "adm_edit_bal_user":
        target_uid = text
        u_data = get_user_from_db(target_uid)
        if not u_data:
            bot.send_message(message.chat.id, "❌ এই আইডির কোনো ইউজার পাওয়া যায়নি!")
            admin_states.pop(user_id, None)
            return

        admin_states[user_id] = f"adm_edit_bal_amt_{target_uid}"
        msg = bot.send_message(message.chat.id, f"👤 ইউজার: <b>{u_data.get('name')}</b>\n💵 বর্তমান ব্যালেন্স: <b>৳ {float(u_data.get('balance', 0.0)):.2f}</b>\n\n👉 ব্যালেন্স যোগ করতে ধনাত্মক (যেমন: <b>50</b>) বা কাটতে ঋণাত্মক (যেমন: <b>-20</b>) সংখ্যা লিখুন:")
        bot.register_next_step_handler(msg, process_admin_input)

    elif state and state.startswith("adm_edit_bal_amt_"):
        target_uid = state.replace("adm_edit_bal_amt_", "")
        try:
            amt = float(text)
            u_data = get_user_from_db(target_uid) or {}
            old_bal = float(u_data.get("balance", 0.0))
            new_bal = max(0.0, old_bal + amt)

            update_user_in_db(target_uid, {"balance": new_bal})
            bot.send_message(message.chat.id, f"✅ ইউজার (<code>{target_uid}</code>) এর ব্যালেন্স আপডেট হয়েছে!\nপূর্বের ব্যালেন্স: ৳ {old_bal:.2f}\nনতুন ব্যালেন্স: <b>৳ {new_bal:.2f} টাকা</b>", reply_markup=get_admin_keyboard())
            
            try:
                bot.send_message(int(target_uid), f"🔔 অ্যাডমিন কর্তৃক আপনার ব্যালেন্স আপডেট করা হয়েছে!\n💰 বর্তমান নতুন ব্যালেন্স: <b>৳ {new_bal:.2f} টাকা</b>")
            except Exception:
                pass
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক টাকার পরিমাণ দিন!")
        admin_states.pop(user_id, None)

    elif state == "adm_task_title":
        admin_states[user_id] = f"adm_task_reward|{text}"
        msg = bot.send_message(message.chat.id, f"💰 <b>'{text}'</b> টাস্কটির জন্য কত টাকা রিওয়ার্ড দিতে চান? (যেমন: 5.00)")
        bot.register_next_step_handler(msg, process_admin_input)

    elif state and state.startswith("adm_task_reward|"):
        title = state.split("|")[1]
        try:
            rew = float(text)
            admin_states[user_id] = f"adm_task_link|{title}|{rew}"
            msg = bot.send_message(message.chat.id, "🔗 <b>টেলিগ্রাম চ্যানেল বা গ্রুপের লিংক দিন:</b>\n<i>(যেমন: https://t.me/yourchannel)</i>")
            bot.register_next_step_handler(msg, process_admin_input)
        except ValueError:
            bot.send_message(message.chat.id, "❌ সঠিক সংখ্যা দিন!")
            admin_states.pop(user_id, None)

    elif state and state.startswith("adm_task_link|"):
        _, title, rew_str = state.split("|")
        rew = float(rew_str)
        link = text

        new_task = {
            "title": title,
            "reward": rew,
            "link": link,
            "createdAt": int(time.time() * 1000)
        }
        if add_task_to_db(new_task):
            bot.send_message(message.chat.id, f"🎉 <b>সফলভাবে নতুন টাস্ক যুক্ত করা হয়েছে!</b>\n\n📌 টাইটেল: {title}\n💰 রিওয়ার্ড: ৳ {rew:.2f}\n🔗 লিংক: {link}", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ টাস্ক যুক্ত করতে ব্যর্থ হয়েছে। ডাটাবেজ চেক করুন.", reply_markup=get_admin_keyboard())
        admin_states.pop(user_id, None)

    elif state == "adm_search_user":
        target_uid = text
        u_data = get_user_from_db(target_uid)
        if not u_data:
            bot.send_message(message.chat.id, "❌ এই আইডির কোনো ইউজার পাওয়া যায়নি!", reply_markup=get_admin_keyboard())
        else:
            joined_date = "N/A"
            if u_data.get("joinedAt"):
                joined_date = datetime.fromtimestamp(u_data.get("joinedAt")/1000).strftime('%d/%m/%Y %I:%M %p')
            
            u_info = f"""👤 <b>ইউজার প্রোফাইল ডাটাবেজ</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🆔 <b>টেলিগ্রাম আইডি:</b> <code>{target_uid}</code>
🏷️ <b>নাম:</b> {u_data.get('name', 'N/A')}
🔗 <b>ইউজারনেম:</b> {u_data.get('username', 'N/A')}
💵 <b>ব্যালেন্স:</b> <b>৳ {float(u_data.get('balance', 0.0)):.2f}</b>
👥 <b>রেফার করেছে:</b> {u_data.get('referrals', 0)} জন
🎬 <b>দেখা ভিডিও:</b> {u_data.get('adsWatched', 0)} টি
✅ <b>টাস্ক সম্পন্ন:</b> {u_data.get('completedTasksCount', 0)} টি
📅 <b>জয়েন তারিখ:</b> {joined_date}</blockquote>"""
            bot.send_message(message.chat.id, u_info, reply_markup=get_admin_keyboard())
        admin_states.pop(user_id, None)

    elif state == "adm_broadcast_msg":
        broadcast_text = text
        all_users = get_all_users_from_db()
        user_list = list(all_users.keys())

        bot.send_message(message.chat.id, f"🚀 <b>ব্রডকাস্ট শুরু হচ্ছে...</b> (মোট ইউজার: {len(user_list)} জন)", reply_markup=get_admin_keyboard())
        
        def run_broadcast():
            success, failed = 0, 0
            for uid in user_list:
                try:
                    bot.send_message(int(uid), broadcast_text, parse_mode="HTML")
                    success += 1
                except Exception:
                    failed += 1
                time.sleep(0.04)

            bot.send_message(int(user_id), f"🎉 <b>ব্রডকাস্ট সম্পন্ন হয়েছে!</b>\n✅ সফল: {success} জন\n❌ ব্যর্থ: {failed} জন")

        threading.Thread(target=run_broadcast).start()
        admin_states.pop(user_id, None)

# =================================================================
# 👑 অ্যাডমিন ইনলাইন বাটন ও কলব্যাক হ্যান্ডলার
# =================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_set_"))
def admin_settings_callback(call):
    user_id = str(call.from_user.id)
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ পারমিশন নেই!", show_alert=True)
        return

    action = call.data
    admin_states[user_id] = action
    prompt_map = {
        "adm_set_adreward": "🎬 প্রতি অ্যাডে কত টাকা দিতে চান? (যেমন: 15)",
        "adm_set_referreward": "👥 প্রতি রেফারে কত টাকা দিতে চান? (যেমন: 60)",
        "adm_set_minwithdraw": "💳 সর্বনিম্ন উইথড্র কত করতে চান? (যেমন: 1000)",
        "adm_set_adlimit": "📊 প্রতিদিন কতটি ভিডিও অ্যাড দেখাতে চান? (যেমন: 15)"
    }
    msg = bot.send_message(call.message.chat.id, f"📝 <b>ইনপুট প্রদান করুন:</b>\n{prompt_map[action]}\n\n<i>(বাতিল করতে /cancel লিখুন)</i>")
    bot.register_next_step_handler(msg, process_admin_input)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_task_"))
def admin_delete_task(call):
    user_id = str(call.from_user.id)
    if not is_admin(user_id): return

    task_id = call.data.replace("del_task_", "")
    if delete_task_from_db(task_id):
        bot.answer_callback_query(call.id, "🗑️ টাস্কটি মুছে ফেলা হয়েছে!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ টাস্ক মুছতে সমস্যা হয়েছে!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tx_app_") or call.data.startswith("tx_rej_"))
def handle_tx_decision(call):
    user_id = str(call.from_user.id)
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ অননুমোদিত!", show_alert=True)
        return

    is_approve = call.data.startswith("tx_app_")
    tx_id = call.data.replace("tx_app_", "").replace("tx_rej_", "")

    try:
        tx_url = f"{FIREBASE_DB_URL}/transactions/{tx_id}.json"
        tx_res = requests.get(tx_url, timeout=5)
        tx = tx_res.json() if tx_res.status_code == 200 else None

        if not tx:
            bot.answer_callback_query(call.id, "❌ লেনদেন ডাটা পাওয়া যায়নি!", show_alert=True)
            return

        target_uid = str(tx.get("userId"))
        amount = float(tx.get("amount", 0.0))

        if is_approve:
            requests.patch(tx_url, json={"status": "Approved"}, timeout=5)
            bot.answer_callback_query(call.id, "✅ উইথড্র Approved করা হয়েছে!", show_alert=True)
            bot.edit_message_text(f"✅ <b>উইথড্র অ্যাপ্রুভড!</b>\nইউজার: {target_uid} | পরিমাণ: ৳ {amount:.2f}", call.message.chat.id, call.message.message_id)

            try:
                bot.send_message(int(target_uid), f"🎉 <b>অভিনন্দন! আপনার ৳ {amount:.2f} টাকার উইথড্র সফলভাবে পেমেন্ট করা হয়েছে!</b> 💸")
            except Exception:
                pass
        else:
            requests.patch(tx_url, json={"status": "Rejected"}, timeout=5)
            u_data = get_user_from_db(target_uid) or {}
            c_bal = float(u_data.get("balance", 0.0))
            c_rej = int(u_data.get("rejectedCount", 0)) + 1

            update_user_in_db(target_uid, {"balance": c_bal + amount, "rejectedCount": c_rej})

            bot.answer_callback_query(call.id, "❌ উইথড্র Rejected ও টাকা রিফান্ড করা হয়েছে!", show_alert=True)
            bot.edit_message_text(f"❌ <b>উইথড্র রিজেক্টেড ও টাকা ফেরত দেওয়া হয়েছে!</b>\nইউজার: {target_uid} | রিফান্ড: ৳ {amount:.2f}", call.message.chat.id, call.message.message_id)

            try:
                bot.send_message(int(target_uid), f"⚠️ <b>আপনার ৳ {amount:.2f} টাকার উইথড্র রিকোয়েস্ট বাতিল করা হয়েছে এবং টাকা মূল ব্যালেন্সে রিফান্ড করা হয়েছে।</b>")
            except Exception:
                pass
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)

# =================================================================
# ২. কাজের বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text == "💼 কাজ ⚡")
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
@bot.message_handler(func=lambda msg: msg.text == "🎬 ভিডিও এড দেখুন")
def video_ad_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    ads_watched = int(user_data.get("adsWatched", 0))

    cfg = get_settings_from_db()
    current_ad_reward = float(cfg.get("adReward") or cfg.get("ad_reward") or AD_REWARD)
    current_daily_limit = int(cfg.get("dailyAdLimit") or cfg.get("daily_ad_limit") or 10)

    server1_webapp_url = f"{MINI_APP_URL}#action=watch_ad&server=1&tgWebAppStartParam={user_id}"
    server2_webapp_url = f"{MINI_APP_URL}#action=watch_ad&server=2&tgWebAppStartParam={user_id}"

    ad_kb = types.InlineKeyboardMarkup(row_width=2)
    btn_server1 = types.InlineKeyboardButton(text="▶️ Server 1 ⚡", web_app=types.WebAppInfo(url=server1_webapp_url))
    btn_server2 = types.InlineKeyboardButton(text="▶️ Server 2 ⚡", web_app=types.WebAppInfo(url=server2_webapp_url))
    ad_kb.add(btn_server1, btn_server2)

    msg_text = f"""🎬 <b>প্রিমিয়াম ভিডিও বিজ্ঞাপন জোন</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>💎 <b>বিজ্ঞাপন রিওয়ার্ড:</b> <b>৳ {current_ad_reward:.2f} টাকা</b> প্রতি ভিডিও!
📊 <b>আজকের দেখা ভিডিও:</b> <b>{ads_watched} / {current_daily_limit}</b> টি

⚡ <b>নিয়মাবলী:</b>
১. নিচের <b>Server 1</b> অথবা <b>Server 2</b> বাটনে চাপ দিন।
২. বিজ্ঞাপনটি সম্পূর্ণ শেষ হওয়া পর্যন্ত দেখুন।
৩. দেখা শেষ হওয়ামাত্রই টাকা সরাসরি মূল ওয়ালেটে যুক্ত হবে।</blockquote>

👇 <i>যেকোনো একটি সার্ভার নির্বাচন করে এড দেখুন:</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=ad_kb, disable_web_page_preview=True)

# =================================================================
# ৪. ট্যাক্স সম্পূর্ণ করুন এবং রিয়েল-টাইম চ্যানেল লিভ ডিটেকশন হ্যান্ডলার
# =================================================================
@bot.chat_member_handler()
def handle_chat_member_update(update: types.ChatMemberUpdated):
    """ইউজার চ্যানেল বা গ্রুপ থেকে লিভ নিলে সাথে সাথে ডিটেকশন ও ব্যালেন্স কাটা"""
    try:
        chat = update.chat
        user = update.new_chat_member.user
        user_id = str(user.id)

        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status

        was_in_chat = old_status in ['member', 'administrator', 'creator', 'restricted']
        is_now_in_chat = new_status in ['member', 'administrator', 'creator', 'restricted']

        if was_in_chat and not is_now_in_chat:
            chat_username = chat.username
            if not chat_username:
                return

            all_tasks = get_all_tasks_from_db()
            matched_task_id = None
            task_reward = 0.0

            for tid, t in all_tasks.items():
                if isinstance(t, dict):
                    t_link = t.get("link", t.get("url", ""))
                    c_uname = extract_telegram_username(t_link)
                    if c_uname and c_uname.lower() == chat_username.lower():
                        matched_task_id = tid
                        task_reward = float(t.get("reward", 5.00))
                        break

            if matched_task_id:
                user_data = get_user_from_db(user_id)
                if user_data:
                    completed_list = user_data.get("completedTasksList", {}) or {}
                    if completed_list.get(str(matched_task_id)) is True:
                        cur_bal = float(user_data.get("balance", 0.0))
                        cur_tasks_count = int(user_data.get("completedTasksCount", 0))

                        new_balance = max(0.0, cur_bal - task_reward)
                        new_tasks_count = max(0, cur_tasks_count - 1)

                        completed_list.pop(str(matched_task_id), None)

                        update_user_in_db(user_id, {
                            "balance": new_balance,
                            "completedTasksCount": new_tasks_count,
                            "completedTasksList": completed_list
                        })

                        notif_kb = types.InlineKeyboardMarkup(row_width=1)
                        task_obj = all_tasks.get(matched_task_id)
                        t_url = task_obj.get("link", task_obj.get("url", "https://t.me")) if task_obj else "https://t.me"
                        
                        btn_rejoin = types.InlineKeyboardButton(text="👉 এখনই পুনরায় জয়েন করুন 🚀", url=t_url)
                        btn_reverify = types.InlineKeyboardButton(text="✅ ভেরিফাই করে টাকা ফিরিয়ে নিন 🔄", callback_data=f"verify_{matched_task_id}")
                        notif_kb.add(btn_rejoin, btn_reverify)

                        notif_msg = f"""⚠️ <b>সতর্কবার্তা! চ্যানেল থেকে লিভ নেওয়ার কারণে রিওয়ার্ড কাটা হয়েছে!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>❌ আপনি আমাদের অফিশিয়াল চ্যানেল/গ্রুপ থেকে বের হয়ে গেছেন!

📉 <b>কর্তনকৃত পরিমাণ:</b> <b>- ৳ {task_reward:.2f} টাকা</b>
💵 <b>বর্তমান ব্যালেন্স:</b> <b>৳ {new_balance:.2f} টাকা</b></blockquote>

👇 <i>টাকা পুনরায় ওয়ালেটে ফেরত পেতে নিচের বাটনে ক্লিক করে আবার জয়েন করুন এবং ভেরিফাই করুন:</i>"""

                        bot.send_message(int(user_id), notif_msg, reply_markup=notif_kb)
    except Exception as e:
        print(f"Chat Member Update Error: {e}")

@bot.message_handler(func=lambda msg: msg.text == "📋 ট্যাক্স সম্পূর্ণ করুন")
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
৩. ভেরিফাই হওয়ামাত্রই বোনাস ব্যালেন্সে যুক্ত হবে!
⚠️ <i>সতর্কতা: জয়েন করার পর চ্যানেল বা গ্রুপ থেকে লিভ নিলে সাথে সাথেই আপনার ব্যালেন্স থেকে সমপরিমাণ টাকা কেটে নেওয়া হবে।</i></blockquote>\n"""

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
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        bot.send_message(message.chat.id, msg_text, reply_markup=task_kb, disable_web_page_preview=True)

# টাস্ক ভেরিফাই Callback
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
# ৫. ব্যালেন্স বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["💰 ব্যালেন্স 💎", "/balance"])
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
# ৬. রেফার বাটন হ্যান্ডলার (শুধু ইনভাইট ও রেফার লিংক শেয়ার)
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["👥 রেফার 🎁", "/refer"])
def refer_handler(message):
    user_id = str(message.from_user.id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    cfg = get_settings_from_db()
    current_refer_reward = float(cfg.get("referReward") or cfg.get("refer_reward") or REFER_REWARD)

    user_data = get_user_from_db(user_id) or {}
    total_refs = int(user_data.get("referrals", 0))
    earned_from_refs = total_refs * current_refer_reward

    share_text = f"🔥 MH EARNING BOT-এ জয়েন করে টাকা ইনকাম শুরু করুন!\n\n👉 রেফারেল লিংক: {referral_link}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}"

    ref_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_share = types.InlineKeyboardButton(text="📢 রেফার লিংক বন্ধুদের শেয়ার 🚀", url=share_url)
    ref_kb.add(btn_share)

    msg_text = f"""👥 <b>রেফারেল ইনকাম সেন্টার</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🎁 <b>প্রতি রেফারে বোনাস:</b> <b>৳ {current_refer_reward:.2f}</b> টাকা!
📊 <b>সর্বমোট রেফারেল:</b> <b>{total_refs}</b> জন
💰 <b>রেফার থেকে আয়:</b> <b>৳ {earned_from_refs:.2f}</b> টাকা</blockquote>

🔗 <b>আপনার পার্সোনাল রেফার লিংক:</b>
<code>{referral_link}</code>

<i>(লিংকটিতে একবার ট্যাপ করলেই কপি হয়ে যাবে)</i>"""

    bot.send_message(message.chat.id, msg_text, reply_markup=ref_kb, disable_web_page_preview=True)

# =================================================================
# 🏆 লিডারবোর্ড সাব-মেন্যু ওপেন বাটন
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["🏆 লিডারবোর্ড", "/leaderboard"])
def leaderboard_menu_handler(message):
    text = """🏆 <b>লিডারবোর্ড ও রেফারেল র‍্যাংকিং হাব</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>🌟 <i>আমাদের প্ল্যাটফর্মের সেরা লিডার ও আপনার নিজস্ব সফল রেফারেলদের বিস্তারিত তথ্য দেখতে নিচের যেকোনো অপশন নির্বাচন করুন:</i>

🥇 <b>/🏆 টপ ১০ লিডারবোর্ড:</b> শীর্ষ ১০ জন রেফারকারীর নাম ও তাদের রেফার সংখ্যা
👥 <b>/👥 আমার রেফারেল:</b> আপনার রেফার করা সদস্যদের নাম ও ডান পাশে তাদের ব্যালেন্স
🔙 <b>/🔙 ব্যাক:</b> পূর্ববর্তী মূল মেন্যুতে ফিরে যান</blockquote>

👇 <i>নিচের কিবোর্ড থেকে অপশন বেছে নিন:</i>"""
    bot.send_message(message.chat.id, text, reply_markup=get_leaderboard_keyboard())

# =================================================================
# 🥇 ১. লাইভ গ্লোবাল টপ ১০ রেফার লিডারবোর্ড হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["🏆 টপ ১০ লিডারবোর্ড", "/🏆 টপ ১০ লিডারবোর্ড", "টপ ১০", "top 10"])
def top_10_leaderboard_handler(message):
    all_users = get_all_users_from_db()

    user_list = []
    for uid, udata in all_users.items():
        if isinstance(udata, dict):
            refs = int(udata.get("referrals", 0))
            name = udata.get("name", "User")
            user_list.append({"id": uid, "name": name, "refs": refs})

    user_list.sort(key=lambda x: x["refs"], reverse=True)
    top_10 = user_list[:10]

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    leader_lines = []
    for idx, usr in enumerate(top_10):
        badge = medals[idx] if idx < len(medals) else f"#{idx+1}"
        u_name = usr['name']
        ref_cnt = usr['refs']
        leader_lines.append(f"{badge} <b>{u_name}</b> — <b>{ref_cnt} জন রেফার</b>")

    if not leader_lines:
        leader_lines.append("<i>বর্তমানে কোনো লিডারবোর্ড ডাটা পাওয়া যায়নি!</i>")

    top_text = "\n".join(leader_lines)

    res_msg = f"""🏆 <b>টপ ১০ রেফার লিডারবোর্ড</b> 🌟
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>👑 <b>সর্বোচ্চ রেফারকারী সেরা ১০ সদস্য:</b>

{top_text}</blockquote>

🚀 <i>বেশি বেশি রেফার করুন এবং লিডারবোর্ডের শীর্ষে উঠে জিতে নিন বিশেষ সম্মাননা ও রিওয়ার্ড!</i>"""

    bot.send_message(message.chat.id, res_msg)

# =================================================================
# 👥 ২. আমার রেফারেল হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["👥 আমার রেফারেল", "/👥 আমার রেফারেল", "আমার রেফারেল", "আমার রেফার"])
def my_referrals_list_handler(message):
    user_id = str(message.from_user.id)
    user_data = get_user_from_db(user_id) or {}
    total_refs_count = int(user_data.get("referrals", 0))

    try:
        ref_url = f"{FIREBASE_DB_URL}/users/{user_id}/myReferrals.json"
        res = requests.get(ref_url, timeout=5)
        my_refs_dict = res.json() if (res.status_code == 200 and res.json()) else {}
    except Exception:
        my_refs_dict = {}

    all_users = get_all_users_from_db()

    if not my_refs_dict:
        my_refs_dict = {uid: u for uid, u in all_users.items() if isinstance(u, dict) and str(u.get("referredBy")) == user_id}

    ref_items = []
    for ref_uid, v in my_refs_dict.items():
        live_ref_user = all_users.get(str(ref_uid), {}) if isinstance(all_users, dict) else {}
        
        name = live_ref_user.get("name") or (v.get("name") if isinstance(v, dict) else "User")
        balance = float(live_ref_user.get("balance", 0.0))
        joined_at = live_ref_user.get("joinedAt") or (v.get("joinedAt") if isinstance(v, dict) else 0)

        ref_items.append({
            "id": str(ref_uid),
            "name": name,
            "balance": balance,
            "joinedAt": joined_at
        })

    ref_items.sort(key=lambda x: (x["balance"], x["joinedAt"]), reverse=True)
    top_my_refs = ref_items[:10]

    if not top_my_refs:
        no_ref_text = f"""👥 <b>আমার রেফারেল তালিকা</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>📊 <b>আপনার মোট রেফার:</b> <b>০ জন</b>
❌ <i>আপনি এখনো কাউকে রেফার করেননি!</i></blockquote>

👉 <i>রেফার লিংক শেয়ার করে এখনই ৫০ টাকা করে বোনাস আয় শুরু করুন!</i>"""
        bot.send_message(message.chat.id, no_ref_text)
        return

    ref_lines = []
    for idx, r in enumerate(top_my_refs, 1):
        u_name = r['name']
        bal = r['balance']
        line = f"<b>{idx}. 👤 {u_name}</b> ──────── <b>৳ {bal:.2f}</b>"
        ref_lines.append(line)

    joined_list_str = "\n".join(ref_lines)

    my_ref_text = f"""👥 <b>আমার রেফারেল মেম্বার তালিকা (টপ ১০)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>📊 <b>মোট রেফারেল:</b> <b>{total_refs_count} জন</b>

{joined_list_str}</blockquote>

⚡ <i>আপনার রেফারেল সদস্যদের রিয়েলটাইম লাইভ ব্যালেন্স প্রদর্শিত হচ্ছে!</i>"""

    bot.send_message(message.chat.id, my_ref_text)

# =================================================================
# ৭. সাপোর্ট বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["🛠️ সাপোর্ট 💬", "/support"])
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
# ৮. সাধারণ ব্যাক বাটন হ্যান্ডলার
# =================================================================
@bot.message_handler(func=lambda msg: msg.text in ["🔙 ব্যাক", "/🔙 ব্যাক", "ব্যাক", "back", "মেন্যু", "<-"])
def back_to_main_menu(message):
    user_id = str(message.from_user.id)
    bot.send_message(message.chat.id, "🏠 <b>মূল মেন্যুতে ফিরে আসা হয়েছে:</b>", reply_markup=get_main_keyboard(user_id))

# =================================================================
# ❓ অপরিচিত ও অনাকাঙ্ক্ষিত মেসেজ হ্যান্ডলার (Fallback Handler)
# =================================================================
@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def fallback_unknown_message(message):
    user_id = str(message.from_user.id)
    fallback_text = """🤖 <b>দুঃখিত! আপনি যা লিখেছেন তা আমি বুঝতে পারিনি।</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<blockquote>💡 <i>বটটি ব্যবহার করতে নিচের কিবোর্ড বাটনগুলো চেপে অপশন সিলেক্ট করুন অথবা পুনরায় শুরু করতে <b>/start</b> কমান্ডটি লিখুন।</i></blockquote>"""
    bot.send_message(message.chat.id, fallback_text, reply_markup=get_main_keyboard(user_id))

# =================================================================
# 🚀 মেইন ইঞ্জিন রানার (Allowed Updates সহ আপডেট করা)
# =================================================================
if __name__ == "__main__":
    print("🌐 Keep-Alive Server চালু হচ্ছে...")
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("✅ MH Earning Bot Engine সফলভাবে চালু হয়েছে...")
    # এখানে allowed_updates যোগ করা হয়েছে যাতে টেলিগ্রাম বট লিভ নেওয়া ট্র্যাক করতে পারে
    bot.infinity_polling(timeout=10, long_polling_timeout=5, allowed_updates=['message', 'chat_member', 'callback_query'])
