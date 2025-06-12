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
            CREATE TABLE IF NOT EXISTS request_routing (
                request_type TEXT,
                rectorate_id INTEGER
            )
            """)


            await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                full_name TEXT,
                is_super INTEGER DEFAULT 0
            )
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
            """)
                        
            await db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")

async def migrate_add_murojaat_id_column():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("ALTER TABLE admin_responses ADD COLUMN murojaat_id INTEGER")
            await db.commit()
            print("✅ 'murojaat_id' ustuni qo‘shildi.")
    except Exception as e:
        print(f"⚠️ Murojaat ID ustunini qo‘shishda xatolik: {e}")

async def get_all_murojaatlar():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # jadval bo'lmasa, bo'sh qaytaradi
            await db.execute("""
            CREATE TABLE IF NOT EXISTS murojaatlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                rectorate_id INTEGER,
                request_type TEXT,
                role TEXT,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cursor = await db.execute("SELECT * FROM murojaatlar ORDER BY created_at DESC")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error fetching murojaatlar: {e}")
        return []


async def get_all_admin_responses():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                SELECT user_id, admin_id, message, timestamp, murojaat_id
                FROM admin_responses ORDER BY timestamp DESC
            """)
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error fetching admin responses: {e}")
        return []



# === USERS CRUD ===

async def get_users():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT telegram_id, first_name, username, full_name, phone_number FROM users")
            return await cursor.fetchall()
    except Exception as e:
        print(f"Error getting users: {e}")
        return []



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
async def add_admin(telegram_id: int, full_name: str, is_super: int = 0):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO admins (telegram_id, full_name, is_super) VALUES (?, ?, ?)",
                (telegram_id, full_name, is_super)
            )
            await db.commit()
    except Exception as e:
        print(f"Error adding admin: {e}")

async def get_admins():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT telegram_id, full_name, is_super FROM admins")
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


async def is_super_admin(telegram_id: int) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT is_super FROM admins WHERE telegram_id = ?", (telegram_id,))
            result = await cursor.fetchone()
            return result and result[0] == 1
    except Exception as e:
        print(f"Error checking super admin: {e}")
        return False

async def log_admin_response(user_id: int, admin_id: int, message: str, murojaat_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO admin_responses (user_id, admin_id, message, murojaat_id, status)
                VALUES (?, ?, ?, ?, 'answered')
            """, (user_id, admin_id, message, murojaat_id))
            await db.commit()
    except Exception as e:
        print(f"Error logging admin response: {e}")


async def get_response_status_by_murojaat_id(murojaat_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT status FROM admin_responses WHERE murojaat_id = ? ORDER BY timestamp DESC LIMIT 1",
                (murojaat_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else "pending"
    except Exception as e:
        print(f"Error checking response status: {e}")
        return "pending"



async def get_response_status(user_id: int):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT status FROM admin_responses WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else "pending"
    except Exception as e:
        print(f"Error checking response status: {e}")
        return "pending"


async def set_request_route(request_type: str, rectorate_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO request_routing (request_type, rectorate_id) VALUES (?, ?)",
                         (request_type, rectorate_id))
        await db.commit()

async def get_rectorate_by_request_type(request_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT rectorate_id FROM request_routing WHERE request_type = ?", (request_type,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_super_admins():
    """Super adminlarning Telegram ID ro‘yxatini olish."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT telegram_id FROM admins WHERE is_super = 1")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching super admins: {e}")
        return []

async def set_request_route(request_type: str, rectorate_id: int):
    """Murojaat turini xodimga bog‘lash yoki yangilash."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO request_routing (request_type, rectorate_id) VALUES (?, ?)",
                (request_type, rectorate_id)
            )
            await db.commit()
    except Exception as e:
        print(f"Error setting request route: {e}")


async def log_murojaat(user_id, rectorate_id, request_type, role, content):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                INSERT INTO murojaatlar (user_id, rectorate_id, request_type, role, content)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, rectorate_id, request_type, role, content))
            await db.commit()
            return cursor.lastrowid  # murojaat_id ni qaytaradi
    except Exception as e:
        print(f"Error logging murojaat: {e}")
        return None
