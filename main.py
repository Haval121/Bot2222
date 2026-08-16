import logging
import sqlite3
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, CallbackQueryHandler, filters
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

USERNAME, NAME, UPLOAD_VIDEO, SEARCH_QUERY, EDIT_CAPTION = range(5)

BOT_TOKEN = "8681382827:AAHZdoim4mbMvhvsjFqeW9AOc23OuV_kl-A"

# ----------------- Database Setup (Railway Volume Support) -----------------
# ئەگەر لەسەر Railway بوو، داتاکان دەچنە ناو Volume بۆ ئەوەی نەسڕێنەوە
DATA_DIR = "/app/data" if os.path.exists("/app") else "."
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "bot_data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            video_file_id TEXT,
            caption TEXT,
            views INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER,
            video_id INTEGER,
            PRIMARY KEY (user_id, video_id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Helper Functions for Database
def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, name FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_user(user_id, username, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, username, name) VALUES (?, ?, ?)", (user_id, username, name))
    conn.commit()
    conn.close()

def add_video(user_id, video_file_id, caption):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (user_id, video_file_id, caption, views) VALUES (?, ?, ?, 1)", (user_id, video_file_id, caption))
    conn.commit()
    conn.close()

def get_all_videos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, video_file_id, caption, views FROM videos")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_videos(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, video_file_id, caption, views FROM videos WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_views(video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET views = views + 1 WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()

def toggle_like(user_id, video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM likes WHERE user_id = ? AND video_id = ?", (user_id, video_id))
    liked = cursor.fetchone()
    
    if liked:
        cursor.execute("DELETE FROM likes WHERE user_id = ? AND video_id = ?", (user_id, video_id))
        is_liked = False
    else:
        cursor.execute("INSERT INTO likes (user_id, video_id) VALUES (?, ?)", (user_id, video_id))
        is_liked = True
        
    conn.commit()
    conn.close()
    return is_liked

def get_like_count(video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM likes WHERE video_id = ?", (video_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def update_caption(video_id, new_caption):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET caption = ? WHERE id = ?", (new_caption, video_id))
    conn.commit()
    conn.close()

def delete_video(video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    cursor.execute("DELETE FROM likes WHERE video_id = ?", (video_id,))
    conn.commit()
    conn.close()

def delete_account(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM likes WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM likes WHERE video_id IN (SELECT id FROM videos WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM videos WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ----------------- Keyboards -----------------
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎬 ڤیدیۆکان 🔞")],
        [KeyboardButton("📩 بڵاوکردنەوەی ڤیدیۆ 🎬"), KeyboardButton("🔍 گەڕان")],
        [KeyboardButton("👤 هەژمارەکەم")]
    ], resize_keyboard=True)

def back_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("⬅️ گەڕانەوە")]], resize_keyboard=True)

