import aiosqlite
import os

# Define a directory for the database
DB_DIR = "data"  # Or any other directory you want to use
DB_PATH = os.path.join(DB_DIR, "bot.db")  # Combine directory with filename

# Ensure the directory exists
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

async def init_db():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Foydalanuvchilar jadvali
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                username TEXT,
                full_name TEXT,
                phone_number TEXT
            )""")
            
            await db.execute("""
            CREATE TABLE IF NOT EXISTS rectorate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                tg_id INTEGER
            )""")

            # Kanallar va guruhlar jadvali
            await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                link TEXT
            )""")
                        
            await db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")



async def add_rectorate(name, tg_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO rectorate (name, tg_id) VALUES (?, ?)", (name, tg_id))
            await db.commit()
    except Exception as e:
        print(f"Error adding channel: {e}")

async def get_rectorate():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name, tg_id FROM rectorate")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting channels: {e}")
        return []

async def add_channel(name, link):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO channels (name, link) VALUES (?, ?)", (name, link))
            await db.commit()
    except Exception as e:
        print(f"Error adding video: {e}")

async def get_channels():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name, link FROM channels")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting videos: {e}")
        return []
    

async def add_users(telegram_id, first_name, username, full_name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO users (telegram_id, first_name, username, full_name) VALUES (?, ?, ?, ?)", (telegram_id, first_name, username, full_name))
            await db.commit()
    except Exception as e:
        print(f"Error adding channel: {e}")

async def add_users_phone(telegram_id, phone_number):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET phone_number = ? WHERE telegram_id = ? ", ( phone_number, telegram_id))
            await db.commit()
    except Exception as e:
        print(f"Error adding channel: {e}")

async def get_user_by_telegram_id(telegram_id):
    """Foydalanuvchining ma'lumotlarini bazadan olish."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT first_name, username, full_name, phone_number FROM users WHERE telegram_id = ?", (telegram_id,))
            user = await cursor.fetchone()
            return user  # Agar ma'lumot topilmasa, None qaytadi
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

async def get_full_users(telegram_id):
    """Foydalanuvchining ma'lumotlarini bazadan olish."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT first_name, username, full_name, phone_number FROM users WHERE telegram_id = ?", (telegram_id,))
            user = await cursor.fetchone()
            return user  # Agar ma'lumot topilmasa, None qaytadi
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None