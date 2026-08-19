import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from rapidfuzz import fuzz

# ڕێکخستنی لۆگینگ بۆ ئەوەی لە لۆگی ڕەیلوەی کێشەکان ببینیت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# داتابەیسێکی فراوان کە نموونەی جۆراوجۆری تێدایە (دەتوانیت هەرچەندت دەوێت زیادی بکەیت)
channels_db = [
    {"name": "Mhrambazakan Group", "username": "@Mhrambazakan", "about": "گروپی سەرەکی mhrambazakan"},
    {"name": "Mhrambaz One", "username": "@Mhrambaz1", "about": "کەناڵی تایبەتی mhrambaz1"},
    {"name": "Maharmbaz Two", "username": "@Maharmbaz2", "about": "گروپی maharmbaz2"},
    {"name": "Mhrambazakan VIP", "username": "@Mhrambazakan1", "about": "تایبەت بە mhrambazakan1"},
    {"name": "Mhrambazakan Pro", "username": "@Mhrambazakan12", "about": "گروپی mhrambazakan12"},
    {"name": "Mhrambazakann Chat", "username": "@Mhrambazakann", "about": "گفتوگۆی mhrambazakann"},
    {"name": "Kurdish Coders", "username": "@KurdishCoders", "about": "گروپێک بۆ فێربوونی پڕۆگرامسازی و پایتۆن"},
    {"name": "English Time", "username": "@EnglishTime", "about": "کەناڵی فێربوونی زمانی ئینگلیزی"},
    {"name": "Movie Land", "username": "@MovieLandKurd", "about": "دابەزاندنی فیلم و درامای جیهانی"}
]

# فەرمانی /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سڵاو! ئێستا هەر ناوێک یان وشەیەک دەتەوێت بنووسە، ڕاستەوخۆ بەدوایدا دەگەڕێم و نزیکترین ئەنجامەکانت بۆ دەهێنم."
    )

# سیستمی گەڕانی گشتی و کراوە بە پشتبەستن بە Fuzzy Matching
async def search_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    
    matched_results = []
    
    for channel in channels_db:
        # پشکنینی لەیەکچوون لەگەڵ یۆزەرتەگ، ناو، یان وەسف
        score_username = fuzz.partial_ratio(user_query.lower(), channel['username'].lower())
        score_name = fuzz.partial_ratio(user_query.lower(), channel['name'].lower())
        score_about = fuzz.partial_ratio(user_query.lower(), channel['about'].lower())
        
        # ئەگەر لە هەر یەکێکیاندا ڕێژەی نزیکی لە 40% زیاتر بوو
        if score_username > 40 or score_name > 40 or score_about > 40:
            if channel not in matched_results:
                matched_results.append(channel)
    
    # ناردنی ئەنجامەکان بۆ بەکارهێنەر
    if matched_results:
        response = f"🔍 **ئەنجامی گەڕان بۆ ('{user_query}'):**\n\n"
        for res in matched_results:
            response += f"📌 **ناو:** {res['name']}\n🔗 **لینک/یۆزەرتاگ:** {res['username']}\n📝 **وەسف:** {res['about']}\n\n"
    else:
        response = f"ببوورە، هیچ ئەنجامێک بۆ '{user_query}' نەدۆزرایەوە."
        
    await update.message.reply_text(response, parse_mode="Markdown")

if __name__ == '__main__':
    # تووکنەکەت ڕاستەوخۆ لێرە جێگیر کراوە
    TOKEN = "8670204681:AAF-qUDAj3aFWPVb7oXDugyI4onog-tlQTA"
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_channels))
    
    print("بۆتەکە لەسەر سێرڤەر دەستی بە کار کرد!")
    application.run_polling()
    
