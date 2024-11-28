from aiogram import Bot
from aiogram.types import ChatMember

async def check_membership(bot: Bot, channel_username: str, user_id: int):
    try:
        # Kanalga a'zo bo'lishini tekshirish
        member: ChatMember = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        
        # A'zo bo'lish holatini tekshirish
        if member.status in ['member', 'administrator', 'creator']:
            return True  # Foydalanuvchi kanalga a'zo
        return False  # Foydalanuvchi kanalga a'zo emas
    
    except Exception as e:
        print(f"Error checking membership for {channel_username}: {e}")
        return False
