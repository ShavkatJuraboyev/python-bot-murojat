from database.db import is_admin as db_is_admin

async def is_admin(user_id: int) -> bool:
    return await db_is_admin(user_id)