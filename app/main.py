import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import MessageReactionUpdated
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.db.base import init_models, async_session_maker
from app.db.models import Message as DBMessage, User as DBUser, Chat as DBChat
from app.handlers.admin import admin_router

# Фикс для корректной работы asyncio в Windows (решает проблему семафоров и прокси)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# 1. ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# Админский роутер должен быть первым, чтобы перехватывать /export
dp.include_router(admin_router)


# 2. ОБРАБОТКА РЕАКЦИЙ
@dp.message_reaction()
async def handle_reaction(reaction: MessageReactionUpdated):
    """Обновляет список реакций у сообщения в базе данных"""
    current_reactions = [r.emoji for r in reaction.new_reaction if r.emoji]
    reactions_str = ", ".join(current_reactions)

    async with async_session_maker() as session:
        try:
            from sqlalchemy import update
            stmt = (
                update(DBMessage)
                .where(DBMessage.message_id == reaction.message_id)
                .where(DBMessage.chat_id == reaction.chat.id)
                .values(reactions=reactions_str)
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(f"✨ Обновлены реакции для сообщения {reaction.message_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления реакций: {e}")


# 3. ОБРАБОТКА СООБЩЕНИЙ И ВЛОЖЕНИЙ
# Фильтр пропускает всё, что не начинается со слеша (не команды)
@dp.message(lambda msg: not (msg.text and msg.text.startswith('/')))
async def handle_everything(message: types.Message):
    """Сохраняет текстовые сообщения и медиафайлы в БД"""
    
    # Проверяем наличие хоть какого-то контента
    is_media = any([message.photo, message.video, message.document, message.voice, message.audio])
    if not (message.text or message.caption or is_media):
        return

    async with async_session_maker() as session:
        try:
            # --- Апсерт Пользователя ---
            stmt_user = pg_insert(DBUser).values(
                id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={'username': message.from_user.username, 'full_name': message.from_user.full_name}
            )
            await session.execute(stmt_user)

            # --- Апсерт Чата ---
            chat_title = message.chat.title or message.chat.full_name or "Личный чат"
            stmt_chat = pg_insert(DBChat).values(
                id=message.chat.id,
                title=chat_title,
                type=message.chat.type
            ).on_conflict_do_update(
                index_elements=['id'],
                set_={'title': chat_title, 'type': message.chat.type}
            )
            await session.execute(stmt_chat)

            # --- Определение типа вложения ---
            attachment_type = None
            attachment_id = None

            if message.photo:
                attachment_type = "photo"
                attachment_id = message.photo[-1].file_id
            elif message.video:
                attachment_type = "video"
                attachment_id = message.video.file_id
            elif message.document:
                attachment_type = "document"
                attachment_id = message.document.file_id
            elif message.voice:
                attachment_type = "voice"
                attachment_id = message.voice.file_id

            # --- Сохранение сообщения ---
            db_msg = DBMessage(
                message_id=message.message_id,
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                text=message.text or message.caption or "",
                timestamp=message.date.replace(tzinfo=None),
                attachment_type=attachment_type,
                attachment_id=attachment_id
            )
            session.add(db_msg)
            await session.commit()
            logger.info(f"✅ Сохранено от {message.from_user.id}: {attachment_type or 'text'}")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            await session.rollback()


# 4. ЗАПУСК БОТА
async def main():
    # Настройка сессии с прокси (твой рабочий адрес)
    proxy_url = "http://127.0.0.1:10801" 
    session = AiohttpSession(proxy=proxy_url)
    
    bot = Bot(token=settings.BOT_TOKEN, session=session)

    # Создаем таблицы в БД, если их еще нет
    # await init_models()
    
    logger.info("🚀 Бот запущен и готов к сбору данных (текст, медиа, реакции)!")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")