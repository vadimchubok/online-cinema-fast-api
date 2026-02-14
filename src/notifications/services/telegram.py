import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.core.config import settings

logger = logging.getLogger(__name__)


bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


async def send_telegram_message(text: str) -> None:
    """
    Asynchronously send a message to the configured Telegram admin chat using Aiogram.
    """
    try:
        await bot.send_message(chat_id=settings.TELEGRAM_ADMIN_CHAT_ID, text=text)
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
