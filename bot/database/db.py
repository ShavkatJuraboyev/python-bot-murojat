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

            await db.execute("""
            CREATE TABLE IF NOT EXISTS request_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                full_name TEXT
            )
            """)

                        
            await db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")


# === USERS CRUD ===

async def get_users():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT telegram_id, first_name, username, full_name, phone_number FROM users")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

async def get_user_by_telegram_id(telegram_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT first_name, username, full_name, phone_number FROM users WHERE telegram_id = ?", (telegram_id,))
            return await cursor.fetchone()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

async def add_users(telegram_id, first_name, username, full_name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (telegram_id, first_name, username, full_name)
                VALUES (?, ?, ?, ?)""",
                (telegram_id, first_name, username, full_name))
            await db.commit()
    except Exception as e:
        print(f"Error adding user: {e}")

async def add_users_phone(telegram_id, phone_number):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET phone_number = ? WHERE telegram_id = ?", (phone_number, telegram_id))
            await db.commit()
    except Exception as e:
        print(f"Error updating phone: {e}")

async def delete_user(telegram_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting user: {e}")


# === RECTORATE CRUD ===

async def get_rectorate():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name, tg_id FROM rectorate")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting rectorate: {e}")
        return []

async def get_rectorate_one(tg_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name FROM rectorate WHERE tg_id = ?", (tg_id,))
            result = await cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error fetching rectorate: {e}")
        return None

async def add_rectorate(name, tg_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO rectorate (name, tg_id) VALUES (?, ?)", (name, tg_id))
            await db.commit()
    except Exception as e:
        print(f"Error adding rectorate: {e}")

async def update_rectorate(old_name, new_name, new_tg_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE rectorate SET name = ?, tg_id = ? WHERE name = ?", (new_name, new_tg_id, old_name))
            await db.commit()
    except Exception as e:
        print(f"Error updating rectorate: {e}")

async def delete_rectorate(tg_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM rectorate WHERE tg_id = ?", (tg_id,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting rectorate: {e}")



# === CHANNELS CRUD ===

async def get_channels():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name, link FROM channels")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []

async def add_channel(name, link):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO channels (name, link) VALUES (?, ?)", (name, link))
            await db.commit()
    except Exception as e:
        print(f"Error adding channel: {e}")

async def update_channel(name, link):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE channels SET name = ? WHERE link = ?", (name, link))
            await db.commit()
    except Exception as e:
        print(f"Error updating channel: {e}")

async def delete_channel(link):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM channels WHERE link = ?", (link,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting channel: {e}")



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

# === REQUEST TYPES CRUD ===

async def get_request_types():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT name FROM request_types")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error fetching request types: {e}")
        return []

async def add_request_type(name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO request_types (name) VALUES (?)", (name,))
            await db.commit()
    except Exception as e:
        print(f"Error adding request type: {e}")

async def update_request_type(old_name, new_name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE request_types SET name = ? WHERE name = ?", (new_name, old_name))
            await db.commit()
    except Exception as e:
        print(f"Error updating request type: {e}")

async def delete_request_type(name):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM request_types WHERE name = ?", (name,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting request type: {e}")

    



# === Adminlar CRUD ===
async def add_admin(telegram_id: int, full_name: str):
    """Yangi admin qo‘shish."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO admins (telegram_id, full_name) VALUES (?, ?)", (telegram_id, full_name))
            await db.commit()
    except Exception as e:
        print(f"Error adding admin: {e}")

async def get_admins():
    """Barcha adminlarni olish."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT telegram_id, full_name FROM admins")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error fetching admins: {e}")
        return []

async def delete_admin(telegram_id: int):
    """Adminni o‘chirish."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
            await db.commit()
    except Exception as e:
        print(f"Error deleting admin: {e}")

async def is_admin(telegram_id: int) -> bool:
    """Foydalanuvchi adminmi yoki yo‘qmi — tekshiradi."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,))
            return await cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking admin: {e}")
        return False
