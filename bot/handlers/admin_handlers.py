from aiogram import types
from aiogram import Router, Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import (
    add_channel, delete_channel, update_channel, get_channels,  get_users,
    add_rectorate, delete_rectorate, update_rectorate, get_rectorate,
    add_request_type, delete_request_type, update_request_type, get_request_types,
    add_admin, delete_admin, get_admins, get_user_by_telegram_id, delete_user, get_rectorate_one,
    is_super_admin, set_request_route, get_all_admin_responses,
    get_all_murojaatlar, get_response_status_by_murojaat_id
)
from utils.auth import is_admin

router = Router()  # Router yaratish

async def start_admin(message: types.Message, bot: Bot):
    if not await is_admin(message.from_user.id):
        await message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        return

    await message.answer("👮 Admin panelga xush kelibsiz!")

    buttons = [
        [types.InlineKeyboardButton(text=f"👮 Adminlar", callback_data=f"list_admins"),
         types.InlineKeyboardButton(text=f"👥 Foydalanuvchilar", callback_data=f"list_users")],
        [types.InlineKeyboardButton(text=f"📢 Telgram kanallar", callback_data=f"list_channels"),
        types.InlineKeyboardButton(text="🧑‍💻 Xodim", callback_data=f"list_rectorate")],
        [types.InlineKeyboardButton(text=f"📝 Ariza turlari", callback_data=f"list_request_types"),
         types.InlineKeyboardButton(text="📊 Monitoring", callback_data="monitoring")],
        [types.InlineKeyboardButton(text="🔗 Bog‘lash: Murojaat -> Xodim", callback_data="link_request")]
         
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Quydagilardan birini tanlang:", reply_markup=keyboard)

async def admin_start_back(callback: types.CallbackQuery):
    if not await is_admin(callback.message.chat.id):
        await callback.message.reply("❌ Ushbu buyruq faqat adminlar uchun!")
        await callback.message.delete()
        return

    buttons = [
        [types.InlineKeyboardButton(text=f"👮 Adminlar", callback_data=f"list_admins"),
         types.InlineKeyboardButton(text=f"👥 Foydalanuvchilar", callback_data=f"list_users")],
        [types.InlineKeyboardButton(text=f"📢 Telgram kanallar", callback_data=f"list_channels"),
        types.InlineKeyboardButton(text="🧑‍💻 Xodim", callback_data=f"list_rectorate")],
        [types.InlineKeyboardButton(text=f"📝 Ariza turlari", callback_data=f"list_request_types"),
         types.InlineKeyboardButton(text="📊 Monitoring", callback_data="monitoring")],
        [types.InlineKeyboardButton(text="🔗 Bog‘lash: Murojaat -> Xodim", callback_data="link_request")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(text="Quydagilardan birini tanlang", reply_markup=keyboard)
    await callback.message.delete()


class AdminStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_tg_id = State()
    waiting_for_is_super = State()
    waiting_for_request_type = State()
    waiting_for_rectorate_select = State()

# 👥 Barcha adminlar ro'yxati
@router.callback_query(lambda c: c.data == "list_admins")
async def list_admins_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")

    admins = await get_admins()
    if not admins:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Admin qo‘shish", callback_data="add_admin")],
            [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")]
        ])
        return await callback.message.answer("🚫 Hech qanday admin mavjud emas.", reply_markup=keyboard)

    buttons = [
        [types.InlineKeyboardButton(text=f"👤 {full_name}", callback_data=f"get_admin:{tg_id}")]
        for tg_id, full_name, _ in admins
    ]
    buttons.append([types.InlineKeyboardButton(text="➕ Admin qo‘shish", callback_data="add_admin")])
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.delete()
    await callback.message.answer("👥 Adminlar ro'yxati:", reply_markup=keyboard)

# 👤 Adminni ko‘rish
@router.callback_query(lambda c: c.data.startswith("get_admin:"))
async def get_admin_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")

    tg_id = int(callback.data.split(":")[1])
    admins = await get_admins()
    admin = next((a for a in admins if a[0] == tg_id), None)
    if not admin:
        return await callback.message.answer("❌ Admin topilmadi.")

    _, full_name, is_super = admin if len(admin) == 3 else (*admin, 0)
    status = "👑 Super Admin" if is_super else "👮 Oddiy Admin"

    text = f"👤 *Admin:*\n\n▪️ Ism: {full_name}\n▪️ Telegram ID: `{tg_id}`\n▪️ Status: {status}"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_admin:{tg_id}")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_admins")]
    ])
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("is_super:"))
async def confirm_is_super(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_name = data['full_name']
    tg_id = data['tg_id']
    is_super = int(callback.data.split(":")[1])

    await add_admin(tg_id, full_name, is_super)
    await callback.message.delete()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_admins")]
    ])
    await callback.message.delete()
    await callback.message.answer("✅ Admin muvaffaqiyatli qo‘shildi!", reply_markup=keyboard)
    await state.clear()


