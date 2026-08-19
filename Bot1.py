import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from sentence_transformers import SentenceTransformer, util

# ڕێکخستنی لۆگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# بارکردنی مۆدێلی زیرەکی دەستکرد
print("خەریکی بارکردنی مۆدێلی AIـین، تکایە چاوەڕێ بکە...")
ai_model = SentenceTransformer('all-MiniLM-L6-v2')

# داتابەیسە نموونەییەکەی کەناڵ و گروپەکان
channels_db = [
    {"name": "Kurdish Coders", "username": "@KurdishCoders", "about": "گروپێک بۆ فێربوونی پڕۆگرامسازی، پایتۆن و دروستکردنی بۆت"},
    {"name": "English Time", "username": "@EnglishTime", "about": "کەناڵی فێربوونی زمانی ئینگلیزی و قسەکردن بە ئینگلیزی"},
    {"name": "Movie Land", "username": "@MovieLandKurd", "about": "دابەزاندنی فیلم و درامای جیهانی بە ژێرنووسی کوردی"},
    {"name": "Tech News", "username": "@TechNews", "about": "هەواڵی تەکنەلۆژیا، مۆبایل و ئەپڵیکەیشنی نوی"}
]

# ئامادەکردنی ڤێکتەری وەسفەکان
descriptions = [c['about'] for c in channels_db]
channel_embeddings = ai_model.encode(descriptions, convert_to_tensor=True)

# فەرمانی /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سڵاو! من بۆتی دۆزینەوەی پێشکەوتووی کەناڵ و گروپم بە زیرەکی دەستکرد.\n"
        "هەر شتێکت دەوێت، بە وەسف یان ناو باسی بکە تا بۆت بدۆزمەوە!"
    )

# سیستمی گەڕانی زیرەک بەپێی پەیامی بەکارهێنەر
async def search_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    
    # گۆڕینی پرسیاری بەکارهێنەر بۆ ڤێکتەری AI
    query_embedding = ai_model.encode(user_query, convert_to_tensor=True)
    
    # بەراوردکردن بە ڕێگەی Cosine Similarity
    cos_scores = util.cos_sim(query_embedding, channel_embeddings)[0]
    
    best_match_idx = cos_scores.argmax().item()
    best_score = cos_scores[best_match_idx].item()
    
    # گەڕاندنەوەی ئەنجام ئەگەر ڕێژەی گونجانەکە گونجاو بوو
    if best_score > 0.2:
        result = channels_db[best_match_idx]
        response = (
            "🔍 **باشترین کەناڵ/گروپ کە لەگەڵ داواکارییەکەت یەکدەگرێت:**\n\n"
            f"📌 **ناو:** {result['name']}\n"
            f"🔗 **یۆزەرتاگ:** {result['username']}\n"
            f"📝 **وەسف:** {result['about']}"
        )
    else:
        response = "ببوورە، هیچ کەناڵێک کە لەگەڵ داواکارییەکەت بگونجێت نەدۆزرایەوە."
        
    await update.message.reply_text(response, parse_mode="Markdown")

if __name__ == '__main__':
    # تووکنەکەی تۆ لەم بۆتەدا جێگیر کراوە
    application = ApplicationBuilder().token("8627963382:AAFI73W5CkvhhxRA2OP7SHPRCjwCEVdHKWg").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_channels))
    
    print("بۆتەکە بە سەرکەوتوویی دەستی بە کار کرد!")
    application.run_polling()
