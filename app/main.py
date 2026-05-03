import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession

from app.core.config import settings
from app.db.base import init_models, async_session, save_telegram_message

# Фикс для Windows + VPN
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

@dp.message()
async def handle_everything(message: types.Message):
    logger.info(f"📩 Новое сообщение от {message.from_user.full_name}")
    async with async_session() as session:
        try:
            await save_telegram_message(session, message)
            logger.info("✅ Успешно сохранено в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")

async def main():
    # Настройка ПРОКСИ (Замени порт 10801 на порт своего VPN!)
    proxy_url = "http://127.0.0.1:10801" 
    session = AiohttpSession(proxy=proxy_url)
    
    bot = Bot(token=settings.BOT_TOKEN, session=session)

    await init_models()
    logger.info("🚀 Бот запущен и готов к работе!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())