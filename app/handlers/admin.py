import csv
import io
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message as TGMessage, BufferedInputFile

from app.db.crud import get_messages_by_period
from app.core.config import settings

admin_router = Router()

@admin_router.message(Command("export"))
async def export_data(message: TGMessage):
    if message.from_user.id != int(settings.ADMIN_ID):
        await message.answer("🛑 У вас нет прав для выполнения этой команды.")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("⚠️ Формат: `/export ДД.ММ.ГГГГ ДД.ММ.ГГГГ`")
        return

    try:
        start_date = datetime.strptime(args[1], "%d.%m.%Y")
        end_date = datetime.strptime(args[2], "%d.%m.%Y").replace(hour=23, minute=59, second=59)
    except ValueError:
        await message.answer("❌ Ошибка формата даты. Используйте точки: 15.05.2026")
        return

    await message.answer(f"⏳ Сбор данных за период с {args[1]} по {args[2]}...")

    # Получаем связанные данные
    rows = await get_messages_by_period(start_date, end_date)
    
    if not rows:
        await message.answer("📭 Сообщений не найдено.")
        return

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Теперь заголовки стали информативными для менеджера!
    writer.writerow([
        'ID', 'Чат', 'Имя', 'Текст', 'Вложение', 'Реакции', 'Дата'
    ])

    for msg, user, chat in rows:
        writer.writerow([
            msg.message_id,
            chat.title,
            user.full_name,
            msg.text,
            msg.attachment_type or "нет",
            msg.reactions or "",
            msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    file_bytes = output.getvalue().encode('utf-8-sig')
    
    document = BufferedInputFile(file_bytes, filename=f"report_{args[1]}_{args[2]}.csv")
    await message.answer_document(document=document, caption=f"📋 Выгрузка готова. Строк: {len(rows)}")