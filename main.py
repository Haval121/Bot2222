import asyncio
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

VIDEO_DELETE_DELAY = 2 * 60
VIDEO_RESEND_DELAY = 40 * 60

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def delete_message_safe(bot, chat_id, message_id):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.warning(f"Failed to delete message {message_id}: {e}")


async def video_cycle(bot, chat_id, file_id, caption):
    while True:
        await asyncio.sleep(VIDEO_RESEND_DELAY)

        try:
            sent = await bot.send_video(chat_id=chat_id, video=file_id, caption=caption)
            logger.info(f"Resent video to chat {chat_id}, message_id={sent.message_id}")
        except Exception as e:
            logger.warning(f"Failed to resend video to chat {chat_id}: {e}")
            continue

        await asyncio.sleep(VIDEO_DELETE_DELAY)
        await delete_message_safe(bot, chat_id, sent.message_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = msg.chat_id
    message_id = msg.message_id

    if msg.video or msg.animation or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith("video/")):
        file_id = (
            msg.video.file_id if msg.video else
            msg.animation.file_id if msg.animation else
            msg.document.file_id
        )
        caption = msg.caption

        logger.info(f"Video received in chat {chat_id}, deleting in 2 min then cycling every 40 min")

        await asyncio.sleep(VIDEO_DELETE_DELAY)
        await delete_message_safe(context.bot, chat_id, message_id)

        asyncio.create_task(video_cycle(context.bot, chat_id, file_id, caption))


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("Bot started successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()
