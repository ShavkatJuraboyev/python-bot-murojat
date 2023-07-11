from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('user.db')
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS user(
    id INTEGER NOT NULL,
    user_phone INTEGER,
    user_id INTEGER,
    user_text TEXT,
    first_name TEXT,
    username TEXT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id" AUTOINCREMENT)
);""")
conn.commit()

TOKEN = ''  # Telegram Bot Token
ADMIN_ID = ''

user_phone_numbers = {}
user_information = {}


def start(update, context):
    chat_id = update.message.chat_id
    phone_button = KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    if chat_id == ADMIN_ID:
        pass
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="👋 Assalomu alaykum botga xush kelibsiz! \n👨‍💻 Murojat qilish uchun, 📲 Telefon raqamingizni yuborishingizni so'rayman.",
                                 reply_markup=reply_markup)

    # user_information lug'atini yaratish
    context.user_data['user_information'] = {}


def process_phone_number(update, context):
    phone_number = update.message.contact.phone_number
    chat_id = update.message.chat_id
    ism = update.message.chat.first_name
    username = update.message.chat.username
    context.user_data['user_information']['user_phone'] = phone_number
    context.user_data['user_information']['user_id'] = chat_id
    context.user_data['user_information']['first_name'] = ism
    context.user_data['user_information']['username'] = username

    user_phone_numbers[chat_id] = phone_number

    admin_chat_id = ADMIN_ID
    if chat_id == ADMIN_ID:
        pass
    else:
        context.bot.send_message(chat_id=admin_chat_id, text=f"📱 Yangi foydalanuvchi telefon raqami: {phone_number}!")
        context.bot.send_message(chat_id=chat_id, text="✍️ Endi siz adminga xabar yuborishingiz mumkin.")


def process_message(update, context):
    chat_id = update.message.chat_id

    if chat_id not in user_phone_numbers:
        context.bot.send_message(chat_id=chat_id, text="📲 Iltimos, avvalo telefon raqamingizni kiriting.")
        return

    elif chat_id in user_phone_numbers:
        message = update.message.text
        context.user_data['user_information']['message'] = message
        context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=chat_id, message_id=update.message.message_id)
        context.bot.send_message(chat_id=chat_id, text="👨‍💻 Murojatiz admin admonition ko'rilib chiqiladi.")

        con = sqlite3.connect('user.db')
        c = con.cursor()
        c.execute(f"INSERT INTO user (user_phone, user_id, user_text, first_name, username) VALUES (?, ?, ?, ?, ?)", (
            context.user_data['user_information']['user_phone'],
            context.user_data['user_information']['user_id'],
            context.user_data['user_information']['message'],
            context.user_data['user_information']['first_name'],
            context.user_data['user_information']['username'],
        ))
        con.commit()
        con.close()


def reply_to_message(update, context):
    admin_chat_id = ADMIN_ID
    if update.message.reply_to_message:
        text = update.message.reply_to_message.text
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        natija = c.execute(f"""SELECT user_id FROM user WHERE user_text='{text}'""").fetchone()[0]
        conn.commit()
        conn.close()
        if admin_chat_id == ADMIN_ID:
            context.bot.forward_message(chat_id=natija, from_chat_id=ADMIN_ID, message_id=update.message.message_id)


def delete_old_data(context):
    ochirish_vaqt = datetime.now() - timedelta(days=7)
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    delete_query = f"DELETE FROM user WHERE date_created < ?;"
    c.execute(delete_query, (ochirish_vaqt,))
    conn.commit()
    conn.close()

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    phone_number_handler = MessageHandler(Filters.contact, process_phone_number)
    reply_handler = MessageHandler(Filters.reply, reply_to_message)
    message_handler = MessageHandler(Filters.text & (~Filters.command), process_message)

    job_queue = updater.job_queue
    job_queue.run_repeating(delete_old_data, interval=24 * 60 * 60, context=updater)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(phone_number_handler)
    dispatcher.add_handler(reply_handler)
    dispatcher.add_handler(message_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
