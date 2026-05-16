from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from app.db.models import Base

# Создаем движок (используем стабильный psycopg)
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Фабрика сессий для crud-операций
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Функция автоматического создания таблиц при старте
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)