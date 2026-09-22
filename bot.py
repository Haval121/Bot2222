import asyncio
import os
import json
from datetime import datetime, timezone
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError, UserNotParticipantError
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
from telethon.tl.functions.channels import InviteToChannelRequest
from colorama import init, Fore

init(autoreset=True)

# زانیارییە سەرەتاییەکان
API_ID = 36234377
API_HASH = "5e199e2ae89cc1c42a6a4853951ff98f"
BOT_TOKEN = "8993540801:AAH_W0X78Cjndjg1uXwgwl4khRSWvk5JFfw"

ACCOUNTS_FILE = "accounts_list.json"
SESSION_DIR = "sessions"
TARGETS_FILE = "target_users.txt"
FAILED_FILE = "failed_users.txt"

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

def load_failed_users():
    if os.path.exists(FAILED_FILE):
        with open(FAILED_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_failed_user(identifier):
    failed = load_failed_users()
    if identifier not in failed:
        with open(FAILED_FILE, "a", encoding="utf-8") as f:
            f.write(identifier + "\n")

# ==================== بەشی دروستکردنی سیشن لە ڕێگەی بۆتەوە ====================
async def run_telegram_bot():
    bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    user_states = {}

    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        await event.respond(
            "👋 بە خیر هاتیت بۆ بۆتی دروستکردنی سیشنی تێلیگرام.\n\n"
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
                await finish_login(event, user_id, bot)
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
                await finish_login(event, user_id, bot)
            except Exception as e:
                await event.respond(f"❌ پاسوورەکە هەڵەیە: {e}\nدووبارە `/start` بنوسە.")
                await client.disconnect()
                del user_states[user_id]

    async def finish_login(event, user_id, bot_client):
        client = user_states[user_id]["client"]
        session_path = user_states[user_id]["session_path"]
        phone = user_states[user_id]["phone"]
        
        me = await client.get_me()
        await client.disconnect()

        real_session_file = f"{session_path}.session"

        if os.path.exists(real_session_file):
            # زیادکردنی ئۆتۆماتیکی بۆ فایلی accounts_list.json
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
                f"فایلی سیشنەکەت دروست بوو و لە سیستەمدا پاشەکەوت کرا:"
            )
            await event.respond(file=real_session_file)
        else:
            await event.respond("❌ هەڵەیەک ڕوویدا.")

        del user_states[user_id]

    print(f"{Fore.GREEN}Telegram Bot is running for generating sessions...")
    await bot.run_until_disconnected()

# ==================== بەشی سکریپتی سکراپ و زیادکردن ====================
async def scrape_and_filter_users():
    print(f"\n{Fore.CYAN}=== SCRAPE & SMART FILTER USERS ===")
    accounts = load_accounts()
    if not accounts:
        print(f"{Fore.RED}No accounts found!")
        return

    acc = accounts[0]
    client = TelegramClient(acc["session"], acc["api_id"], acc["api_hash"])
    await client.start()

    source_group = input(f"{Fore.GREEN}Enter source group link/username: {Fore.WHITE}").strip()
    dest_group = input(f"{Fore.GREEN}Enter destination group link/username: {Fore.WHITE}").strip()
    
    try:
        limit_input = input(f"{Fore.GREEN}Max users to scrape (Press Enter for unlimited): {Fore.WHITE}").strip()
        max_users = int(limit_input) if limit_input.isdigit() else float('inf')
    except Exception:
        max_users = float('inf')

    try:
        print(f"{Fore.YELLOW}Fetching members...")
        source_entity = await client.get_entity(source_group)
        dest_entity = await client.get_entity(dest_group)

        failed_users = load_failed_users()
        valid_users = []
        total_checked = 0

        async for user in client.iter_participants(source_entity):
            if len(valid_users) >= max_users:
                break
            if user.bot or user.deleted:
                continue

            identifier = user.username if user.username else str(user.id)
            if identifier in failed_users:
                continue

            total_checked += 1
            try:
                await client.get_permissions(dest_entity, user)
                continue
            except UserNotParticipantError:
                pass
            except Exception:
                pass

            if getattr(user, 'restricted', False):
                continue

            valid_users.append(identifier)
            print(f"{Fore.GREEN}[VALID] Added: {identifier}")

        with open(TARGETS_FILE, "w", encoding="utf-8") as f:
            for u in valid_users:
                f.write(u + "\n")

        print(f"{Fore.GREEN}=== SCRAPING COMPLETED. Saved: {len(valid_users)} ===")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")
    finally:
        await client.disconnect()

async def filter_and_add_members():
    print(f"\n{Fore.CYAN}=== ADD MEMBERS TO DESTINATION GROUP ===")
    accounts = load_accounts()
    if not accounts:
        print(f"{Fore.RED}No accounts found! Please generate a session first.")
        return

    if not os.path.exists(TARGETS_FILE):
        print(f"{Fore.RED}Target file not found!")
        return

    with open(TARGETS_FILE, "r", encoding="utf-8") as f:
        targets = [line.strip() for line in f if line.strip()]

    if not targets:
        print(f"{Fore.RED}No targets found.")
        return

    dest_group = input(f"{Fore.GREEN}Enter destination group link/username: {Fore.WHITE}").strip()
    
    acc_index = 0
    current_client = TelegramClient(
        accounts[acc_index]["session"], 
        accounts[acc_index]["api_id"], 
        accounts[acc_index]["api_hash"]
    )
    await current_client.start()

    try:
        dest_entity = await current_client.get_entity(dest_group)
    except Exception as e:
        print(f"{Fore.RED}Cannot access destination group: {e}")
        await current_client.disconnect()
        return

    remaining_targets = list(targets)

    for target in targets:
        await asyncio.sleep(5)  # چاوەڕوانی بۆ ئەوەی سپام نەبوو

        query_target = int(target) if target.isdigit() else target
        display_name = f"@{target}" if not target.isdigit() else f"ID:{target}"

        try:
            user_entity = await current_client.get_entity(query_target)
            await current_client(InviteToChannelRequest(
                channel=dest_entity,
                users=[user_entity]
            ))
            print(f"{Fore.GREEN}[SUCCESS] Added {display_name}")
            remaining_targets.remove(target)
        except FloodWaitError as e:
            print(f"{Fore.RED}[FLOOD] Wait {e.seconds} seconds.")
            break
        except Exception as err:
            print(f"{Fore.YELLOW}[SKIP] {display_name}: {err}")
            save_failed_user(target)
            remaining_targets.remove(target)

    with open(TARGETS_FILE, "w", encoding="utf-8") as f:
        for u in remaining_targets:
            f.write(u + "\n")

    await current_client.disconnect()
    print(f"{Fore.GREEN}Process completed!")

# ==================== سەرەکی (Main Menu) ====================
async def main():
    while True:
        print(f"\n{Fore.MAGENTA}==========================================")
        print(f"{Fore.WHITE}       TELEGRAM MANAGER & BOT TOOL        ")
        print(f"{Fore.MAGENTA}==========================================")
        print(f"{Fore.WHITE}1. Start Telegram Bot (To generate session)")
        print(f"{Fore.WHITE}2. Scrape & Filter Users")
        print(f"{Fore.WHITE}3. Add Members to Group")
        print(f"{Fore.WHITE}4. Exit")
        
        choice = input(f"\n{Fore.GREEN}Choose an option (1-4): {Fore.WHITE}").strip()
        
        if choice == "1":
            await run_telegram_bot()
        elif choice == "2":
            await scrape_and_filter_users()
        elif choice == "3":
            await filter_and_add_members()
        elif choice == "4":
            break
        else:
            print(f"{Fore.RED}Invalid choice!")

if __name__ == "__main__":
    asyncio.run(main())
                