# ----------------- Start & Registration (With Deep Linking Profile View) -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.args and context.args[0].startswith("prof_"):
        target_username = context.args[0].replace("prof_", "")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, name FROM users WHERE username = ?", (target_username,))
        target_user = cursor.fetchone()
        conn.close()
        
        if target_user:
            t_user_id, t_username, t_name = target_user
            t_vids = get_user_videos(t_user_id)
            
            text = (
                f"👤 **پڕۆفایلی: {t_name}**\n"
                f"🔗 @{t_username}\n\n"
                f"📊 **ئامارەکانی هەژمار:**\n"
                f"🎬 ژمارەی پۆستەکان: {len(t_vids)}\n"
            )
            
            grid_buttons = []
            if not t_vids:
                text += "\n📝 هێشتا هیچ پۆستێکی بڵاونەکردووەتەوە."
            else:
                text += "\n👇 کاتێک داگریت لەسەر هەریەک لە ژمارەکان ڤیدیۆکە نیشان دەدرێت:"
                row = []
                for idx, vid in enumerate(t_vids, 1):
                    vid_id = vid[0]
                    row.append(InlineKeyboardButton(f"🎥 #{idx}", callback_data=f"show_my_vid_{vid_id}"))
                    if len(row) == 3:
                        grid_buttons.append(row)
                        row = []
                if row:
                    grid_buttons.append(row)
                    
            kb = InlineKeyboardMarkup(grid_buttons) if grid_buttons else None
            await update.message.reply_text(text, reply_markup=kb)
            return ConversationHandler.END
        else:
            await update.message.reply_text("❌ ئەم هەژمارە نەدۆزرایەوە یان سڕدراوەتەوە.")
            return ConversationHandler.END

    welcome_text = "┌─── 🎬 TikTok_Hub ───┐\n\n│ 👋 سڵاو!\n\n│ 🎬 بەخێربێیت بۆ TikTok_hub\n\n│ 📩 ئێستا پۆست بکه لە هەژمارەکەت\n\n└─────────────────────┘"
    
    if get_user(user_id):
        await update.message.reply_text(welcome_text, reply_markup=main_keyboard())
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"{welcome_text}\n\n🧾 بۆ بەکارهێنانی بۆت، سەرەتا هەژمارەکەت دروست بکه.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("📝 دروستکردنی هەژمار")]], resize_keyboard=True)
        )
        return ConversationHandler.END

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧾 **دروستکردنی هەژمار**\n\nتکایه username ئەکەت بنووسه.\nتەنها پیته ئینگلیزییەکان، ژماره و _ بەکاربهێنه.",
        reply_markup=back_keyboard()
    )
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ گەڕانەوە":
        await update.message.reply_text("گەڕایتەوە بۆ ڕووکاری سەرەکی.", reply_markup=main_keyboard())
        return ConversationHandler.END

    context.user_data['username'] = update.message.text.replace("@", "")
    await update.message.reply_text("✅ username تۆمار کرا.\n\nئێستا ناوت بنووسه:", reply_markup=back_keyboard())
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ گەڕانەوە":
        await update.message.reply_text("گەڕایتەوە بۆ ڕووکاری سەرەکی.", reply_markup=main_keyboard())
        return ConversationHandler.END

    user_id = update.effective_user.id
    username = context.user_data['username']
    name = update.message.text
    
    add_user(user_id, username, name)
    await update.message.reply_text("✅ هەژمارەکەت بە سەرکەوتوویی دروستکرا.", reply_markup=main_keyboard())
    return ConversationHandler.END
        # ----------------- Upload Video -----------------
async def upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 **بڵاوکردنەوەی ڤیدیۆ**\n\nتەنها ڤیدیۆ بنێره، من خۆکارانه زیادیدەکەم بۆ بەشی ڤیدیۆکان.\nدەتوانیت #هاشتاگیش لەگەڵ ژێرنووس ببنوسیت.",
        reply_markup=back_keyboard()
    )
    return UPLOAD_VIDEO

async def handle_video_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text == "⬅️ گەڕانەوە":
        await update.message.reply_text("گەڕایتەوە بۆ ڕووکاری سەرەکی.", reply_markup=main_keyboard())
        return ConversationHandler.END

    if update.message.video:
        video_id = update.message.video.file_id
        caption = update.message.caption or ""
        
        add_video(user_id, video_id, caption)
        await update.message.reply_text("✅ ڤیدیۆکەت بە سەرکەوتوویی بڵاوکرایەوە!", reply_markup=main_keyboard())
        return ConversationHandler.END
    else:
        await update.message.reply_text("تکایە ڤیدیۆیەک بنێرە یان دوگمەی '⬅️ گەڕانەوە' دابگرە.", reply_markup=back_keyboard())
        return UPLOAD_VIDEO