# ➕ Admin qo‘shish boshlanishi
@router.callback_query(lambda c: c.data == "add_admin")
async def add_admin_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")
    await callback.message.delete()
    await callback.message.answer("✏️ Admin to‘liq ismini kiriting:")
    await state.set_state(AdminStates.waiting_for_full_name)

@router.message(AdminStates.waiting_for_full_name)
async def add_admin_full_name(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo‘q.")
    await state.update_data(full_name=message.text.strip())
    await message.answer("📥 Admin Telegram ID sini kiriting:")
    await state.set_state(AdminStates.waiting_for_tg_id)

@router.message(AdminStates.waiting_for_tg_id)
async def add_admin_tg_id(message: types.Message, state: FSMContext):
    try:
        tg_id = int(message.text.strip())
        await state.update_data(tg_id=tg_id)
        buttons = [
            [types.InlineKeyboardButton(text="✅ Ha", callback_data="is_super:1")],
            [types.InlineKeyboardButton(text="❌ Yo‘q", callback_data="is_super:0")]
        ]
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("📌 Bu admin Super admin bo‘ladimi?", reply_markup=kb)
        await state.set_state(AdminStates.waiting_for_is_super)
    except:
        await message.answer("❌ Telegram ID noto‘g‘ri formatda.")

# 🗑 Adminni o‘chirish
@router.callback_query(lambda c: c.data.startswith("delete_admin:"))
async def delete_admin_callback(callback: types.CallbackQuery):
    # if not await is_admin(callback.from_user.id):
    #     return await callback.message.reply("❌ Ruxsat yo‘q.")
    tg_id = int(callback.data.split(":")[1])
    await delete_admin(tg_id)
    await callback.message.delete()
    await callback.message.answer("✅ Admin o‘chirildi.")
    await list_admins_callback(callback)

    
# 🔗 Super admin murojaat turini XODIMga bog‘laydi
@router.callback_query(lambda c: c.data == "link_request")
async def start_linking(callback: types.CallbackQuery, state: FSMContext):
    if not await is_super_admin(callback.from_user.id):
        return await callback.message.reply("❌ Faqat super admin kirishi mumkin.")

    request_types = await get_request_types()
    if not request_types:
        return await callback.message.answer("❌ Murojaat turlari topilmadi.")

    buttons = [
        [types.InlineKeyboardButton(text=name[0], callback_data=f"select_request:{name[0]}")]
        for name in request_types
    ]
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.delete()
    await callback.message.answer("🔗 Qaysi murojaat turiga XODIM bog‘lamoqchisiz:", reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("select_request:"))
async def select_request_type(callback: types.CallbackQuery, state: FSMContext):
    req_type = callback.data.split(":")[1]
    await state.update_data(request_type=req_type)

    rectorates = await get_rectorate()
    if not rectorates:
        return await callback.message.answer("❌ Xodimlar mavjud emas.")

    buttons = [
        [types.InlineKeyboardButton(text=name, callback_data=f"select_rectorate:{tg_id}")]
        for name, tg_id in rectorates
    ]
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="link_request")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.delete()
    await callback.message.answer(f"✅ {req_type} murojaatini qaysi XODIMga bog‘laysiz:", reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("select_rectorate:"))
async def confirm_link(callback: types.CallbackQuery, state: FSMContext):
    tg_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    request_type = data['request_type']
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")],
    ])
    await set_request_route(request_type, tg_id)
    await callback.message.edit_text(f"✅ {request_type} turi {tg_id} ID xodimga bog‘landi.", reply_markup=keyboard)
    await state.clear()

# Holatni saqlash uchun
user_page_state = {}

