import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

TOKEN = "8667887809:AAE8BpyPP9ehPEs0czgimcLiryYXHgryZYw"
# فەرهەنگێک بۆ هەڵگرتنی لۆگۆی هەر بەکارهێنەرێک
user_logos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("بەخێر بێن! سەرەتا تکایە ئەو وێنەیەت بنێرە کە دەتەوێت ببێت بە لۆگۆ.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    file_path = f"logo_{update.message.from_user.id}.png"
    await photo_file.download_to_drive(file_path)
    user_logos[update.message.from_user.id] = file_path
    await update.message.reply_text("لۆگۆکە هەڵگیرا! ئێستا ڤیدیۆکەت بنێرە.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_logos:
        await update.message.reply_text("تکایە سەرەتا وێنەی لۆگۆکە بنێرە.")
        return

    status = await update.message.reply_text("⏳ خەریکم لۆگۆکە دەخەمە سەری...")
    
    video_file = await update.message.video.get_file()
    input_vid = f"in_{user_id}.mp4"
    output_vid = f"out_{user_id}.mp4"
    await video_file.download_to_drive(input_vid)

    try:
        clip = VideoFileClip(input_vid)
        logo = ImageClip(user_logos[user_id]).set_duration(clip.duration)
        
        # قەبارە و شوێن (چەپی سەرەوە)
        logo = logo.resize(height=clip.h * 0.1).set_position(("left", "top"))
        
        final = CompositeVideoClip([clip, logo])
        final.write_videofile(output_vid, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
        
        await update.message.reply_video(video=open(output_vid, 'rb'), caption="ئەمەش ڤیدیۆکەت بە لۆگۆوە!")
        
        clip.close()
        final.close()
    except Exception as e:
        await update.message.reply_text(f"هەڵەیەک ڕوویدا: {e}")
    finally:
        if os.path.exists(input_vid): os.remove(input_vid)
        if os.path.exists(output_vid): os.remove(output_vid)
        await status.delete()

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.run_polling()
    
