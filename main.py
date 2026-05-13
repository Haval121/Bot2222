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


async def delete_msg(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except:
        pass


async def resend_loop(bot, chat_id, file_id, caption):
    while True:
        await asyncio.sleep(RESEND_DELAY)

        sent = await bot.send_video(
            chat_id=chat_id,
            video=file_id,
            caption=caption
        )

        await asyncio.sleep(DELETE_DELAY)
        await delete_msg(bot, chat_id, sent.message_id)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text = msg.text or msg.caption or ""

    if URL_REGEX.search(text):
        await delete_msg(context.bot, msg.chat_id, msg.message_id)
        return

    if msg.video:
        file_id = msg.video.file_id
        caption = msg.caption

        await asyncio.sleep(DELETE_DELAY)
        await delete_msg(context.bot, msg.chat_id, msg.message_id)

        asyncio.create_task(
            resend_loop(
                context.bot,
                msg.chat_id,
                file_id,
                caption
            )
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle))
    app.run_polling()


if __name__ == "__main__":
    main()