# 📋 Foydalanuvchilar ro'yxatini sahifalab ko'rsatish
@router.callback_query(lambda c: c.data == "list_users")
async def cmd_list_users(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    user_page_state[callback.from_user.id] = 1
    await show_users_page(callback.message, callback.from_user.id, page=1)

@router.callback_query(lambda c: c.data.startswith("next_user_page") or c.data.startswith("prev_user_page"))
async def paginate_users_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_page = user_page_state.get(user_id, 1)

    if callback.data.startswith("next_user_page"):
        current_page += 1
    elif callback.data.startswith("prev_user_page") and current_page > 1:
        current_page -= 1

    user_page_state[user_id] = current_page
    await callback.message.delete()
    await show_users_page(callback.message, user_id, current_page)

async def show_users_page(message_obj: types.Message, user_id: int, page: int = 1):
    users = await get_users()
    if not users:
        return await message_obj.answer("🚫 Foydalanuvchilar mavjud emas.")

    users_per_page = 10
    start_index = (page - 1) * users_per_page
    end_index = start_index + users_per_page
    users_to_display = users[start_index:end_index]

    text = f"<b>📋 Foydalanuvchilar ro‘yxati</b> (sahifa {page}):\n\n"
    buttons = []

    for i, (telegram_id, first_name, username, full_name, phone) in enumerate(users_to_display, start=start_index + 1):
        text += f"{i}. {full_name or 'Noma\'lum'} | @{username or 'yo‘q'} | {phone or '📵'} | ID: <code>{telegram_id}</code>\n"
        buttons.append([
            types.InlineKeyboardButton(text=f"👤 {full_name or 'Foydalanuvchi'}", callback_data=f"get_user:{telegram_id}")
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Oldingi", callback_data="prev_user_page"))
    if end_index < len(users):
        nav_buttons.append(types.InlineKeyboardButton(text="➡️ Keyingi", callback_data="next_user_page"))

    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message_obj.delete()
    await message_obj.answer(text, reply_markup=keyboard, parse_mode="HTML")

# 👤 Bitta foydalanuvchi ma'lumotini olish
@router.callback_query(lambda c: c.data.startswith("get_user:"))
async def get_user_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")

    telegram_id = int(callback.data.split(":")[1])
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return await callback.message.answer("❌ Foydalanuvchi topilmadi.")

    first_name, username, full_name, phone = user
    text = (
        f"<b>👤 Foydalanuvchi ma'lumotlari:</b>\n"
        f"▪️ Ism: {first_name}\n"
        f"▪️ Username: @{username or 'yo‘q'}\n"
        f"▪️ To‘liq ism: {full_name or '-'}\n"
        f"▪️ Telefon: {phone or '📵'}\n"
        f"▪️ Telegram ID: <code>{telegram_id}</code>"
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_user:{telegram_id}")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_users")]
    ])
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# 🗑️ Foydalanuvchini o‘chirish
@router.callback_query(lambda c: c.data.startswith("delete_user:"))
async def delete_user_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")

    telegram_id = int(callback.data.split(":")[1])
    await delete_user(telegram_id)
    await callback.message.delete()
    await callback.message.answer("✅ Foydalanuvchi o‘chirildi.")
    await cmd_list_users(callback)  # Ro'yxatni yangilash


class RektoratStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_tg_id = State()
    editing_old_name = State()
    editing_new_name = State()
    editing_new_tg_id = State()

# 🏛 Rektoratlar ro'yxatini ko'rsatish
@router.callback_query(lambda c: c.data == "list_rectorate")
async def list_rectorate_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")

    rectorates = await get_rectorate()
    
    buttons = [
        [types.InlineKeyboardButton(text=name, callback_data=f"get_rectorate:{tg_id}")]
        for name, tg_id in rectorates
    ]

    # 🟢 Har doim tugma qo‘shiladi
    buttons.append([types.InlineKeyboardButton(text="➕ Yangi qo‘shish", callback_data="add_rectorate")])
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    if not rectorates:
        return await callback.message.answer("🚫 Hech qanday Xodim mavjud emas.", reply_markup=keyboard)
    await callback.message.delete()
    await callback.message.answer("🏛 Xodimlar ro'yxati:", reply_markup=keyboard)


# 📄 Bitta Xodim tafsilotlari
@router.callback_query(lambda c: c.data.startswith("get_rectorate:"))
async def get_rectorate_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")

    tg_id = int(callback.data.split(":")[1])
    name = await get_rectorate_one(tg_id)
    if not name:
        return await callback.message.answer("❌ Xodim topilmadi.")

    text = f"🏛 *Xodim ma'lumotlari:*\n\n▪️ Nomi: {name}\n▪️ Telegram ID: `{tg_id}`"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_rectorate:{name}:{tg_id}")],
        [types.InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_rectorate:{tg_id}")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_rectorate")]
    ])
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# 🗑️ Xodimni o‘chirish
@router.callback_query(lambda c: c.data.startswith("delete_rectorate:"))
async def delete_rectorate_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    tg_id = int(callback.data.split(":")[1])
    await delete_rectorate(tg_id)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_rectorate")]
        ])
    await callback.message.delete()
    await callback.message.answer("✅ Xodim o‘chirildi.", reply_markup=keyboard)
    # await list_rectorate_callback(callback)

