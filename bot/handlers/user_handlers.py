from aiogram import F, types, Router, Dispatcher, Bot
from aiogram.filters import Command
from database.db import get_channels, add_users, get_rectorate, add_users_phone, get_user_by_telegram_id, get_rectorate_one
from utils.membership import check_membership
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

def escape_markdown(text: str) -> str:
    """Telegram Markdown uchun maxsus belgilarni qochirish."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{char}" if char in escape_chars else char for char in text)

router = Router()  # Router yaratish

# Holatlar guruhi
class UserStates(StatesGroup):
    waiting_for_message_content = State()
user_data = {}

# /start komandasi uchun handler
async def start_handler(message: types.Message, bot: Bot):
    telegram_id = message.chat.id
    user = await get_user_by_telegram_id(telegram_id)

    if user:
        # Ma'lumotlar bazasida foydalanuvchi mavjud
        first_name, username, full_name, phone_number = user
        if not full_name:
            # Agar ism va familiya bo'lmasa
            await message.answer("Ismingiz va familiyangizni yuboring:")
        elif not phone_number:
            # Agar telefon raqami bo'lmasa
            phone_button = KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)
            phone_keyboard = ReplyKeyboardMarkup(keyboard=[[phone_button]], resize_keyboard=True)
            await message.answer("🤳 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard)
        else:
            # Kanal va guruhlar a'zoligini tekshirish
            channels = await get_channels()
            all_joined = True
            for name, link in channels:
                channel_username = link.split("/")[-1]
                if not await check_membership(bot, channel_username, telegram_id):
                    all_joined = False
                    break

            if all_joined:
                # Foydalanuvchi barcha kanal va guruhlarga a'zo bo'lsa
                await message.answer("Xush kelibsiz🤗! Kimga murojaat yo'llamoqchisiz📝!")
                await show_rectorate_list(message)
            else:
                # Foydalanuvchi hali hamma kanal va guruhlarga a'zo emas
                await check_user_channels(message, bot)
    else:
        # Foydalanuvchi ma'lumotlari bazada mavjud emas
        await message.answer("👋 Assalomu alaykum! \n🤗 Botimizga xush kelibsiz.\n✍️ Iltimos, ismingiz va familiyangizni yozing:")

# Foydalanuvchi ism va familiyasini qayta ishlash
async def name_handler(message: types.Message):
    telegram_id = message.chat.id
    full_name = message.text.strip()
    first_name = message.chat.first_name if message.chat.first_name else ''
    username = message.chat.username if message.chat.username else ''

    # Foydalanuvchi ma'lumotlarini qo'shish yoki yangilash
    await add_users(telegram_id, first_name, username, full_name)

    # Telefon raqamini so'rash
    phone_button = KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)
    phone_keyboard = ReplyKeyboardMarkup(keyboard=[[phone_button]], resize_keyboard=True)
    await message.answer("🤳 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard)

# Telefon raqamini qayta ishlash
async def phone_handler(message: types.Message, bot: Bot):
    telegram_id = message.chat.id
    phone_number = message.contact.phone_number

    try:
        await add_users_phone(telegram_id, phone_number)
        await message.answer("✅ Telefon raqamingiz tasdiqlandi")
        await check_user_channels(message, bot)
    except Exception as e:
        await message.answer(f"❌ Telefon raqamini tasdiqlashda xatolik yuz berdi: {e}")

# Kanal va guruhlarni tekshirish
async def check_user_channels(message, bot):
    channels = await get_channels()  # Kanallar ro‘yxatini olish
    buttons = [
        [InlineKeyboardButton(text=name, url=link)] for name, link in channels
    ]
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership")])
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "Iltimos, quyidagi 👇 kanallarga obuna bo'ling va tekshirish tugmasini bosing:",
        reply_markup=inline_kb
    )

# Kanal va guruh a'zoligini qayta tekshirish
@router.callback_query(lambda call: call.data == "check_membership")
async def verify_membership(call: types.CallbackQuery, bot: Bot):
    telegram_id = call.from_user.id
    channels = await get_channels()
    all_joined = True

    for name, link in channels:
        channel_username = link.split("/")[-1]
        if not await check_membership(bot, channel_username, telegram_id):
            all_joined = False
            break
            
    if all_joined:
        await call.message.delete()  # Inline tugmalarni o'chirish
        await call.message.answer("✅ Siz barcha kanal va guruhlarga a'zo bo'lgansiz!")
        await show_rectorate_list(call.message)
    else:
        await call.message.answer("❌ Hali hamma kanal va guruhlarga a'zo bo'lmagansiz. Iltimos, qo'shiling!")


# Rektorat ma'lumotlarini ko'rsatish
async def show_rectorate_list(message: types.Message):
    rectorate = await get_rectorate()
    if not rectorate:
        await message.answer("❌ Rektorat ro'yxati topilmadi.")
        return
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"rectorate:{tg_id}")]
        for name, tg_id in rectorate
    ]
    inline_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("✔️ Siz kimga murojaat yubormoqchisiz:", reply_markup=inline_kb)


@router.callback_query(lambda call: call.data.startswith("rectorate:"))
async def handle_rectorate_selection(call: CallbackQuery, state: FSMContext):
    rectorate_id = call.data.split(":")[1]
    user_data[call.from_user.id] = {"rectorate_id": rectorate_id}  # Rektoratni saqlash

    # Eski tugmalarni o'chirish
    await call.message.delete()

    buttons = [
        [InlineKeyboardButton(text="Ariza yuborish", callback_data="request:type:Ariza yuborish")],
        [InlineKeyboardButton(text="Shikoyat qilish", callback_data="request:type:Shikoyat qilish")],
        [InlineKeyboardButton(text="Taklif qilish", callback_data="request:type:Taklif qilish")],
        [InlineKeyboardButton(text="Boshqa", callback_data="request:type:Boshqa")]
    ]
    inline_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.answer("✔️ Quyidagi murojaat turini tanlang:", reply_markup=inline_kb)


@router.callback_query(lambda call: call.data.startswith("request:type:"))
async def handle_request_type(call: CallbackQuery, state: FSMContext):
    request_type = call.data.split(":")[2]
    user_data[call.from_user.id]["request_type"] = request_type  # Murojaat turini saqlash

    # Eski tugmalarni o'chirish
    await call.message.delete()

    buttons = [
        [InlineKeyboardButton(text="Talaba", callback_data="role:Talaba")],
        [InlineKeyboardButton(text="Xodim", callback_data="role:Xodim")],
        [InlineKeyboardButton(text="Boshqa", callback_data="role:Boshqa")],
    ]
    inline_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.answer("✔️ Quydagilardan birini tanlang :", reply_markup=inline_kb)


@router.callback_query(lambda call: call.data.startswith("role:"))
async def handle_role_selection(call: CallbackQuery, state: FSMContext):
    role = call.data.split(":")[1]
    user_data[call.from_user.id]["role"] = role  # Rolni saqlash

    # Eski tugmalarni o'chirish
    await call.message.delete()

    await call.message.answer("🖌 Murojaatingiz mazmunini yozing va yuboring:")

    # Holatni foydalanuvchiga o'tkazish
    await state.set_state(UserStates.waiting_for_message_content)


@router.message(UserStates.waiting_for_message_content)
async def collect_message_content(message: Message, state: FSMContext):
    # Mazmunni saqlash
    user_id = message.from_user.id
    user_data[user_id]["content"] = message.text
    user = await get_user_by_telegram_id(user_id)

    if user:
        # Ma'lumotlar bazasida foydalanuvchi mavjud
        first_name, username, full_name, phone_number = user

    # Foydalanuvchiga javob qaytarish
    rectorate_id = user_data[user_id]["rectorate_id"]
    request_type = user_data[user_id]["request_type"]
    role = user_data[user_id]["role"]
    content = user_data[user_id]["content"]
    name = await get_rectorate_one(rectorate_id)
    await message.answer("Murojaatingiz muvaffaqiyatli yuborildi.")
    summary = (
        f"✅ *Murojaat tafsilotlari:*\n\n"
        f"🔹 Rektorat: {escape_markdown(name)}\n"
        f"🔹 Murojaat turi: {escape_markdown(request_type)}\n"
        f"🔹 Rol: {escape_markdown(role)}\n"
        f"🔹 Mazmun: {escape_markdown(content)}\n\n"
        f"👨‍💻Admin tez orada sizga javob qaytaradi."
    )

    await message.answer(summary, parse_mode="Markdown")

     # Rektoratga yuborish
    if rectorate_id:  # agar rectorate_id mavjud bo'lsa
        summary_rectarat = (
            f"✅ *Murojaat tafsilotlari:*\n\n"
            f"🔹 Ism familiya: {escape_markdown(full_name)}\n"
            f"🔹 Telefon: {escape_markdown(phone_number)}\n"
            f"🔹 Username: {escape_markdown(username)}\n"
            f"🔹 Murojaat turi: {escape_markdown(request_type)}\n"
            f"🔹 Rol: {escape_markdown(role)}\n"
            f"🔹 Mazmun: {escape_markdown(content)}\n"
            f"❗️ *Reply qilib javob yozing, foydalanuvchi ID: {user_id}*"
        )

        try:
            await message.bot.send_message(
                rectorate_id,
                summary_rectarat,  # Yuborilgan murojaatning tafsilotlari
                parse_mode="Markdown"  # Markdown formatni aniqlash
            )
        except Exception as e:
            await message.answer(f"❌ Xatolik yuz berdi: {e}")
    else:
        await message.answer("❌ Rektorat ID topilmadi.")

    # Holatdan chiqish
    await state.clear()
    # Foydalanuvchi ma'lumotlarini o'chirish
    user_data.pop(user_id, None)
    
@router.message(F.text, F.reply_to_message)
async def forward_reply_to_user(message: Message):
    # Reply qilingan xabardan foydalanuvchi ID ni olish
    if message.reply_to_message and "foydalanuvchi ID" in message.reply_to_message.text:
        try:
            # Foydalanuvchi ID'sini olish
            user_id_line = message.reply_to_message.text.split("foydalanuvchi ID:")[-1].strip()
            user_id = int(user_id_line)
            
            # Adminning javob xabarini foydalanuvchiga yuborish
            await message.bot.send_message(
                user_id,
                f"👨‍💻 *Admindan javob keldi:*\n\n{message.text}",
                parse_mode="Markdown"
            )
            await message.answer("✅ Javob foydalanuvchiga muvaffaqiyatli yuborildi.")
        except Exception as e:
            await message.answer(f"❌ Javobni yuborishda xatolik: {e}")
    else:
        await message.answer("❌ Reply xabar foydalanuvchi ID'ni o'z ichiga olmaydi.")


# Router yordamida handlerlarni ro'yxatga olish
def register_user_handlers(dp: Dispatcher, bot: Bot):
    dp.include_router(router)  # Routerni Dispatcherga qo'shish
    router.message.register(start_handler, Command("start"))  # /start komandasi uchun handler
    router.message.register(name_handler, lambda msg: msg.text and not msg.contact)  # Matn uchun handler
    router.message.register(phone_handler, lambda msg: msg.contact)  # Telefon raqam uchun handler
