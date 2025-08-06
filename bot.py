from pyrogram import Client, idle
from pyromod import listen
import os
from config import API_ID, API_HASH, BOT_TOKEN

main_bot = Client(
    "B7R",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="Maker")
)

async def start_bot():
    print("[INFO]: جاري تشغيل البوت")
    await main_bot.start()
    print("[INFO]: بدأ تشغيل")
    # استدعاء دالة التحميل الأولي
    try:
        from Maker.Makr import on_start
        await on_start()
    except Exception as e:
        print(f"[ERROR]: خطأ في التحميل الأولي: {e}")
    await idle()


bot_id = BOT_TOKEN.split(":")[0]    
    