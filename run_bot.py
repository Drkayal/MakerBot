#!/usr/bin/env python3
import asyncio
import logging
from pyrogram import idle

# إعداد السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("بدء تشغيل البوت...")
        
        # استيراد البوت والدوال من Makr.py
        from Maker.Makr import bot, on_start
        
        # تشغيل البوت
        await bot.start()
        logger.info("تم تشغيل البوت بنجاح")
        
        # تحميل البيانات الأولية
        await on_start()
        logger.info("تم تحميل البيانات الأولية")
        
        # إبقاء البوت نشطاً
        await idle()
        
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())