# ➕ Xodim qo‘shish bosqichi
@router.callback_query(lambda c: c.data == "add_rectorate")
async def add_rectorate_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")
    await callback.message.delete()
    await callback.message.answer("✏️ Xodim nomini kiriting:")
    await state.set_state(RektoratStates.waiting_for_name)

@router.message(RektoratStates.waiting_for_name)
async def add_rectorate_name(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo'q.")
    await state.update_data(name=message.text.strip())
    await message.delete()
    await message.answer("📥 Telegram ID ni kiriting:")
    await state.set_state(RektoratStates.waiting_for_tg_id)

@router.message(RektoratStates.waiting_for_tg_id)
async def add_rectorate_tg(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo'q.")
    data = await state.get_data()
    name = data['name']
    try:
        tg_id = int(message.text.strip())
        await add_rectorate(name, tg_id)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_rectorate")]
        ])
        await message.delete()
        await message.answer("✅ Yangi Xodim qo‘shildi!", reply_markup=keyboard)
    except:
        await message.answer("❌ Telegram ID noto‘g‘ri formatda.")
    await state.clear()

# ✏️ Xodimni tahrirlash
@router.callback_query(lambda c: c.data.startswith("edit_rectorate:"))
async def edit_rectorate_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")
    _, old_name, old_tg_id = callback.data.split(":")
    await state.update_data(old_name=old_name)
    await callback.message.answer(f"✏️ Yangi nomini kiriting (eski: {old_name}):")
    await state.set_state(RektoratStates.editing_new_name)

@router.message(RektoratStates.editing_new_name)
async def edit_rectorate_name(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo'q.")
    await state.update_data(new_name=message.text.strip())
    await message.answer("📥 Yangi Telegram ID ni kiriting:")
    await state.set_state(RektoratStates.editing_new_tg_id)

@router.message(RektoratStates.editing_new_tg_id)
async def edit_rectorate_tg(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo'q.")
    data = await state.get_data()
    old_name = data['old_name']
    new_name = data['new_name']
    try:
        new_tg_id = int(message.text.strip())
        await update_rectorate(old_name, new_name, new_tg_id)
        await message.answer("✅ Xodim yangilandi!")
    except:
        await message.answer("❌ Telegram ID noto‘g‘ri formatda.")
    await state.clear()



# Murojaat turlari uchun holatlar
class RequestTypeStates(StatesGroup):
    waiting_for_name = State()
    editing_old_name = State()
    editing_new_name = State()

# 📋 Murojaat turlari ro'yxati
@router.callback_query(lambda c: c.data == "list_request_types")
async def list_request_types_callback(callback: types.CallbackQuery):

    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")

    types_list = await get_request_types()
    if not types_list:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Qo‘shish", callback_data="add_request_type")],
            [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")]
        ])
        return await callback.message.answer("🚫 Hech qanday murojaat turi mavjud emas.", reply_markup=keyboard)

    buttons = [
        [types.InlineKeyboardButton(text=name[0], callback_data=f"get_request_type:{name[0]}")]
        for name in types_list
    ]
    buttons.append([types.InlineKeyboardButton(text="➕ Qo‘shish", callback_data="add_request_type")])
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.delete()
    await callback.message.answer("📋 Murojaat turlari:", reply_markup=keyboard)

# 🔍 Bitta murojaat turini ko‘rish
@router.callback_query(lambda c: c.data.startswith("get_request_type:"))
async def get_request_type_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    name = callback.data.split(":")[1]
    text = f"📄 *Murojaat turi:*\n\n▪️ Nomi: {name}"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_request_type:{name}")],
        [types.InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"delete_request_type:{name}")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_request_types")]
    ])
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# ➕ Yangi murojaat turi qo‘shish
@router.callback_query(lambda c: c.data == "add_request_type")
async def add_request_type_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    await callback.message.delete()
    await callback.message.answer("✏️ Murojaat turi nomini kiriting:")
    await state.set_state(RequestTypeStates.waiting_for_name)

