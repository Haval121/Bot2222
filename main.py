import asyncio
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8725595567:AAFeQb5xhmJMqZybazVmxDPy2_qR1RshRno"

DELETE_DELAY = 120
RESEND_DELAY = 300

URL_REGEX = re.compile(r'https?://\S+|t\.me/\S+|www\.\S+', re.IGNORECASE)

logging.basicConfig(level=logging.INFO)

videos = []


async def delete_msg(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass


async def cycle(bot, chat_id):
    while True:

        await asyncio.sleep(DELETE_DELAY)

        for v in videos:
            await delete_msg(bot, chat_id, v["msg_id"])

        await asyncio.sleep(RESEND_DELAY)

        new_videos = []

        tasks = [
            bot.send_video(
                chat_id,
                video=v["file_id"],
                caption=v["caption"]
            )
            for v in videos
        ]

        sent_msgs = await asyncio.gather(*tasks)

        for i, sent in enumerate(sent_msgs):
            new_videos.append({
                "msg_id": sent.message_id,
                "file_id": videos[i]["file_id"],
                "caption": videos[i]["caption"]
            })

        videos.clear()
        videos.extend(new_videos)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = msg.text or msg.caption or ""

    if URL_REGEX.search(text):
        await delete_msg(context.bot, msg.chat_id, msg.message_id)
        return

    if msg.video:
        videos.append({
            "msg_id": msg.message_id,
            "file_id": msg.video.file_id,
            "caption": msg.caption
        })

        if len(videos) == 1:
            asyncio.create_task(cycle(context.bot, msg.chat_id))


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_polling()


if __name__ == "__main__":
    main()
