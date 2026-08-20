import subprocess
import sys

# ئەم بەشە کتێبخانەکان دڵنیا دەکاتەوە کە دامەزراون
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import aiogram
    import moviepy
    import dotenv
except ImportError:
    install("aiogram")
    install("moviepy")
    install("python-dotenv")

import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from dotenv import load_dotenv

# پاشان کۆدەکەی پێشوو...
BOT_TOKEN = "8667887809:AAE8BpyPP9ehPEs0czgimcLiryYXHgryZYw"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("بەخێر بێن! ڤیدیۆیەک بنێرە تا لۆگۆی کەناڵەکەت بخەمە سەری.")

@dp.message(F.video)
async def process_video(message: Message):
    status_msg = await message.answer("⏳ خەریکم ڤیدیۆکە پرۆسێس دەکەم...")
    
    video_file = await bot.get_file(message.video.file_id)
    input_video_path = f"in_{message.from_user.id}.mp4"
    output_video_path = f"out_{message.from_user.id}.mp4"
    logo_path = "logo.png"
    
    await bot.download_file(video_file.file_path, input_video_path)
    
    try:
        clip = VideoFileClip(input_video_path)
        logo = ImageClip(logo_path).set_duration(clip.duration)
        logo = logo.resize(width=clip.w * 0.20)
        logo = logo.set_position(("right", "bottom"))
        
        final_clip = CompositeVideoClip([clip, logo])
        
        final_clip.write_videofile(
            output_video_path, codec="libx264", audio_codec="aac", 
            fps=24, preset="ultrafast", logger=None
        )
        
        caption = "بینی ڤیدیۆی زیاتر 👇\n[بۆچوون و سەردانیکردنی کەناڵ](https://t.me/+1NHBFRGHW_oyOWE6)"
        
        await message.answer_video(
            video=FSInputFile(output_video_path),
            caption=caption,
            parse_mode="Markdown"
        )
        
        clip.close()
        final_clip.close()
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ هەڵەیەک ڕوویدا: {str(e)}")
    finally:
        if os.path.exists(input_video_path): os.remove(input_video_path)
        if os.path.exists(output_video_path): os.remove(output_video_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
