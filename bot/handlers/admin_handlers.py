from aiogram import types
from aiogram import Router, Bot, Dispatcher
from aiogram.filters import Command
from database.db import add_channel, add_rectorate
from utils.auth import is_admin

router = Router()  # Router yaratish

# /add_channel komandasi handleri
async def add_rectorate_handler(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    args =  message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply("❌ Format: /add_rectorate Nomi tg_id")
        return
    name, tg_id = args[1], args[2]
    await add_rectorate(name, tg_id)
    await message.reply("✅ qo'shildi!")

async def add_channel_handler(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvi
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    args =  message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply("❌ Format: /add_channel Nomi Link")
        return
    name, link = args[1], args[2]
    await add_channel(name, link)
    await message.reply("✅ qo'shildi!")


# Router yordamida handlerlarni ro'yxatga olish
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(add_channel_handler, Command("add_channel"))  # /add_channel komandasini ro'yxatga olish
    router.message.register(add_rectorate_handler, Command("add_rectorate"))  # /add_rectorate komandasini ro'yxatga olish
