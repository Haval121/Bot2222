import asyncio
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8725595567:AAFeQb5xhmJMqZybazVmxDPy2_qR1RshRno"
ADMIN_ID = 8734106005
DELETE_DELAY = 900

URL_REGEX = re.compile(r'https?://\S+|t\.me/\S+|www\.\S+', re.IGNORECASE)

logging.basicConfig(level=logging.INFO)


async def delete_msg(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
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
        file_id = msg.video.file_id
        caption = msg.caption

        await asyncio.sleep(DELETE_DELAY)
        await delete_msg(context.bot, msg.chat
