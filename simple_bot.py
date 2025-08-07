import asyncio
from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN

# بوت بسيط للاختبار
bot = Client(
    name="simple_test",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="/tmp"  # استخدام مجلد مؤقت
)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("البوت يعمل!")

async def main():
    print("بدء تشغيل البوت البسيط...")
    await bot.start()
    print("البوت جاهز!")
    
    # إرسال رسالة اختبار
    try:
        await bot.send_message(985612253, "البوت متصل ويعمل!")
        print("تم إرسال رسالة اختبار")
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")
    
    await asyncio.sleep(10)
    await bot.stop()
    print("تم إيقاف البوت")

if __name__ == "__main__":
    asyncio.run(main())