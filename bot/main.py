import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from handlers.admin_handlers import register_admin_handlers
from handlers.user_handlers import register_user_handlers

# Bot tokenini o'rnatish
BOT_TOKEN = "5131381239:AAHm0l1BmMt4nIpw3mKBfvOrtK_eZ2pooPc"

async def main():
    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Ma'lumotlar bazasini ishga tushirish
    print("Initializing database...")
    await init_db()
    
    # Handlerlarni ro'yxatga olish
    print("Registering handlers...")
    register_admin_handlers(dp, bot)
    register_user_handlers(dp, bot)
    
    # Botni ishga tushirish
    try:
        print("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        # Botni to'xtatishda resurslarni tozalash
        print("Shutting down bot...")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
