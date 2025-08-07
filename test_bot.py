#!/usr/bin/env python3
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup
from config import API_ID, API_HASH, BOT_TOKEN

# إنشاء عميل البوت
bot = Client(
    "TestBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start") & filters.private)
async def start_test(client, message):
    print(f"[DEBUG] تم استلام /start من {message.from_user.id}")
    
    keyboard = [
        [("❲ صنع بوت ❳"), ("❲ حذف بوت ❳")],
        [("❲ استخراج جلسه ❳")],
        [("❲ السورس ❳"), ("❲ مطور السورس ❳")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await message.reply(
        "** ≭︰اهلا بك في مصنع البوتات **", 
        reply_markup=reply_markup, 
        quote=True
    )
    print(f"[DEBUG] تم الرد على {message.from_user.id}")

async def main():
    print("تشغيل البوت التجريبي...")
    await bot.start()
    print("البوت جاهز للاختبار! أرسل /start الآن")
    
    # إبقاء البوت نشطاً
    await idle()

if __name__ == "__main__":
    asyncio.run(main())