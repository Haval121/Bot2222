import asyncio
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8725595567:AAG1lw-AMx0v9EQS_i9fsFPn5QcFi8zHaSc"
ADMIN_ID = 8734106005

DELETE_DELAY = 900
PHOTO_DELETE_DELAY = 10800  # 3 hours

URL_REGEX = re.compile(r'(https?://\S+|t\.me/\S+|www\.\S+|@\w+)', re.IGNORECASE)

logging.basicConfig(level=logging.INFO)


async def delete_msg(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass


async def delete_photo(bot, chat_id, msg_id):
    await asyncio.sleep(PHOTO_DELETE_DELAY)
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

    # 🔗 block links + usernames
    if URL_REGEX.search(text):
        await delete_msg(context.bot, msg.chat_id, msg.message_id)
        return

    # 🤖 block ONLY bot text messages
    if msg.text and msg.from_user and msg.from_user.is_bot:
        await delete_msg(context.bot, msg.chat_id, msg.message_id)
        return

    # 🎥 video
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

    # 🎞 gif / animation
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

    # 🖼 photo
    elif msg.photo:
        asyncio.create_task(
            delete_photo(
                context.bot,
                msg.chat_id,
                msg.message_id
            )
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_polling()


if __name__ == "__main__":
    main()