# ----------------- Profile & Manage Posts (Custom Share Link & Text) -----------------
async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("تکایە سەرەتا هەژمار دروست بکە.", reply_markup=main_keyboard())
        return

    bot_username = "TikTok_hubbbb_bot"
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=prof_{user[1]}&text=سەیری%20پڕۆفایل%20و%20ڤیدیۆکانم%20بکە%20لە%20تۆڕی%20TikTok_Hub!%20🎬"

    my_vids = get_user_videos(user_id)
    text = (
        f"👤 **{user[2]}**\n"
        f"🔗 @{user[1]}\n\n"
        f"📊 **ئامارەکانی هەژمار:**\n"
        f"🎬 ژمارەی پۆستەکان: {len(my_vids)}\n"
    )
    
    grid_buttons = []
    if not my_vids:
        text += "\n📝 هێشتا هیچ پۆستێکی نییە."
    else:
        text += "\n👇 کاتێک داگریت لەسەر هەریەک لە ژمارەی ڤیدیۆکان نیشان دەدرێت:"
        row = []
        for idx, vid in enumerate(my_vids, 1):
            vid_id = vid[0]
            row.append(InlineKeyboardButton(f"🎥 #{idx}", callback_data=f"show_my_vid_{vid_id}"))
            if len(row) == 3:
                grid_buttons.append(row)
                row = []
        if row:
            grid_buttons.append(row)
            
    grid_buttons.append([InlineKeyboardButton("🔗 📤 شێرکردنی هەژمارەکەم", url=share_url)])
    grid_buttons.append([InlineKeyboardButton("⚠️ 🗑 سڕینەوەی هەژمار", callback_data="confirm_delete_account")])
    
    kb = InlineKeyboardMarkup(grid_buttons)
    await update.message.reply_text(text, reply_markup=kb)

# ----------------- Watch Videos & Next/Prev Sequence -----------------
async def watch_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    videos = get_all_videos()
    if not videos:
        await update.message.reply_text("هیچ ڤیدیۆیەک بڵاو نەکراوەتەوە.", reply_markup=main_keyboard())
        return
    
    context.user_data['current_vid_index'] = 0
    await send_video_card(update, context, is_new_message=True)

async def send_video_card(update, context, is_new_message=False):
    videos = get_all_videos()
    if not videos:
        return

    idx = context.user_data.get('current_vid_index', 0)
    if idx >= len(videos):
        idx = 0
        context.user_data['current_vid_index'] = 0
    elif idx < 0:
        idx = len(videos) - 1
        context.user_data['current_vid_index'] = idx
        
    vid = videos[idx]
    vid_id, owner_id, video_file_id, caption, views = vid
    
    update_views(vid_id)
    views += 1
    
    owner = get_user(owner_id)
    owner_name = owner[2] if owner else "نەنوراو"
    owner_username = owner[1] if owner else "unknown"
    
    likes_count = get_like_count(vid_id)
    
    caption_text = f"👤 {owner_name}\n@{owner_username}\n\n{caption}\n\n👁 {views}"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬆️ ڤیدیۆی پێشتر", callback_data="prev_video")],
        [InlineKeyboardButton("⬇️ ڤیدیۆی نوێ", callback_data="next_video")],
        [InlineKeyboardButton(f"❤️ لایک ({likes_count})", callback_data=f"like_{vid_id}"),
         InlineKeyboardButton("💬 کۆمێنت", callback_data=f"comment_{vid_id}")],
        [InlineKeyboardButton(f"👤 @{owner_username}", callback_data=f"profile_{owner_username}")]
    ])
    
    query = update.callback_query
    if query:
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=video_file_id,
            caption=caption_text,
            reply_markup=kb
        )
        try:
            await query.message.delete()
        except Exception:
            pass
    elif is_new_message:
        await update.message.reply_video(
            video=video_file_id,
            caption=caption_text,
            reply_markup=kb
        )

