# ✅ YANGILANGAN user_handlers.py
from aiogram import F, types, Router, Dispatcher, Bot
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.db import (
    get_channels, add_users,
    add_users_phone, get_user_by_telegram_id,
    get_request_types, get_rectorate_by_request_type, get_super_admins,
    get_rectorate_one, get_response_status, log_murojaat
)
from utils.membership import check_membership

router = Router()

def escape_markdown(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{char}" if char in escape_chars else char for char in text)


class UserStates(StatesGroup):
    waiting_for_message_content = State()

user_data = {}

async def start_handler(message: types.Message, bot: Bot):
    telegram_id = message.chat.id
    user = await get_user_by_telegram_id(telegram_id)

    if user:
        first_name, username, full_name, phone_number = user
        if not full_name:
            await message.answer("Ismingiz va familiyangizni yuboring:")
        elif not phone_number:
            phone_button = KeyboardButton(text="📾 Telefon raqamni yuborish", request_contact=True)
            phone_keyboard = ReplyKeyboardMarkup(keyboard=[[phone_button]], resize_keyboard=True)
            await message.answer("🤹 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard)
        else:
            await check_user_channels(message, bot)
    else:
        await message.answer("👋 Assalomu alaykum!\n🤗 Botimizga xush kelibsiz.\n✍️ Iltimos, ismingiz va familiyangizni yozing:")

async def name_handler(message: types.Message):
    telegram_id = message.chat.id
    full_name = message.text.strip()
    first_name = message.chat.first_name or ''
    username = message.chat.username or ''
    await add_users(telegram_id, first_name, username, full_name)
    phone_button = KeyboardButton(text="📾 Telefon raqamni yuborish", request_contact=True)
    phone_keyboard = ReplyKeyboardMarkup(keyboard=[[phone_button]], resize_keyboard=True)
    await message.answer("🤹 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard)

async def phone_handler(message: types.Message, bot: Bot):
    telegram_id = message.chat.id
    phone_number = message.contact.phone_number
    await add_users_phone(telegram_id, phone_number)
    await check_user_channels(message, bot)

async def check_user_channels(message, bot):
    channels = await get_channels()
    buttons = [[InlineKeyboardButton(text=name, url=link)] for name, link in channels]
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership")])
    inline_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Iltimos, quyidagi 👇 kanallarga obuna bo'ling va tekshirish tugmasini bosing:", reply_markup=inline_kb)

@router.callback_query(lambda c: c.data == "check_membership")
async def verify_membership(call: CallbackQuery, bot: Bot):
    telegram_id = call.from_user.id
    channels = await get_channels()
    all_joined = True
    for name, link in channels:
        channel_username = link.split("/")[-1]
        if not await check_membership(bot, channel_username, telegram_id):
            all_joined = False
            break
    if all_joined:
        await call.message.delete()
        request_types = await get_request_types()
        buttons = [[InlineKeyboardButton(text=typ[0], callback_data=f"request_type:{typ[0]}")] for typ in request_types]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await call.message.answer("✅ Murojaat turini tanlang:", reply_markup=kb)
    else:
        await call.message.answer("❌ Hali hamma kanalga obuna emassiz.")

@router.callback_query(lambda c: c.data.startswith("request_type:"))
async def handle_request_type(call: CallbackQuery, state: FSMContext):
    request_type = call.data.split(":")[1]
    rectorate_id = await get_rectorate_by_request_type(request_type)
    if not rectorate_id:
        return await call.message.answer("❌ Bu murojaat turi uchun xodim belgilanmagan.")

    user_data[call.from_user.id] = {
        "request_type": request_type,
        "rectorate_id": rectorate_id
    }
    await call.message.delete()
    buttons = [[InlineKeyboardButton(text=role, callback_data=f"role:{role}")] for role in ["Talaba", "Xodim", "Boshqa"]]
    await call.message.answer("Rolingizni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data.startswith("role:"))
async def handle_role_selection(call: CallbackQuery, state: FSMContext):
    role = call.data.split(":")[1]
    user_data[call.from_user.id]["role"] = role
    await call.message.delete()
    await call.message.answer("Murojaatingiz matnini kiriting:")
    await state.set_state(UserStates.waiting_for_message_content)


@router.message(UserStates.waiting_for_message_content)
async def collect_message_content(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data[user_id]["content"] = message.text
    user = await get_user_by_telegram_id(user_id)
    if not user:
        return await message.answer("Foydalanuvchi topilmadi.")

    full_name, username, phone = user[2], user[1], user[3]
    rectorate_id = user_data[user_id]["rectorate_id"]
    request_type = user_data[user_id]["request_type"]
    role = user_data[user_id]["role"]
    content = user_data[user_id]["content"]

    # 🟡 Qaysi xodimga yuborilmoqda
    rectorate_name = await get_rectorate_one(rectorate_id)
    status = await get_response_status(user_id)

    summary = (
        f"📩 *Yangi murojaat*\n\n"
        f"👤 Ism: {escape_markdown(full_name)}\n"
        f"📞 Telefon: {escape_markdown(phone)}\n"
        f"🔗 Username: @{escape_markdown(username or 'yo‘q')}\n"
        f"📌 Murojaat turi: {escape_markdown(request_type)}\n"
        f"📎 Rol: {escape_markdown(role)}\n"
        f"📝 Matn: {escape_markdown(content)}\n\n"
        f"👥 Yuborilgan xodim: {escape_markdown(rectorate_name)}\n"
        f"✅ Holat: {'✅ Javob berilgan' if status == 'answered' else '❗️ Kutilmoqda'}\n\n"
        f"❗️ *Reply qilib javob yozing, foydalanuvchi ID: {user_id}*"
    )

    await message.answer("Murojaatingiz yuborildi.")
    await message.bot.send_message(rectorate_id, summary, parse_mode="Markdown")

    for admin_id in await get_super_admins():
        try:
            await message.bot.send_message(admin_id, summary, parse_mode="Markdown")
        except:
            pass

    await state.clear()
    user_data.pop(user_id, None)
    await log_murojaat(user_id, rectorate_id, request_type, role, content)


@router.message(F.text, F.reply_to_message)
async def forward_reply_to_user(message: Message):
    if message.reply_to_message and "foydalanuvchi ID" in message.reply_to_message.text:
        try:
            user_id_line = message.reply_to_message.text.split("foydalanuvchi ID:")[-1].strip()
            user_id = int(user_id_line)

            # ➕ foydalanuvchiga javob yuborish
            await message.bot.send_message(
                user_id,
                f"👨‍💻 *Admindan javob keldi:*\n\n{message.text}",
                parse_mode="Markdown"
            )

            # ✅ MUHIM: statusni 'answered' qilish
            from database.db import log_admin_response
            await log_admin_response(user_id, message.from_user.id, message.text)

            await message.answer("✅ Javob foydalanuvchiga yuborildi.")
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")



def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)
    router.message.register(start_handler, Command("start"))
    router.message.register(name_handler, lambda msg: msg.text and not msg.contact)
    router.message.register(phone_handler, lambda msg: msg.contact)
