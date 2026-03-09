"""
🚌 Toshkent — Moskva Avtobus Bot
Main entry point. Registers all handlers and starts polling.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import user, admin, groups

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.error(
            "❌ BOT_TOKEN topilmadi!\n"
            ".env faylida BOT_TOKEN ni to'ldiring.\n"
            "Tokenni @BotFather dan olishingiz mumkin."
        )
        return

    # Initialize bot with HTML parse mode
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize dispatcher with memory storage for FSM
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers (order matters: admin before user for command priority)
    dp.include_router(admin.router)
    dp.include_router(groups.router)
    dp.include_router(user.router)

    logger.info("🚌 Bot ishga tushdi!")

    # Start the background broadcast worker
    from scheduler import auto_broadcast_worker
    worker_task = asyncio.create_task(auto_broadcast_worker(bot))

    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=[
            "message",
            "callback_query",
            "my_chat_member",
        ])
    finally:
        worker_task.cancel()
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