# ----------------- Callback Handlers -----------------
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if data == "next_video":
        await query.answer()
        context.user_data['current_vid_index'] = context.user_data.get('current_vid_index', 0) + 1
        await send_video_card(update, context)

    elif data == "prev_video":
        await query.answer()
        context.user_data['current_vid_index'] = context.user_data.get('current_vid_index', 0) - 1
        await send_video_card(update, context)

    elif data.startswith("comment_"):
        await query.answer("تایبەتمەندی کۆمێنت بەزووترین کات بەردەست دەبێت!", show_alert=True)

    elif data.startswith("profile_"):
        username = data.split("_")[1]
        await query.answer(f"پڕۆفایلی @{username}", show_alert=True)

    elif data == "confirm_delete_account":
        await query.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ بەڵێ، هەموو شتێک بسڕەوە", callback_data="do_delete_account")],
            [InlineKeyboardButton("❌ نەخێر، پاشگەزبوومەوە", callback_data="cancel_delete_account")]
        ])
        await query.message.reply_text(
            "⚠️ **دڵنیایت لە سڕینەوەی هەژمارەکەت؟**\n\nبە داگرتنی ئەم دوگمەیە هەموو زانیارییەکانت، ڤیدیۆکانت و لایکەکانت بە تەواوی دەسڕدرێنەوە و ناگەڕێنرێنەوە!",
            reply_markup=kb
        )

    elif data == "do_delete_account":
        await query.answer()
        delete_account(user_id)
        await query.message.delete()
        await query.message.reply_text(
            "🗑 **هەژمارەکەت و هەموو داتاکانت بە تەواوی سڕانەوە.**\n\nدەتوانیت هەر کاتێک ویستت سەرلەنوێ هەژمار دروست بکەیتەوە.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("📝 دروستکردنی هەژمار")]], resize_keyboard=True)
        )

    elif data == "cancel_delete_account":
        await query.answer("پاشگەزبوویتەوە.")
        await query.message.delete()

    elif data.startswith("show_my_vid_"):
        await query.answer()
        vid_id = int(data.split("_")[3])
        videos = get_all_videos()
        target_vid = next((v for v in videos if v[0] == vid_id), None)
        if target_vid:
            _, owner_id, video_file_id, caption, views = target_vid
            likes_count = get_like_count(vid_id)
            caption_text = f"🎬 پۆستەکەت\n❤️ {likes_count} لایک  👁 {views}\n\n{caption}"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ دەستکاری", callback_data=f"edit_{vid_id}"),
                 InlineKeyboardButton("🗑 سەرینەوە", callback_data=f"del_{vid_id}")]
            ])
            await query.message.reply_video(video_file_id, caption=caption_text, reply_markup=kb)

    elif data.startswith("like_"):
        vid_id = int(data.split("_")[1])
        is_liked = toggle_like(user_id, vid_id)
        
        if is_liked:
            await query.answer("لایکت کرد ❤️")
        else:
            await query.answer("لایکەکەت لابرایەوە")
            
        videos = get_all_videos()
        target_vid = next((v for v in videos if v[0] == vid_id), None)
        if target_vid:
            _, owner_id, _, caption, views = target_vid
            owner = get_user(owner_id)
            owner_name = owner[2] if owner else "نەنوراو"
            owner_username = owner[1] if owner else "unknown"
            
            likes_count = get_like_count(vid_id)
            caption_text = f"👤 {owner_name}\n@{owner_username}\n\n{caption}\n\n👁 {views}"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬆️ ڤیدیۆی پێشتر", callback_data="prev_video")],
                [InlineKeyboardButton("⬇️ ڤیدیۆی نوێ", callback_data="next_video")],
                [InlineKeyboardButton(f"❤️ لایک ({likes_count})", callback_data=f"like_{vid_id}"),
                 InlineKeyboardButton("💬 کۆمێنت", callback_data=f"comment_{vid_id}")],
                [InlineKeyboardButton(f"👤 @{owner_username}", callback_data=f"profile_{owner_username}")]
            ])
            await query.edit_message_caption(caption=caption_text, reply_markup=kb)

    elif data.startswith("del_"):
        vid_id = int(data.split("_")[1])
        videos = get_all_videos()
        target_vid = next((v for v in videos if v[0] == vid_id), None)
        if target_vid:
            owner_id = target_vid[1]
            if owner_id != user_id:
                await query.answer("❌ تۆ تەنها دەتوانیت پۆستەکانی خۆت بسڕیتەوە!", show_alert=True)
                return
            delete_video(vid_id)
            await query.answer("پۆستەکە سڕایەوە")
            await query.message.delete()
            await query.message.reply_text("✅ پۆستەکە بە سەرکەوتوویی سڕایەوە.")

    elif data.startswith("edit_"):
        vid_id = int(data.split("_")[1])
        videos = get_all_videos()
        target_vid = next((v for v in videos if v[0] == vid_id), None)
        if target_vid:
            owner_id = target_vid[1]
            if owner_id != user_id:
                await query.answer("❌ تۆ تەنها دەتوانیت دەستکاری پۆستەکانی خۆت بکەیت!", show_alert=True)
                return
            await query.answer()
            context.user_data['editing_vid_id'] = vid_id
            await query.message.reply_text("📝 تکایە نوسین یان #هاشتاگی نوێ بۆ ئەم پۆستە بنووسە:", reply_markup=back_keyboard())
            return EDIT_CAPTION