@router.message(RequestTypeStates.waiting_for_name)
async def add_request_type_save(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo‘q.")
    name = message.text.strip()
    await add_request_type(name)
    await message.delete()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_request_types")]
    ])
    await message.answer("✅ Murojaat turi qo‘shildi!", reply_markup=keyboard)
    await state.clear()

# ✏️ Murojaat turini tahrirlash
@router.callback_query(lambda c: c.data.startswith("edit_request_type:"))
async def edit_request_type_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    old_name = callback.data.split(":")[1]
    await state.update_data(old_name=old_name)
    await callback.message.answer(f"✏️ Yangi nomini kiriting (eski: {old_name}):")
    await state.set_state(RequestTypeStates.editing_new_name)

@router.message(RequestTypeStates.editing_new_name)
async def edit_request_type_save(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo‘q.")
    data = await state.get_data()
    old_name = data['old_name']
    new_name = message.text.strip()
    await update_request_type(old_name, new_name)
    await message.answer("✅ Murojaat turi yangilandi!")
    await state.clear()

# 🗑 Murojaat turini o‘chirish
@router.callback_query(lambda c: c.data.startswith("delete_request_type:")) 
async def delete_request_type_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id): 
        return await callback.message.reply("❌ Ruxsat yo‘q.") 
    
    name = callback.data.split(":")[1]
    await delete_request_type(name) 
    
    # Xabarni o‘chiramiz
    await callback.message.delete()

    # Faqat bitta javob qaytaramiz
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_request_types")]
    ])
    await callback.message.answer("✅ Murojaat turi o‘chirildi.", reply_markup=keyboard)

    # Qayta chaqirmaymiz:
    # await list_request_types_callback(callback)  ❌ SHU YERDA XATO



class ChannelStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_link = State()
    editing_old_link = State()
    editing_new_name = State()

# 📋 Kanallar ro'yxati
@router.callback_query(lambda c: c.data == "list_channels")
async def list_channels_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo'q.")

    channels = await get_channels()
    if not channels:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ Qo‘shish", callback_data="add_channel")],
            [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")]
        ])
        return await callback.message.answer("🚫 Hech qanday kanal mavjud emas.", reply_markup=keyboard)

    buttons = [
        [types.InlineKeyboardButton(text=name, callback_data=f"get_channel:{link}")]
        for name, link in channels
    ]
    buttons.append([types.InlineKeyboardButton(text="➕ Qo‘shish", callback_data="add_channel")])
    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.delete()
    await callback.message.answer("📋 Kanallar ro'yxati:", reply_markup=keyboard)

# 🔍 Bitta kanal ma'lumotlari
@router.callback_query(lambda c: c.data.startswith("get_channel:"))
async def get_channel_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    link = callback.data.split(":", 1)[1]
    channels = await get_channels()
    channel = next((c for c in channels if c[1] == link), None)
    if not channel:
        return await callback.message.answer("❌ Kanal topilmadi.")
    name, _ = channel
    text = f"📡 *Kanal:*\n\n▪️ Nomi: {name}\n▪️ Havola: {link}"
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_channel:{link}")],
        [types.InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"delete_channel:{link}")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_channels")]
    ])
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# ➕ Kanal qo‘shish boshlanishi
@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    await callback.message.delete()
    await callback.message.answer("✏️ Kanal nomini kiriting:")
    await state.set_state(ChannelStates.waiting_for_name)

@router.message(ChannelStates.waiting_for_name)
async def add_channel_name(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo‘q.")
    await state.update_data(name=message.text.strip())
    await message.delete()
    await message.answer("📥 Kanal havolasini (https://...) kiriting:")
    await state.set_state(ChannelStates.waiting_for_link)

@router.message(ChannelStates.waiting_for_link)
async def add_channel_link(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo‘q.")
    data = await state.get_data()
    name = data['name']
    link = message.text.strip()
    await add_channel(name, link)
    await message.delete()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="list_channels")]
    ])
    await message.answer("✅ Kanal qo‘shildi!", reply_markup=keyboard)
    await state.clear()

# ✏️ Kanalni tahrirlash
@router.callback_query(lambda c: c.data.startswith("edit_channel:"))
async def edit_channel_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    old_link = callback.data.split(":")[1]
    await state.update_data(old_link=old_link)
    await callback.message.answer("✏️ Yangi nomini kiriting:")
    await state.set_state(ChannelStates.editing_new_name)

