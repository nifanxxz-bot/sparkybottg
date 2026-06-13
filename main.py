import asyncio
from config import bot, dp, init_db
import handlers.menu
import handlers.admin
import handlers.games

async def main():
    # Создаем таблицы базы данных, если их нет
    init_db()
    
    # Подключаем модули (роутеры) по очереди
    dp.include_router(handlers.menu.router)
    dp.include_router(handlers.admin.router)
    dp.include_router(handlers.games.router)
    
    print("🚀 Модульный GRAM BOT успешно запущен! Все части работают как единое целое.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
