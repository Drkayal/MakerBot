#!/usr/bin/env python3
"""
بوت باستخدام webhook لتجنب مشاكل التوقيت
"""
import logging
from flask import Flask, request, jsonify
import requests
import json
from config import BOT_TOKEN

# إعداد السجل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# إعدادات البوت
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_URL = "https://your-app-url.com/webhook"  # يجب تغييرها

def send_message(chat_id, text, reply_markup=None):
    """إرسال رسالة عبر Telegram API"""
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    response = requests.post(url, data=data)
    return response.json()

def create_keyboard():
    """إنشاء كيبورد الإعدادات"""
    return {
        "keyboard": [
            [{"text": "❲ صنع بوت ❳"}, {"text": "❲ حذف بوت ❳"}],
            [{"text": "❲ فتح المصنع ❳"}, {"text": "❲ قفل المصنع ❳"}],
            [{"text": "❲ استخراج جلسه ❳"}],
            [{"text": "❲ السورس ❳"}, {"text": "❲ مطور السورس ❳"}]
        ],
        "resize_keyboard": True
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    """معالج webhook"""
    try:
        update = request.get_json()
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            text = message.get('text', '')
            
            logger.info(f"رسالة من {user_id}: {text}")
            
            # معالجة أمر /start
            if text == '/start':
                keyboard = create_keyboard()
                send_message(
                    chat_id,
                    "** ≭︰اهلا بك عزيزي المطور **\n\nالبوت يعمل الآن بـ webhook!",
                    keyboard
                )
            
            # معالجة باقي الأوامر
            elif text == "❲ صنع بوت ❳":
                send_message(chat_id, "⚡ قريباً سيتم إضافة هذه الميزة...")
            
            elif text == "❲ السورس ❳":
                send_message(chat_id, "📁 السورس: https://github.com/example")
            
            else:
                send_message(chat_id, "👋 مرحباً! أرسل /start للبدء")
        
        return jsonify({"ok": True})
    
    except Exception as e:
        logger.error(f"خطأ في webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """فحص صحة الخدمة"""
    return jsonify({"status": "ok", "message": "البوت يعمل"})

@app.route('/set_webhook')
def set_webhook():
    """تعيين webhook"""
    url = f"{TELEGRAM_API}/setWebhook"
    data = {"url": WEBHOOK_URL}
    response = requests.post(url, data=data)
    return jsonify(response.json())

if __name__ == '__main__':
    print("🚀 بدء تشغيل البوت بـ webhook...")
    print("ℹ️  لتشغيل البوت، تحتاج إلى:")
    print("   1. رفع الكود على خدمة مثل Heroku أو Railway")
    print("   2. تحديث WEBHOOK_URL")
    print("   3. زيارة /set_webhook لتعيين webhook")
    
    # تشغيل محلي للاختبار
    app.run(host='0.0.0.0', port=8080, debug=True)