@router.message(ChannelStates.editing_new_name)
async def edit_channel_save(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Ruxsat yo‘q.")
    data = await state.get_data()
    old_link = data['old_link']
    new_name = message.text.strip()
    await update_channel(new_name, old_link)
    await message.answer("✅ Kanal tahrirlandi!")
    await state.clear()

# 🗑 Kanalni o‘chirish
@router.callback_query(lambda c: c.data.startswith("delete_channel:"))
async def delete_channel_callback(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q.")
    link = callback.data.split(":", 1)[1]
    await delete_channel(link)
    await callback.message.delete()
    await callback.message.answer("✅ Kanal o‘chirildi.")
    await list_channels_callback(callback)
    
MONITOR_PAGE_SIZE = 5
monitor_cache = {}  # user_id -> (page, murojaatlar, javoblar)

@router.callback_query(lambda c: c.data.startswith("monitoring"))
async def monitoring_panel(callback: types.CallbackQuery):
    if not await is_super_admin(callback.from_user.id):
        return await callback.message.reply("❌ Ruxsat yo‘q. Faqat super adminlar uchun.")

    page = 0
    if ":" in callback.data:
        _, page = callback.data.split(":")
        page = int(page)

    murojaatlar = await get_all_murojaatlar()
    javoblar = await get_all_admin_responses()
    user_id = callback.from_user.id

    if not murojaatlar:
        return await callback.message.answer("📭 Hech qanday murojaat topilmadi.")

    monitor_cache[user_id] = (page, murojaatlar, javoblar)
    start = page * MONITOR_PAGE_SIZE
    end = start + MONITOR_PAGE_SIZE
    sliced = murojaatlar[start:end]

    buttons = []
    for m in sliced:
        murojaat_id, uid, _, request_type, _, _, _ = m
        user = await get_user_by_telegram_id(uid)
        full_name = user[2] if user else "Noma'lum"
        status = await get_response_status_by_murojaat_id(murojaat_id)
        status_text = "✅" if status == "answered" else "⏳"
        buttons.append([
            types.InlineKeyboardButton(
                text=f"{status_text} {full_name} | {request_type}",
                callback_data=f"view_murojaat:{murojaat_id}"
            )
        ])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"monitoring:{page - 1}"))
    if end < len(murojaatlar):
        nav_buttons.append(types.InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"monitoring:{page + 1}"))

    buttons.append([types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_admin")])
    if nav_buttons:
        buttons.append(nav_buttons)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.delete()
    await callback.message.answer("📋 Murojaatlar ro‘yxati:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("view_murojaat:"))
async def view_murojaat_detail(callback: types.CallbackQuery):
    murojaat_id = int(callback.data.split(":")[1])
    murojaatlar = await get_all_murojaatlar()
    javoblar = await get_all_admin_responses()
    murojaat = next((m for m in murojaatlar if m[0] == murojaat_id), None)
    if not murojaat:
        return await callback.message.answer("❌ Murojaat topilmadi.")

    murojaat_id, uid, rectorate_id, request_type, role, content, created_at = murojaat
    user = await get_user_by_telegram_id(uid)
    rectorate_name = await get_rectorate_one(rectorate_id)

    full_name = user[2] if user else "Noma'lum"
    phone = user[3] if user else "-"

    status = await get_response_status_by_murojaat_id(murojaat_id)
    status_text = "✅ Javob berilgan" if status == "answered" else "⏳ Kutilmoqda"

    response = next((r for r in javoblar if r[4] == murojaat_id), None)
    admin_id = response[1] if response else "-"
    admin_message = response[2] if response else "-"
    response_time = response[3] if response else "-"

    text = (
        f"🆔 Murojaat ID: {murojaat_id}\n"
        f"🕒 {created_at}\n"
        f"👤 {full_name} | 📞 {phone}\n"
        f"📌 Murojaat turi: {request_type}\n"
        f"🧾 Rol: {role}\n"
        f"✉️ Matn: {content}\n"
        f"👨‍💼 Xodim: {rectorate_name}\n"
        f"👮 Javob bergan admin: {admin_id}\n"
        f"🗨️ Javob matni: {admin_message}\n"
        f"📅 Javob vaqti: {response_time}\n"
        f"📍 Holat: {status_text}"
    )

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="monitoring")]
    ])
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)


# Router yordamida handlerlarni ro'yxatga olish
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(start_admin, Command('start_admin'))
    router.callback_query.register(
        admin_start_back,
        lambda c: c.data and c.data.startswith('back_admin')
    )
