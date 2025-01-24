from aiogram import types
from aiogram import Router, Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from database.db import add_channel, add_rectorate, get_users, get_rectorate, update_rectorate
from utils.auth import is_admin

router = Router()  # Router yaratish

async def start_admin(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):  # Admin tekshiruvini amalga oshiramiz
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return
    buttons = [
        [types.InlineKeyboardButton(text=f"👥 Foydalanuvchilar", callback_data=f"all_users"),
        types.InlineKeyboardButton(text=f"📢 Telgram kanallar", callback_data=f"all_channels")],
        [types.InlineKeyboardButton(text="🗣 Bo'limlar", callback_data=f"all_department")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text="Quydagilardan birini tanlang", reply_markup=keyboard)

async def admin_start_back(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"👥 Foydalanuvchilar", callback_data=f"all_users"),
        types.InlineKeyboardButton(text=f"📢 Telgram kanallar", callback_data=f"all_channels")],
        [types.InlineKeyboardButton(text="🗣 Bo'limlar", callback_data=f"all_department")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Quydagilardan birini tanlang", reply_markup=keyboard)
    await callback.message.delete()

async def users_all(callback: types.CallbackQuery, page: int = 1):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    users = await get_users()
    if not users:
        button = [[types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday foydalanuvchi mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    users_per_page = 10
    start_index = (page - 1) * users_per_page
    end_index = start_index + users_per_page
    users_to_display = users[start_index:end_index]

    buttons = [
        [types.InlineKeyboardButton(text=f"👤{full_name} - 📞{phone_number} -🆔{telegram_id}", url=f"https://t.me/{username}")]
        for telegram_id, _, username, full_name, phone_number in users_to_display
    ]

    # Sahifalarni ko'rsatish uchun "keyingi" va "oldingi" tugmalari
    buttons.append([
        types.InlineKeyboardButton(text="⬅️", callback_data=f"oldingi_{page-1}" if page > 1 else "oldingi_1"),
        types.InlineKeyboardButton(text="➡️", callback_data=f"keyingi_{page+1}" if end_index < len(users) else f"keyingi_{page}")
    ])

    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text=f"📊Barcha bot foydalanuvchilari- Sahifa {page}", reply_markup=keyboard)
    await callback.message.delete()

@router.callback_query(lambda c: c.data and c.data.startswith('keyingi_'))
async def next_page(callback: types.CallbackQuery):
    page = int(callback.data.split('_')[1])  # keyingi_{page} dan sahifa raqamini olish
    await users_all(callback, page)

@router.callback_query(lambda c: c.data and c.data.startswith('oldingi_'))
async def prev_page(callback: types.CallbackQuery):
    page = int(callback.data.split('_')[1])  # oldingi_{page} dan sahifa raqamini olish
    await users_all(callback, page)


async def all_rectorate(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return
    
    rektoratlar = await get_rectorate()
    if not rektoratlar:
        button = [[types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="back_admin")]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=button)
        await callback.message.answer(text="❌ Hech qanday adminlar mavjud emas", reply_markup=keyboard)
        await callback.message.delete()
        return
    
    buttons = [
        [types.InlineKeyboardButton(text=f"👤 {name} - 🆔 {teg_id}", callback_data="edit_department")]
        for name, teg_id, in rektoratlar
    ]
    buttons.append(
        [types.InlineKeyboardButton(text="🚮 O'chirish", callback_data="delete_departmen"),
        types.InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_department")])
    buttons.append([types.InlineKeyboardButton(text=f"🔙 Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text=f"Barcha adminlar", reply_markup=keyboard)
    await callback.message.delete()


async def edit_rectorate(callback: types.CallbackQuery):
    if not is_admin(callback.message.chat.id):  # Admin tekshiruvi
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return
    departments = await get_rectorate()
    buttons = [
        [types.InlineKeyboardButton(text=f"✏️ {department_name}", callback_data=f"editdepart_{department_name}")]
        for  department_name, teg_id in departments
    ]
    buttons.append([types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Tahrir qilinadigan bo'limni tanlang:", reply_markup=keyboard)
    await callback.message.delete()

async def prompt_edit_department(callback: types.CallbackQuery):
    department_name = callback.data.split("_", 1)[1]
    buttons = [
        [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(
        f"Tahrirlash uchun admin nomi va, telegram idsini yozing\n"
        f"Format:\n`/edit_department {department_name}, Yangi_nomi, Yangi_telegram_id`\n\n"
        f"Masalan:\n`/edit_department {department_name}, YangiNom, Yangitelegramid`",
        parse_mode="Markdown", reply_markup=keyboard
    )
    await callback.answer() 

async def confirm_edit_channel(message: types.Message, command: CommandObject):
    try:
        data = command.args.split(",")
        if len(data) < 3:
            await message.reply("❌ Format: `/edit_department Old_nomi, Yangi_nomi, Yangi_telegram_id`")
            return

        old_name = data[0].strip()
        new_name = data[1].strip()
        new_tg_id = data[2].strip()

        await update_rectorate(old_name, new_name, new_tg_id)
        buttons = [
            [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
            types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_channels")]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"✅ Admin yangilandi:\nEski nomi: {old_name}\nYangi nomi: {new_name}\nYangi link: {new_tg_id}", reply_markup=keyboard)
    except ValueError:
        await message.reply("❌ Xato! Formatni tekshirib qaytadan urinib ko‘ring.")


async def prompt_add_department(callback: types.CallbackQuery):
    buttons = [
        [types.InlineKeyboardButton(text=f"⬆️ Bosh saxifa", callback_data="back_admin"), 
        types.InlineKeyboardButton(text=f"⬅️ Ortga", callback_data="all_department")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(
        f"Tahrirlash uchun admin nomi va, telegram idsini yozing\n"
        f"Format:\n`/add_department Yangi_nomi, Yangi_telegram_id`\n\n"
        f"Masalan:\n`/add_department  YangiNom, Yangitelegramid`",
        parse_mode="Markdown", reply_markup=keyboard
    )
    await callback.answer() 

# /add_departmen komandasi handleri
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
    router.message.register(start_admin, Command('start_admin'))
    router.callback_query.register(
        admin_start_back,
        lambda c: c.data and c.data.startswith('back_admin')
    )
    router.callback_query.register(
        users_all,
        lambda c: c.data and c.data.startswith('all_users')
    )
    router.callback_query.register(
        all_rectorate,
        lambda c: c.data and c.data.startswith('all_department')
    )
    router.callback_query.register(
        edit_rectorate,
        lambda c: c.data and c.data.startswith('edit_department')
    )
    router.callback_query.register(
        prompt_edit_department,
        lambda c: c.data and c.data.startswith('editdepart_')
    )
    router.message.register(confirm_edit_channel, Command("edit_department"))
    
    router.callback_query.register(
        prompt_add_department,
        lambda c: c.data and c.data.startswith('add_department')
    )
    

    router.message.register(add_channel_handler, Command("add_channel"))  # /add_channel komandasini ro'yxatga olish
    router.message.register(add_rectorate_handler, Command("add_department"))  # /add_rectorate komandasini ro'yxatga olish
