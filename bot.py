from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

TOKEN = "8667887809:AAE8BpyPP9ehPEs0czgimcLiryYXHgryZYw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("بەخێر بێن! ڤیدیۆیەک بنێرە تا لەگەڵ لینکەکەت بۆ بنێرمەوە.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_text = (
        "بینی ڤیدیۆی زیاتر 👇\n"
        "[سەردانی کەناڵ](https://t.me/+1NHBFRGHW_oyOWE6)"
    )
    
    # ناردنی ڤیدیۆکە وەک خۆی لەگەڵ لینکەکە
    await update.message.reply_video(
        video=update.message.video.file_id,
        caption=caption_text,
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    application.run_polling()
    
