import os
import sys
import logging
import asyncio
from threading import Thread
from flask import Flask, request, Response
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Update

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, PORT
from handlers.commands import router as commands_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
flask_app = Flask(__name__)

# Bot & Dispatcher
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
dp.include_router(commands_router)


def init_bot():
    """Initialize bot and set webhook"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _init():
        try:
            await bot.set_webhook(
                url=WEBHOOK_URL + WEBHOOK_PATH,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook set successfully: {WEBHOOK_URL + WEBHOOK_PATH}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
    
    loop.run_until_complete(_init())
    loop.close()


def run_webhook_server():
    """Run Flask webhook server in a thread"""
    flask_app.run(host="0.0.0.0", port=PORT, threaded=True)


@flask_app.route("/", methods=["GET"])
def index():
    return """
    <html dir="rtl">
    <head><title>بوت التحميل المتكامل</title></head>
    <body style="text-align:center; font-family: Arial; padding: 50px;">
        <h1>✅ البوت يعمل بنجاح!</h1>
        <p>بوت التحميل المتكامل - يوتيوب، إنستغرام، تيك توك</p>
    </body>
    </html>
    """


@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        update_data = request.get_json(force=True)
        
        if not update_data:
            return Response(status=400)
        
        update = Update(**update_data)
        
        # Create new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(dp.feed_update(bot=bot, update=update))
        finally:
            loop.close()
        
        return Response(status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status=500)


@flask_app.route("/set-webhook", methods=["GET"])
def setup_webhook():
    """Manual webhook setup endpoint"""
    try:
        init_bot()
        return "✅ Webhook set successfully!"
    except Exception as e:
        return f"❌ Error: {str(e)}", 500


@flask_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "bot": "running"}, 200


async def run_polling():
    """Run bot in polling mode (for local development)"""
    # Delete webhook first
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting polling mode...")
    await dp.start_polling(bot)


def main_polling():
    """Main entry for polling mode"""
    asyncio.run(run_polling())


def main_webhook():
    """Main entry for webhook mode"""
    # Set webhook in a separate thread
    init_bot()
    
    # Start Flask server
    logger.info(f"Starting webhook server on port {PORT}...")
    flask_app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "polling":
        # Polling mode for local development
        main_polling()
    else:
        # Webhook mode for production
        main_webhook()
