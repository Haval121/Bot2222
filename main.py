import asyncio
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8725595567:AAGAknpTVYp6ipfXxadnWsGpKnCnRRU3z5c"
ADMIN_ID = 8734106005
DELETE_DELAY = 360

URL_REGEX = re.compile(r'(https?://\S+|t\.me/\S+|www\.\S+|@\w+)', re.IGNORECASE)

logging.basicConfig(level=logging.INFO)


async def delete_msg(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass


async def process_media(bot, chat_id, msg_id, file_id, caption, is_video=True):
    await asyncio.sleep(DELETE_DELAY)

    await delete_msg(bot, chat_id, msg_id)

    try:
        if is_video:
            await bot.send_video(ADMIN_ID, video=file_id, caption=caption)
        else:
            await bot.send_animation(ADMIN_ID, animation=file_id, caption=caption)
    except:
        pass


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = msg.text or msg.caption or ""

    if URL_REGEX.search(text):
        await delete_msg(context.bot, msg.chat_id, msg.message_id)
        return

    if msg.video:
        asyncio.create_task(
            process_media(
                context.bot,
                msg.chat_id,
                msg.message_id,
                msg.video.file_id,
                msg.caption,
                True
            )
        )

    elif msg.animation:
        asyncio.create_task(
            process_media(
                context.bot,
                msg.chat_id,
                msg.message_id,
                msg.animation.file_id,
                msg.caption,
                False
            )
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_polling()


if __name__ == "__main__":
    main()
