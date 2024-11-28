from aiogram import types, Router, Dispatcher, Bot
from aiogram.filters import Command
from database.db import get_channels, add_users, get_rectorate
from utils.membership import check_membership

router = Router()  # Router yaratish

# /start komanda handleri
async def start_handler(message: types.Message, bot: Bot):

    await message.answer(
        "Assalomu alaykum! Botimizga xush kelibsiz.\nIltimos, ismingiz va familiyangizni yuboring:"
    )

# Foydalanuvchi ism va familiyasini qayta ishlash
async def name_handler(message: types.Message):
    telegram_id = message.chat.id
    full_name = message.text.strip()  # Foydalanuvchi yuborgan ism va familiya
    first_name = message.chat.first_name if message.chat.first_name else ' '
    username = message.chat.username if message.chat.username else ' '
    print(telegram_id)
    # Bazaga saqlash
    try:
        await add_users(telegram_id, first_name, username, full_name)
        await message.answer("✅ Ma'lumotlaringiz saqlandi. Botdan foydalanishni boshlashingiz mumkin!")
    except Exception as e:
        await message.answer(f"❌ Ma'lumotlarni saqlashda xatolik yuz berdi: {e}")

# Router yordamida handlerlarni ro'yxatga olish
def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(start_handler, Command("start"))  # /start komandasi uchun handler
    router.message.register(name_handler)  # Foydalanuvchi ismi uchun umumiy handler
