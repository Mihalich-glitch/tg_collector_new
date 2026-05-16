from datetime import datetime
from sqlalchemy import select
from app.db.models import Message, User, Chat
from app.db.base import async_session_maker

async def get_messages_by_period(start_date: datetime, end_date: datetime):
    async with async_session_maker() as session:
        # Объединяем три таблицы, чтобы вытащить полную информацию
        query = (
            select(Message, User, Chat)
            .join(User, Message.user_id == User.id)
            .join(Chat, Message.chat_id == Chat.id)
            .where(Message.timestamp.between(start_date, end_date))
            .order_by(Message.timestamp.asc())
        )
        result = await session.execute(query)
        # Возвращает список кортежей (Message, User, Chat)
        return result.all()