async def save_edited_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ گەڕانەوە":
        await update.message.reply_text("گەڕایتەوە بۆ ڕووکاری سەرەکی.", reply_markup=main_keyboard())
        return ConversationHandler.END

    new_caption = update.message.text
    vid_id = context.user_data.get('editing_vid_id')
    user_id = update.effective_user.id
    
    if vid_id:
        videos = get_all_videos()
        target_vid = next((v for v in videos if v[0] == vid_id), None)
        if target_vid and target_vid[1] == user_id:
            update_caption(vid_id, new_caption)
            await update.message.reply_text("✅ پۆستەکە بە سەرکەوتوویی دەستکاری کرا!", reply_markup=main_keyboard())
        else:
            await update.message.reply_text("❌ بڕگە ڕێگەپێدراو نییە بۆ دەستکاریکردنی ئەم پۆستە.", reply_markup=main_keyboard())
            
    return ConversationHandler.END

# ----------------- Search -----------------
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 ناوی بەکارهێنەر یاخود وشەیەک لە کەپشنی ڤیدیۆ بنووسە (یان #هاشتاگ):",
        reply_markup=back_keyboard()
    )
    return SEARCH_QUERY

async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.message.text
    if q == "⬅️ گەڕانەوە":
        await update.message.reply_text("گەڕایتەوە بۆ ڕووکاری سەرەکی.", reply_markup=main_keyboard())
        return ConversationHandler.END

    videos = get_all_videos()
    results = [v for v in videos if q.lower() in v[3].lower()]
    
    if not results:
        await update.message.reply_text("هیچ نەدۆزرایەوە.", reply_markup=main_keyboard())
    else:
        for vid in results:
            await update.message.reply_video(vid[2], caption=vid[3])
        await update.message.reply_text("ئەنجامەکانی گەڕان 👆", reply_markup=main_keyboard())
    return ConversationHandler.END

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("گەڕایتەوە بۆ ڕووکاری سەرەکی.", reply_markup=main_keyboard())
    return ConversationHandler.END

# ----------------- Main Execution -----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    reg_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 دروستکردنی هەژمار$"), start_registration)],
        states={
            USERNAME: [MessageHandler(filters.TEXT, get_username)],
            NAME: [MessageHandler(filters.TEXT, get_name)],
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ گەڕانەوە$"), go_back)],
    )

    upload_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📩 بڵاوکردنەوەی ڤیدیۆ 🎬$"), upload_start)],
        states={
            UPLOAD_VIDEO: [MessageHandler(filters.VIDEO | filters.TEXT, handle_video_upload)]
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ گەڕانەوە$"), go_back)],
    )

    search_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 گەڕان$"), search_start)],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT, process_search)]
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ گەڕانەوە$"), go_back)],
    )

    edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callbacks, pattern="^edit_")],
        states={
            EDIT_CAPTION: [MessageHandler(filters.TEXT, save_edited_caption)]
        },
        fallbacks=[MessageHandler(filters.Regex("^⬅️ گەڕانەوە$"), go_back)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(reg_handler)
    app.add_handler(upload_handler)
    app.add_handler(search_handler)
    app.add_handler(edit_handler)

    app.add_handler(MessageHandler(filters.Regex("^👤 هەژمارەکەم$"), my_account))
    app.add_handler(MessageHandler(filters.Regex("^🎬 ڤیدیۆکان 🔞$"), watch_videos))
    app.add_handler(MessageHandler(filters.Regex("^⬅️ گەڕانەوە$"), go_back))
    app.add_handler(CallbackQueryHandler(handle_callbacks))

    print("بۆتەکە بە سەرکەوتوویی دەستی بەکارکردن کرد...")
    app.run_polling()

if __name__ == '__main__':
    main()
            
