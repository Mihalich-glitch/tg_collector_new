from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .models import Base, User, Chat, Message
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Создание таблиц при запуске
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Функция сохранения любого сообщения
async def save_telegram_message(session, message):
    # 1. Обработка пользователя
    user = await session.get(User, message.from_user.id)
    if not user:
        user = User(id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name)
        session.add(user)

    # 2. Обработка чата
    chat = await session.get(Chat, message.chat.id)
    if not chat:
        chat = Chat(id=message.chat.id, title=message.chat.title or "Private", type=message.chat.type)
        session.add(chat)

    # 3. Сохранение сообщения
    new_msg = Message(
        message_id=message.message_id,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        text=message.text or message.caption or "",
        timestamp=message.date.replace(tzinfo=None) # Убираем таймзону для SQLite
    )
    session.add(new_msg)
    await session.commit()