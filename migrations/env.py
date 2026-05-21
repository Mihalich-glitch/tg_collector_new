import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- НАСТРОЙКА ПУТЕЙ И ИМПОРТ МОДЕЛЕЙ ---
# Высчитываем корень проекта (tg_collector3) относительно этого файла
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Явно импортируем Base и все модели, чтобы Alembic их увидел!
from app.db.models import Base, User, Chat, Message
from app.core.config import settings
# ----------------------------------------

# Объект конфигурации Alembic, предоставляющий доступ к значениям в alembic.ini
config = context.config

# Настраиваем логирование из файла alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем метаданные для поддержки --autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме (генерация SQL-скриптов без подключения)."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Вспомогательная синхронная функция выполнения миграций внутри транзакции."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме (реальное применение изменений к БД)."""
    
    # Динамически подменяем URL подключения данными из нашего .env
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())