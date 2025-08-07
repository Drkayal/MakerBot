#!/usr/bin/env python3
import requests
import time
import json
from config import BOT_TOKEN

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
    
    def get_updates(self):
        """الحصول على التحديثات"""
        url = f"{self.api_url}/getUpdates"
        params = {"offset": self.last_update_id + 1, "timeout": 10}
        
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get("ok"):
                return data.get("result", [])
            else:
                print(f"خطأ في API: {data}")
                return []
        except Exception as e:
            print(f"خطأ في الاتصال: {e}")
            return []
    
    def send_message(self, chat_id, text, reply_markup=None):
        """إرسال رسالة"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"خطأ في إرسال الرسالة: {e}")
            return None
    
    def create_keyboard(self):
        """إنشاء كيبورد المطور الكامل"""
        return {
            "keyboard": [
                [{"text": "❲ صنع بوت ❳"}, {"text": "❲ حذف بوت ❳"}],
                [{"text": "❲ فتح المصنع ❳"}, {"text": "❲ قفل المصنع ❳"}],
                [{"text": "❲ ايقاف بوت ❳"}, {"text": "❲ تشغيل بوت ❳"}],
                [{"text": "❲ ايقاف البوتات ❳"}, {"text": "❲ تشغيل البوتات ❳"}],
                [{"text": "❲ البوتات المشتغلة ❳"}],
                [{"text": "❲ البوتات المصنوعه ❳"}, {"text": "❲ تحديث الصانع ❳"}],
                [{"text": "❲ الاحصائيات ❳"}],
                [{"text": "❲ رفع مطور ❳"}, {"text": "❲ تنزيل مطور ❳"}],
                [{"text": "❲ المطورين ❳"}],
                [{"text": "❲ اذاعه ❳"}, {"text": "❲ اذاعه بالتوجيه ❳"}, {"text": "❲ اذاعه بالتثبيت ❳"}],
                [{"text": "❲ استخراج جلسه ❳"}, {"text": "❲ الاسكرينات المفتوحه ❳"}],
                [{"text": "❲ 𝚄𝙿𝙳𝙰𝚃𝙴 𝙲𝙾𝙾𝙺𝙸𝙴𝚂 ❳"}, {"text": "❲ 𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙲𝙾𝙾𝙺𝙸𝙴𝚂 ❳"}],
                [{"text": "❲ السورس ❳"}, {"text": "❲ مطور السورس ❳"}],
                [{"text": "❲ اخفاء الكيبورد ❳"}]
            ],
            "resize_keyboard": True
        }
    
    def handle_message(self, message):
        """معالج الرسائل"""
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "")
        
        print(f"[INFO] رسالة من {user_id}: {text}")
        
        # التحقق من المطور
        OWNER_IDS = [985612253]  # ضع آيدي المطور هنا
        is_dev = user_id in OWNER_IDS
        
        if text == "/start":
            if is_dev:
                keyboard = self.create_keyboard()
                self.send_message(
                    chat_id,
                    "** ≭︰اهلا بك عزيزي المطور **\n\n✅ البوت يعمل بنجاح!",
                    keyboard
                )
            else:
                simple_keyboard = {
                    "keyboard": [
                        [{"text": "❲ صنع بوت ❳"}],
                        [{"text": "❲ السورس ❳"}]
                    ],
                    "resize_keyboard": True
                }
                self.send_message(
                    chat_id,
                    "** ≭︰اهلا بك عزيزي العضو **",
                    simple_keyboard
                )
        
        elif text == "❲ صنع بوت ❳":
            self.send_message(chat_id, "🤖 **صنع البوت**\n\nالمعذرة، هذه الميزة قيد التطوير بسبب مشاكل في النظام.\n\nيرجى المحاولة لاحقاً.")
        
        elif text == "❲ السورس ❳":
            self.send_message(chat_id, "📂 **السورس**\n\nقناة السورس: https://t.me/k55dd")
        
        elif text == "❲ مطور السورس ❳":
            self.send_message(chat_id, "👨‍💻 **مطور السورس**\n\n@AAAKP")
        
        else:
            self.send_message(chat_id, "❓ أمر غير مفهوم. أرسل /start للبدء.")
    
    def run(self):
        """تشغيل البوت"""
        print("🚀 بدء تشغيل البوت...")
        print("✅ البوت جاهز للاستقبال!")
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        self.handle_message(update["message"])
                
                time.sleep(1)  # تأخير قصير
                
            except KeyboardInterrupt:
                print("\n⛔ تم إيقاف البوت")
                break
            except Exception as e:
                print(f"❌ خطأ: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = TelegramBot(BOT_TOKEN)
    bot.run()