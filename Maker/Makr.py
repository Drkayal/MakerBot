import os
import sys
import asyncio
import subprocess
import re
import shutil
import logging
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ChatPrivileges, Message
from pyrogram.errors import PeerIdInvalid
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient as mongo_client
from random import randint
from pyrogram.raw.functions.phone import CreateGroupCall
from config import API_ID, API_HASH, MONGO_DB_URL, OWNER, OWNER_ID, OWNER_NAME, CHANNEL, GROUP, PHOTO, VIDEO, BOT_TOKEN

# إعداد السجل (logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة العميل الأساسي
bot = Client(
    "FactoryBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# تهيئة قاعدة البيانات
mongo_async = mongo_client(MONGO_DB_URL)
mongodb = mongo_async.AnonX
users_db = mongodb.tgusersdb
chats_db = mongodb.chats
bot_db = MongoClient(MONGO_DB_URL)["Yousef"].botpsb
mkchats_db = bot_db.chatss
blocked_db = bot_db.blocked
broadcasts_collection = bot_db["broadcasts"]
devs_collection = bot_db["devs"]

# متغيرات الحالة
off = False
Bots = []
mk = []
blocked = []
ch = CHANNEL

async def load_data():
    """تحميل البيانات الأولية من قاعدة البيانات"""
    global Bots, mk, blocked
    
    try:
        # تحميل البوتات
        bot_list = list(bot_db.find())
        for bot_data in bot_list:
            Bots.append([bot_data["username"], bot_data["dev"]])
        
        # تحميل الدردشات
        chat_list = list(mkchats_db.find())
        for chat_data in chat_list:
            mk.append(int(chat_data["chat_id"]))
        
        # تحميل المحظورين
        blocked_list = list(blocked_db.find())
        for blocked_data in blocked_list:
            blocked.append(int(blocked_data["user_id"]))
        
        logger.info("تم تحميل البيانات الأولية بنجاح")
    except Exception as e:
        logger.error(f"خطأ في تحميل البيانات: {e}")
        # تجاهل الخطأ والاستمرار

async def is_dev(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم مطورًا"""
    if user_id in OWNER_ID:
        return True
    dev = await devs_collection.find_one({"user_id": user_id})
    return bool(dev)

async def is_user(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم موجودًا في قاعدة البيانات"""
    return await users_db.find_one({"user_id": user_id})

async def add_new_user(user_id: int):
    """إضافة مستخدم جديد إلى قاعدة البيانات"""
    await users_db.insert_one({"user_id": user_id})

async def del_user(user_id: int):
    """حذف مستخدم من قاعدة البيانات"""
    await users_db.delete_one({"user_id": user_id})

async def get_users() -> list:
    """الحصول على قائمة جميع المستخدمين"""
    return [user["user_id"] async for user in users_db.find()]

async def set_broadcast_status(user_id: int, bot_id: str, key: str):
    """تعيين حالة البث"""
    await broadcasts_collection.update_one(
        {"user_id": user_id, "bot_id": bot_id},
        {"$set": {key: True}},
        upsert=True
    )

async def get_broadcast_status(user_id: int, bot_id: str, key: str) -> bool:
    """الحصول على حالة البث"""
    doc = await broadcasts_collection.find_one({"user_id": user_id, "bot_id": bot_id})
    return doc.get(key, False) if doc else False

async def delete_broadcast_status(user_id: int, bot_id: str, *keys: str):
    """حذف حالة البث"""
    unset_dict = {key: "" for key in keys}
    await broadcasts_collection.update_one(
        {"user_id": user_id, "bot_id": bot_id},
        {"$unset": unset_dict}
    )

def sanitize_path(path: str) -> str:
    """تنظيف المسارات لمنع هجمات الحقن"""
    return re.sub(r'[^a-zA-Z0-9_-]', '', path)

def is_screen_running(name: str) -> bool:
    """التحقق مما إذا كان البوت قيد التشغيل"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"python3 -m AnonXMusic.*{name}"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip()
    except subprocess.CalledProcessError:
        return False

async def safe_screen_command(command: list, cwd: str = None):
    """تنفيذ أوامر الشاشة بشكل آمن"""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode().strip(), stderr.decode().strip(), process.returncode
    except Exception as e:
        logger.error(f"خطأ في تنفيذ الأمر: {e}")
        return None, str(e), 1

@bot.on_message(filters.text & filters.private, group=5662)
async def cmd_handler(bot, msg):
    """معالج الأوامر النصية"""
    uid = msg.from_user.id
    if not await is_dev(uid):
        return

    if msg.text == "الغاء":
        await delete_broadcast_status(uid, bot.me.username, "broadcast", "pinbroadcast", "fbroadcast", "users_up")
        await msg.reply("» تم الغاء بنجاح", quote=True)

    elif msg.text == "❲ اخفاء الكيبورد ❳":
        await msg.reply("≭︰تم اخفاء الكيبورد ارسل /start لعرضه مره اخرى", 
                       reply_markup=ReplyKeyboardRemove(), 
                       quote=True)

    elif msg.text == "❲ الاحصائيات ❳":
        user_list = await get_users()
        dev_count = len(OWNER_ID) + await devs_collection.count_documents({})
        await msg.reply(
            f"**≭︰عدد الاعضاء  **{len(user_list)}\n"
            f"**≭︰عدد مطورين في المصنع  **{dev_count}",
            quote=True
        )

    elif msg.text == "❲ اذاعه ❳":
        await set_broadcast_status(uid, bot.me.username, "broadcast")
        await delete_broadcast_status(uid, bot.me.username, "fbroadcast", "pinbroadcast")
        await msg.reply("ارسل الاذاعه :-\n نص + ملف + متحركه + ملصق + صوره ", quote=True)

    elif msg.text == "❲ اذاعه بالتوجيه ❳":
        await set_broadcast_status(uid, bot.me.username, "fbroadcast")
        await delete_broadcast_status(uid, bot.me.username, "broadcast", "pinbroadcast")
        await msg.reply("ارسل الاذاعه :-\n نص + ملف + متحركه + ملصق + صوره ", quote=True)

    elif msg.text == "❲ اذاعه بالتثبيت ❳":
        await set_broadcast_status(uid, bot.me.username, "pinbroadcast")
        await delete_broadcast_status(uid, bot.me.username, "broadcast", "fbroadcast")
        await msg.reply("ارسل الاذاعه :-\n نص + ملف + متحركه + ملصق + صوره ", quote=True)

@bot.on_message(filters.private, group=368388)
async def broadcast_handler(bot, msg):
    """معالج عمليات البث"""
    uid = msg.from_user.id
    if not await is_dev(uid):
        return

    text = msg.text
    ignore = ["❲ اذاعه ❳", "❲ اذاعه بالتوجيه ❳", "❲ اذاعه بالتثبيت ❳", 
              "❲ الاحصائيات ❳", "❲ اخفاء الكيبورد ❳", "الغاء"]
    if text in ignore:
        return

    if await get_broadcast_status(uid, bot.me.username, "broadcast"):
        await delete_broadcast_status(uid, bot.me.username, "broadcast")
        message = await msg.reply("• جاري الإذاعة ..", quote=True)
        users_list = await get_users()
        total = len(users_list)
        
        for i, user_id in enumerate(users_list, 1):
            try:
                await msg.copy(int(user_id))
                progress = int((i / total) * 100)
                if i % 5 == 0 or i == total:
                    await message.edit(f"» نسبه الاذاعه {progress}%")
            except PeerIdInvalid:
                await del_user(int(user_id))
            except Exception as e:
                logger.error(f"فشل البث للمستخدم {user_id}: {e}")
        
        await message.edit("» تمت الاذاعه بنجاح")

    elif await get_broadcast_status(uid, bot.me.username, "pinbroadcast"):
        await delete_broadcast_status(uid, bot.me.username, "pinbroadcast")
        message = await msg.reply("» جاري الإذاعة ..", quote=True)
        users_list = await get_users()
        total = len(users_list)
        
        for i, user_id in enumerate(users_list, 1):
            try:
                m = await msg.copy(int(user_id))
                await m.pin(disable_notification=False, both_sides=True)
                progress = int((i / total) * 100)
                if i % 5 == 0 or i == total:
                    await message.edit(f"» نسبه الاذاعه {progress}%")
            except PeerIdInvalid:
                await del_user(int(user_id))
            except Exception as e:
                logger.error(f"فشل البث للمستخدم {user_id}: {e}")
        
        await message.edit("» تمت الاذاعه بنجاح")

    elif await get_broadcast_status(uid, bot.me.username, "fbroadcast"):
        await delete_broadcast_status(uid, bot.me.username, "fbroadcast")
        message = await msg.reply("» جاري الإذاعة ..", quote=True)
        users_list = await get_users()
        total = len(users_list)
        
        for i, user_id in enumerate(users_list, 1):
            try:
                await msg.forward(int(user_id))
                progress = int((i / total) * 100)
                if i % 5 == 0 or i == total:
                    await message.edit(f"• نسبه الاذاعه {progress}%")
            except PeerIdInvalid:
                await del_user(int(user_id))
            except Exception as e:
                logger.error(f"فشل البث للمستخدم {user_id}: {e}")
        
        await message.edit("» تمت الاذاعه بنجاح")

@bot.on_message(filters.command("start") & filters.private)
async def start_command(bot, msg):
    """معالج أمر /start"""
    print(f"[DEBUG] تم استلام أمر /start من المستخدم: {msg.from_user.id}")
    try:
        if not await is_user(msg.from_user.id):
            print(f"[DEBUG] مستخدم جديد: {msg.from_user.id}")
            await add_new_user(msg.from_user.id) 
            text = (
                f"** ≭︰  دخل عضو جديد لـ↫ مصنع   **\n\n"
                f"** ≭︰  الاسم : {msg.from_user.first_name}   **\n"
                f"** ≭︰  تاك : {msg.from_user.mention}   **\n"
                f"** ≭︰  الايدي : {msg.from_user.id} **"
            )
            user_count = len(await get_users())
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton(f" ≭︰عدد الاعضاء  {user_count}", 
                 callback_data=f"user_count_{msg.from_user.id}")]]
            )
            
            if msg.chat.id not in OWNER_ID:
                for user_id in OWNER_ID:
                    try:
                        await bot.send_message(
                            int(user_id), 
                            text, 
                            reply_markup=reply_markup
                        )
                    except Exception as e:
                        logger.error(f"فشل إرسال إشعار للمطور {user_id}: {e}")

        print(f"[DEBUG] قيمة off: {off}")
        print(f"[DEBUG] معرف المستخدم: {msg.chat.id}")
        print(f"[DEBUG] هل مطور: {await is_dev(msg.chat.id)}")
        
        # عرض واجهة المستخدم المناسبة
        if off:  # المصنع مغلق
            if not await is_dev(msg.chat.id):
                print(f"[DEBUG] المصنع مغلق والمستخدم ليس مطور")
                return await msg.reply_text(
                    f"**≭︰التنصيب المجاني معطل، راسل المبرمج ↫ @{OWNER[0]}**"
                )
            else:
                print(f"[DEBUG] المستخدم مطور - عرض لوحة المطور")
                keyboard = [
                    [("❲ صنع بوت ❳"), ("❲ حذف بوت ❳")],
                    [("❲ فتح المصنع ❳"), ("❲ قفل المصنع ❳")],
                    [("❲ ايقاف بوت ❳"), ("❲ تشغيل بوت ❳")],
                    [("❲ ايقاف البوتات ❳"), ("❲ تشغيل البوتات ❳")],
                    [("❲ البوتات المشتغلة ❳")],
                    [("❲ البوتات المصنوعه ❳"), ("❲ تحديث الصانع ❳")],
                    [("❲ الاحصائيات ❳")],
                    [("❲ رفع مطور ❳"), ("❲ تنزيل مطور ❳")],
                    [("❲ المطورين ❳")],
                    [("❲ اذاعه ❳"), ("❲ اذاعه بالتوجيه ❳"), ("❲ اذاعه بالتثبيت ❳")],
                    [("❲ استخراج جلسه ❳"), ("❲ الاسكرينات المفتوحه ❳")],
                    ["❲ 𝚄𝙿𝙳𝙰𝚃𝙴 𝙲𝙾𝙾𝙺𝙸𝙴𝚂 ❳", "❲ 𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙲𝙾𝙾𝙺𝙸𝙴𝚂 ❳"],
                    [("❲ السورس ❳"), ("❲ مطور السورس ❳")],
                    [("❲ اخفاء الكيبورد ❳")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                await msg.reply("** ≭︰اهلا بك عزيزي المطور  **", 
                               reply_markup=reply_markup, 
                               quote=True)
        else:  # المصنع مفتوح
            print(f"[DEBUG] المصنع مفتوح")
            if await is_dev(msg.chat.id):
                print(f"[DEBUG] مطور في المصنع المفتوح - عرض لوحة المطور")
                keyboard = [
                    [("❲ صنع بوت ❳"), ("❲ حذف بوت ❳")],
                    [("❲ فتح المصنع ❳"), ("❲ قفل المصنع ❳")],
                    [("❲ ايقاف بوت ❳"), ("❲ تشغيل بوت ❳")],
                    [("❲ ايقاف البوتات ❳"), ("❲ تشغيل البوتات ❳")],
                    [("❲ البوتات المشتغلة ❳")],
                    [("❲ البوتات المصنوعه ❳"), ("❲ تحديث الصانع ❳")],
                    [("❲ الاحصائيات ❳")],
                    [("❲ رفع مطور ❳"), ("❲ تنزيل مطور ❳")],
                    [("❲ المطورين ❳")],
                    [("❲ اذاعه ❳"), ("❲ اذاعه بالتوجيه ❳"), ("❲ اذاعه بالتثبيت ❳")],
                    [("❲ استخراج جلسه ❳"), ("❲ الاسكرينات المفتوحه ❳")],
                    ["❲ 𝚄𝙿𝙳𝙰𝚃𝙴 𝙲𝙾𝙾𝙺𝙸𝙴𝚂 ❳", "❲ 𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙲𝙾𝙾𝙺𝙸𝙴𝚂 ❳"],
                    [("❲ السورس ❳"), ("❲ مطور السورس ❳")],
                    [("❲ اخفاء الكيبورد ❳")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                await msg.reply("** ≭︰اهلا بك عزيزي المطور  **", 
                               reply_markup=reply_markup, 
                               quote=True)
            else:
                print(f"[DEBUG] عضو عادي - عرض لوحة العضو")
                keyboard = [
                    [("❲ صنع بوت ❳"), ("❲ حذف بوت ❳")],
                    [("❲ استخراج جلسه ❳")],
                    [("❲ السورس ❳"), ("❲ مطور السورس ❳")],
                    [("❲ اخفاء الكيبورد ❳")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                await msg.reply("** ≭︰اهلا بك عزيزي العضو  **", 
                               reply_markup=reply_markup, 
                               quote=True)
    except Exception as e:
        print(f"[ERROR] خطأ في معالج start: {e}")
        await msg.reply("حدث خطأ، حاول مرة أخرى")

# تم تحريك chat_manager إلى نهاية الملف

@bot.on_message(filters.command(["❲ السورس ❳"], ""))
async def source_info(client: Client, message: Message):
    """معلومات السورس"""
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❲ Help Group ❳", url=f"{GROUP}"),
                InlineKeyboardButton("❲ Source Ch ❳", url=f"{CHANNEL}"),
            ],
            [
                 InlineKeyboardButton(f"{OWNER_NAME}", url=f"https://t.me/{OWNER[0]}")
            ]
        ]
    )

    await message.reply_video(
        video=VIDEO,
        caption="**≭︰Welcome to Source Music **",
        reply_markup=keyboard,
    )

@bot.on_message(filters.command(["❲ مطور السورس ❳"], ""))
async def developer_info(client: Client, message: Message):
    """معلومات المطور"""
    try:
        async def get_user_info():
            user_id = OWNER_ID[0]
            user = await client.get_users(user_id)
            chat = await client.get_chat(user_id)

            name = user.first_name
            bio = chat.bio or "لا يوجد"

            usernames = []
            if hasattr(user, 'usernames') and user.usernames:
                usernames.extend([f"@{u.username}" for u in user.usernames])
            if user.username:
                usernames.append(f"@{user.username}")
            username_text = " ".join(usernames) if usernames else "لا يوجد"

            photo_path = None
            if user.photo:
                photo_path = await client.download_media(user.photo.big_file_id)

            return user.id, name, username_text, bio, photo_path

        user_id, name, username, bio, photo_path = await get_user_info()

        title = message.chat.title or message.chat.first_name
        chat_title = f"≯︰العضو ↫ ❲ {message.from_user.mention} ❳\n≯︰اسم المجموعه ↫ ❲ {title} ❳" if message.from_user else f"≯︰اسم المجموعه ↫ ❲ {title} ❳"

        try:
            await client.send_message(
                user_id,
                f"**≯︰هناك من بحاجه للمساعده**\n{chat_title}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(f"❲ {title} ❳", url=f"https://t.me/{message.chat.username}")]]
                ) if message.chat.username else None
            )
        except Exception as e:
            logger.error(f"فشل إرسال رسالة للمطور: {e}")

        if photo_path:
            await message.reply_photo(
                photo=photo_path,
                caption=(
                    f"**≯︰Information programmer  ↯.\n          ━─━─────━─────━─━\n"
                    f"≯︰Name ↬ ❲ {name} ❳** \n"
                    f"**≯︰User ↬ ❲ {username} ❳**\n"
                    f"**≯︰Bio ↬ ❲ {bio} ❳**"
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(f"❲ {name} ❳", user_id=user_id)]]
                )
            )
            os.remove(photo_path)
        else:
            await message.reply_text(
                f"**≯︰Information programmer  ↯.\n          ━─━─────━─────━─━\n"
                f"≯︰Name ↬ ❲ {name} ❳** \n"
                f"**≯︰User ↬ ❲ {username} ❳**\n"
                f"**≯︰Bio ↬ ❲ {bio} ❳**",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(f"❲ {name} ❳", user_id=user_id)]]
                )
            )

    except Exception as e:
        logger.error(f"خطأ في معلومات المطور: {e}")
        await message.reply_text("حدث خطأ أثناء جلب معلومات المطور.")

@bot.on_message(filters.command("❲ رفع مطور ❳", ""))
async def add_developer(client, message: Message):
    """رفع مطور جديد"""
    if not await is_dev(message.from_user.id):
        return await message.reply("**≭︰ليس لديك صلاحيات**")

    m = await client.ask(message.chat.id, "**≭︰ارسل معرف المستخدم الآن**")
    username = m.text.replace("@", "")
    
    try:
        user = await client.get_chat(username)
        if await is_dev(user.id):
            return await message.reply("**≭︰هذا المستخدم مطور بالفعل**")
        
        await devs_collection.insert_one({"user_id": user.id})
        return await message.reply(f"**≭︰تم رفع {user.first_name} كمطور بنجاح**")
    except Exception as e:
        logger.error(f"خطأ في رفع المطور: {e}")
        return await message.reply("**≭︰فشل في العثور على المستخدم، تحقق من المعرف**")

@bot.on_message(filters.command("❲ تنزيل مطور ❳", ""))
async def remove_developer(client, message: Message):
    """تنزيل مطور"""
    if not await is_dev(message.from_user.id):
        return await message.reply("**≭︰ليس لديك صلاحيات**")

    m = await client.ask(message.chat.id, "**≭︰ارسل المعرف الآن**")
    username = m.text.replace("@", "")
    
    try:
        user = await client.get_chat(username)
        if not await is_dev(user.id):
            return await message.reply("**≭︰هذا المستخدم ليس مطوراً**")

        await devs_collection.delete_one({"user_id": user.id})
        return await message.reply(f"**≭︰تم تنزيل {user.first_name} من المطورين بنجاح**")
    except Exception as e:
        logger.error(f"خطأ في تنزيل المطور: {e}")
        return await message.reply("**≭︰فشل في العثور على المستخدم، تحقق من المعرف**")

@bot.on_message(filters.command("❲ المطورين ❳", ""))
async def list_developers(client, message: Message):
    """عرض قائمة المطورين"""
    if not await is_dev(message.from_user.id):
        return await message.reply("<b>≭︰ليس لديك صلاحيات</b>")

    response = "<b><u>≭︰قائمة المطورين :</u></b>\n\n"
    # المطورين الأساسيين
    for i, uid in enumerate(OWNER_ID, start=1):
        try:
            user = await client.get_users(uid)
            name = user.first_name or "No Name"
            mention = f'<a href="tg://user?id={uid}">{name}</a>'
            response += f"<b>{i}- {mention}</b> (المالك)\n"
        except Exception as e:
            logger.error(f"خطأ في جلب معلومات المطور {uid}: {e}")
            continue
    
    # المطورين الإضافيين
    devs = []
    async for dev in devs_collection.find({"user_id": {"$nin": OWNER_ID}}):
        devs.append(dev)
    
    if devs:
        for i, dev in enumerate(devs, start=len(OWNER_ID)+1):
            try:
                user = await client.get_users(dev["user_id"])
                name = user.first_name or "No Name"
                mention = f'<a href="tg://user?id={user.id}">{name}</a>'
                response += f"<b>{i}- {mention}</b>\n"
            except Exception as e:
                logger.error(f"خطأ في جلب معلومات المطور {dev['user_id']}: {e}")
                continue
    else:
        response += "\n<b>≭︰لا يوجد مطورين مضافين بعد</b>"

    await message.reply_text(response, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command(["❲ فتح المصنع ❳", "❲ قفل المصنع ❳"], "") & filters.private)
async def toggle_factory(client, message):
    """فتح/قفل المصنع"""
    global off
    if not await is_dev(message.from_user.id):
        return
    
    if message.text == "❲ فتح المصنع ❳":
        off = False
        await message.reply_text("** ≭︰تم فتح المصنع **")
    else:
        off = True
        await message.reply_text("** ≭︰تم قفل المصنع **")

@bot.on_message(filters.command("❲ صنع بوت ❳", "") & filters.private)
async def create_bot(client, message):
    """صنع بوت جديد"""
    if not await is_dev(message.from_user.id):
        for bot_data in Bots:
            if int(bot_data[1]) == message.from_user.id:
                return await message.reply_text("<b> ≭︰لـقـد قـمت بـصـنع بـوت مـن قـبل </b>")

    try:
        # طلب التوكن والتحقق منه
        ask = await client.ask(message.chat.id, "<b> ≭︰ارسـل تـوكـن الـبوت </b>", timeout=120)
        TOKEN = ask.text.strip()
        
        # التحقق من صحة التوكن
        if not re.match(r'^[0-9]+:[a-zA-Z0-9_-]{35}$', TOKEN):
            return await message.reply_text("<b> ≭︰توكن البوت غير صحيح! يجب أن يكون بالشكل: 1234567890:AbCdEfGhIjKlMnOpQrStUvWxYz</b>")
        
        temp_bot = Client(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN, in_memory=True)
        try:
            await temp_bot.start()
            bot_me = await temp_bot.get_me()
            username = bot_me.username
            if not username:
                return await message.reply_text("<b> ≭︰لم يتم الحصول على اسم المستخدم للبوت!</b>")
            await temp_bot.stop()
        except Exception as e:
            logger.error(f"خطأ في التوكن: {e}")
            return await message.reply_text(f"<b> ≭︰توكن البوت غير صحيح: {str(e)}</b>")

        # طلب كود الجلسة والتحقق منه
        ask = await client.ask(message.chat.id, "<b> ≭︰ارسـل كـود الـجلسـه </b>", timeout=120)
        SESSION = ask.text.strip()
        
        # التحقق من صحة كود الجلسة (طول أولي)
        if len(SESSION) < 200:
            return await message.reply_text("<b> ≭︰كود الجلسة قصير جداً! تأكد من نسخ الكود كاملاً</b>")
        
        try:
            print(f"[DEBUG] فحص الجلسة: طول الكود = {len(SESSION)}")
            user_client = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION, in_memory=True)
            await user_client.start()
            user_me = await user_client.get_me()
            print(f"[DEBUG] تم التحقق من الجلسة بنجاح: {user_me.first_name}")
            await user_client.stop()
        except Exception as e:
            logger.error(f"خطأ في الجلسة: {e}")
            print(f"[DEBUG] خطأ في الجلسة: {e}")
            return await message.reply_text(f"<b> ≭︰كود الجلسة غير صحيح: {str(e)}</b>")

        # طلب آيدي المطور (للمطورين الأساسيين فقط)
        Dev = message.from_user.id
        if message.from_user.id in OWNER_ID:
            ask = await client.ask(message.chat.id, "<b> ≭︰ارسـل ايدي المطور </b>", timeout=120)
            try:
                Dev = int(ask.text.strip())
                await client.get_users(Dev)
            except Exception as e:
                logger.error(f"خطأ في آيدي المطور: {e}")
                return await message.reply_text("<b>يرجى إرسال آيدي المطور الصحيح (أرقام فقط)</b>")

        bot_id = username
        bot_dir = f"Maked/{sanitize_path(bot_id)}"
        
        # حذف المجلد القديم إذا كان موجوداً
        if os.path.exists(bot_dir):
            shutil.rmtree(bot_dir, ignore_errors=True)

        # التحقق من وجود مجلد القالب
        if not os.path.exists("Make"):
            return await message.reply_text("<b> ≭︰خطأ: مجلد القالب 'Make' غير موجود!</b>")

        try:
            shutil.copytree("Make", bot_dir)
        except Exception as e:
            logger.error(f"خطأ في نسخ القالب: {e}")
            return await message.reply_text(f"<b>خطأ في إنشاء مجلد البوت: {str(e)}</b>")

        # إنشاء مجموعة التخزين
        try:
            user_client = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION, in_memory=True)
            await user_client.start()
            
            # إنشاء المجموعة
            group = await user_client.create_supergroup("تخزين ميوزك", "مجموعة تخزين سورس ميوزك")
            group_link = await user_client.export_chat_invite_link(group.id)
            
            # إضافة البوت إلى المجموعة
            await user_client.add_chat_members(group.id, username)
            
            # ترقية البوت في المجموعة
            await user_client.promote_chat_member(
                group.id, 
                username, 
                ChatPrivileges(
                    can_change_info=True,
                    can_invite_users=True,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=True,
                    can_manage_chat=True,
                    can_manage_video_chats=True
                )
            )
            
            # إنشاء المكالمة الجماعية
            await user_client.invoke(
                CreateGroupCall(
                    peer=await user_client.resolve_peer(group.id),
                    random_id=randint(10000000, 999999999)
                )
            )
            
            # إرسال رسالة تأكيد
            await user_client.send_message(group.id, "تم فتح الاتصال لتفعيل الحساب.")
            await user_client.stop()
        except Exception as e:
            logger.error(f"خطأ في إنشاء مجموعة التخزين: {e}")
            shutil.rmtree(bot_dir, ignore_errors=True)
            return await message.reply_text(f"<b>خطأ في إنشاء مجموعة التخزين: {str(e)}</b>")

        # كتابة ملف البيئة
        env_path = os.path.join(bot_dir, ".env")
        try:
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_content = (
                    f"ID = {bot_id}\n"
                    f"BOT_TOKEN = {TOKEN}\n"
                    f"STRING_SESSION = {SESSION}\n"
                    f"OWNER_ID = {Dev}\n"
                    f"LOGGER_ID = {group.id}\n"
                    f"API_ID = {API_ID}\n"
                    f"API_HASH = {API_HASH}\n"
                    f"MONGO_DB_URL = {MONGO_DB_URL}"
                )
                env_file.write(env_content)
        except Exception as e:
            logger.error(f"خطأ في كتابة ملف .env: {e}")
            shutil.rmtree(bot_dir, ignore_errors=True)
            return await message.reply_text(f"<b>خطأ في كتابة ملف الإعدادات: {str(e)}</b>")

        # اختبار التشغيل (لمدة أطول)
        test_msg = await message.reply("**≭︰جاري اختبار تشغيل البوت، هذه العملية قد تستغرق حتى 30 ثانية...**")
        cmd = ["python3", "-c", "import AnonXMusic; print('Bot test passed successfully')"]
        _, stderr, returncode = await safe_screen_command(cmd, cwd=bot_dir)
        
        if returncode != 0:
            await test_msg.edit(f"<b>فشل اختبار تشغيل البوت: {stderr[:1000]}</b>")
            shutil.rmtree(bot_dir, ignore_errors=True)
            return
        
        # التشغيل الرسمي
        screen_name = sanitize_path(bot_id)
        
        # أولاً: تثبيت المتطلبات
        install_msg = await message.reply("**≭︰جاري تثبيت متطلبات البوت...**")
        install_cmd = ["bash", "-c", f"cd {bot_dir} && pip3 install --no-cache-dir -r requirements.txt"]
        stdout, stderr, returncode = await safe_screen_command(install_cmd)
        
        if returncode != 0:
            await install_msg.edit(f"<b>فشل تثبيت المتطلبات: {stderr[:1000]}</b>")
            shutil.rmtree(bot_dir, ignore_errors=True)
            return
        
        # ثانياً: اختبار التشغيل السريع
        await install_msg.edit("**≭︰جاري اختبار التشغيل...**")
        test_cmd = ["bash", "-c", f"cd {bot_dir} && timeout 15 python3 -m AnonXMusic"]
        stdout, stderr, returncode = await safe_screen_command(test_cmd)
        
        # عرض نتيجة الاختبار
        if returncode != 0:
            await install_msg.edit(f"<b>فشل اختبار التشغيل:</b>\n\n<code>{stderr[:1500] if stderr else 'لا توجد تفاصيل'}</code>")
            # عدم حذف البوت للتشخيص
            return
        
        # ثالثاً: التشغيل في الخلفية
        start_msg = await install_msg.edit("**≭︰جاري التشغيل الرسمي للبوت...**")
        cmd = ["bash", "-c", f"cd {bot_dir} && nohup python3 -m AnonXMusic > {bot_dir}/bot.log 2>&1 &"]
        stdout, stderr, returncode = await safe_screen_command(cmd)
        
        if returncode != 0:
            await start_msg.edit(f"<b>فشل التشغيل الرسمي: {stderr[:1000]}</b>")
            shutil.rmtree(bot_dir, ignore_errors=True)
            return
        
        # التحقق من تشغيل البوت
        await asyncio.sleep(10)  # وقت أطول للتحقق
        if is_screen_running(bot_id):
            await start_msg.edit("**≭︰تم تشغيل البوت بنجاح!**")
        else:
            # قراءة ملف السجل لمعرفة السبب
            log_file = f"{bot_dir}/bot.log"
            error_info = "لا توجد معلومات إضافية"
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        log_content = f.read()[-500:]  # آخر 500 حرف من السجل
                        error_info = log_content
                except:
                    pass
            
            await start_msg.edit(f"<b>فشل التشغيل: البوت لم يبدأ بشكل صحيح</b>\n\n<code>السجل:\n{error_info}</code>")
            # عدم حذف البوت للتشخيص
            # shutil.rmtree(bot_dir, ignore_errors=True)
            return

        # تحديث القوائم
        Bots.append([bot_id, Dev])
        await bot_db.insert_one({"username": bot_id, "dev": Dev})

        # إرسال الإشعارات
        success_text = (
            f"**≭︰تم تشغيل البوت بنجاح**\n\n"
            f"**≭︰معرف البوت ↫ @{username}\n"
            f"**≭︰رابط مجموعة التخزين ↫ [اضغط هنا]({group_link})\n"
            f"**≭︰آيدي المطور ↫ {Dev}\n"
            f"**≭︰يمكنك مراقبة السجلات بـ: screen -r {screen_name}"
        )
        
        await message.reply_text(success_text, disable_web_page_preview=True)
        
        for chat in OWNER:
            try:
                await client.send_message(
                    chat,
                    f"<b> ≭︰تنصيب جديد </b>\n\n"
                    f"<b>معرف البوت ↫ </b>@{bot_id}\n"
                    f"<b>ايدي المطور ↫ </b>{Dev}\n"
                    f"<b>الصانع ↫ </b>{message.from_user.mention}\n"
                    f"<b>رابط المجموعة ↫ </b>{group_link}"
                )
            except Exception as e:
                logger.error(f"فشل إرسال إشعار للمطور {chat}: {e}")

    except asyncio.TimeoutError:
        await message.reply_text("**≭︰انتهى الوقت المحدد للعملية!**")
    except Exception as e:
        logger.error(f"خطأ في صنع البوت: {e}")
        if os.path.exists(bot_dir):
            shutil.rmtree(bot_dir, ignore_errors=True)
        await message.reply_text(f"<b>فشل التنصيب: {str(e)}</b>")

@bot.on_message(filters.command("❲ حذف بوت ❳", "") & filters.private)
async def delete_bot(client, message):
    """حذف بوت"""
    if not await is_dev(message.from_user.id):
        for bot_data in Bots:
            if int(bot_data[1]) == message.from_user.id:
                bot_id = bot_data[0]
                bot_dir = f"Maked/{sanitize_path(bot_id)}"
                shutil.rmtree(bot_dir, ignore_errors=True)
                
                # إيقاف الشاشة
                screen_name = sanitize_path(bot_id)
                await safe_screen_command(["screen", "-XS", screen_name, "quit"])
                
                # تحديث القوائم
                Bots.remove(bot_data)
                await bot_db.delete_one({"username": bot_id})
                
                return await message.reply_text("** ≭︰تم حذف بوتك من المصنع   **.")
        return await message.reply_text("** ≭︰لم تقم ب صنع بوت   **")
    
    try:
        ask = await client.ask(message.chat.id, "** ≭︰ ارسل يوزر البوت   **", timeout=15)
        bot_username = ask.text.replace("@", "").strip()
    except asyncio.TimeoutError:
        return
    
    bot_id = sanitize_path(bot_username)
    bot_dir = f"Maked/{bot_id}"
    
    # حذف من القوائم
    for bot_data in Bots:
        if bot_data[0] == bot_username:
            Bots.remove(bot_data)
            break
    
    await bot_db.delete_one({"username": bot_username})
    
    # حذف الملفات
    if os.path.exists(bot_dir):
        shutil.rmtree(bot_dir, ignore_errors=True)
    
    # إيقاف الشاشة
    await safe_screen_command(["screen", "-XS", bot_id, "quit"])
    
    await message.reply_text("** ≭︰ تم حـذف البـوت بنـجاح   **")

@bot.on_message(filters.command("❲ البوتات المصنوعه ❳", ""))
async def list_bots(client, message):
    """عرض البوتات المصنوعة"""
    if not await is_dev(message.from_user.id):
        return
    
    if not Bots:
        return await message.reply_text("** ≭︰ لا يوجد بوتات مصنوعه عزيزي المطور   **")
    
    text = "** ≭︰ اليك قائمة البوتات المصنوعه **\n\n"
    
    for i, bot_data in enumerate(Bots, 1):
        bot_username = bot_data[0]
        owner_id = bot_data[1]
        try:
            owner = await client.get_users(owner_id)
            owner_name = owner.first_name or "غير معروف"
            owner_mention = f"@{owner.username}" if owner.username else owner_name
        except:
            owner_mention = "غير متوفر"
        
        text += f"{i}- @{bot_username} : {owner_mention}\n"
    
    await message.reply_text(text)

@bot.on_message(filters.command(["❲ الاسكرينات المفتوحه ❳"], ""))
async def list_screens(client: Client, message):
    """عرض جلسات الشاشة النشطة"""
    if not await is_dev(message.from_user.id):
        return
    
    try:
        result = subprocess.run(
            ["screen", "-ls"],
            capture_output=True,
            text=True,
            check=True
        )
        screens = result.stdout
        await message.reply_text(f"** ≭︰جلسات الشاشة النشطة:**\n\n```\n{screens}\n```")
    except subprocess.CalledProcessError as e:
        logger.error(f"خطأ في جلب جلسات الشاشة: {e}")
        await message.reply_text("** ≭︰فشل في جلب جلسات الشاشة**")

@bot.on_message(filters.command("❲ تحديث الصانع ❳", ""))
async def update_factory(client: Client, message):
    """تحديث الصانع"""
    if message.from_user.id not in OWNER_ID: 
        return await message.reply_text("** ≭︰ هذا الامر يخص المالك فقط **")
    
    try:
        msg = await message.reply("** ≭︰جاري تحديث المصنع **")
        args = [sys.executable, "main.py"] 
        os.execle(sys.executable, *args, os.environ)
    except Exception as e:
        logger.error(f"خطأ في التحديث: {e}")
        await msg.edit_text(f"** ≭︰فشل تحديث المصنع: {e} **")

@bot.on_message(filters.command("❲ تشغيل بوت ❳", ""))
async def start_specific_bot(client, message):
    """تشغيل بوت معين"""
    if not await is_dev(message.from_user.id):
        return await message.reply_text("** ≭︰هذا الامر يخص المطور فقط **")

    if not os.path.exists('Maked'):
        return await message.reply_text("**~ خطأ: لا يوجد مجلد Maked.**")

    bots_to_start = []
    for folder in os.listdir("Maked"):
        if re.search('[Bb][Oo][Tt]', folder, re.IGNORECASE):
            if not is_screen_running(folder):
                bots_to_start.append(folder)

    if not bots_to_start:
        return await message.reply_text("** ≭︰لا يوجد أي بوت متوقف حالياً لتشغيله **")

    buttons = [
        [InlineKeyboardButton(f"تشغيل @{bot}", callback_data=f"startbot:{bot}")]
        for bot in bots_to_start
    ]
    await message.reply_text(
        "** ≭︰اختر البوت الذي تريد تشغيله:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query(filters.regex("^startbot:(.*)"))
async def start_selected_bot(client, callback_query):
    """تشغيل البوت المحدد"""
    bot_username = callback_query.data.split(":")[1]
    bot_dir = f"Maked/{sanitize_path(bot_username)}"

    if not os.path.exists(bot_dir):
        await callback_query.answer("** ≭︰البوت غير موجود **")
        return

    if is_screen_running(bot_username):
        await callback_query.answer(f"** ≭︰البوت @{bot_username} يعمل بالفعل **")
    else:
        screen_name = sanitize_path(bot_username)
        cmd = [
            "screen", "-dmS", screen_name, 
            "bash", "-c", 
            f"cd {bot_dir} && python3 -m AnonXMusic"
        ]
        stdout, stderr, returncode = await safe_screen_command(cmd)
        
        if returncode == 0:
            await callback_query.answer(f"** ≭︰تم تشغيل البوت @{bot_username} بنجاح **")
        else:
            await callback_query.answer(f"** ≭︰فشل تشغيل البوت: {stderr} **")

@bot.on_message(filters.command("❲ ايقاف بوت ❳", "") & filters.private)
async def stop_bot(client, message):
    """ايقاف بوت معين"""
    if not await is_dev(message.from_user.id):
        return await message.reply_text("** ≭︰هذا الامر يخص المطور فقط **")
    
    try:
        ask = await client.ask(message.chat.id, "** ≭︰ارسـل مـعرف البوت **", timeout=300)
        bot_username = ask.text.replace("@", "").strip()
    except asyncio.TimeoutError:
        return
    
    if not bot_username:
        await message.reply_text("** ≭︰خطأ: يجب عليك تحديد اسم البوت **")
        return

    bot_found = False
    for folder in os.listdir("Maked"):
        if re.search('[Bb][Oo][Tt]', folder, re.IGNORECASE) and bot_username in folder:
            bot_found = True
            # إيقاف البوت باستخدام pkill
            bot_dir = f"/workspace/Maked/{folder}"
            await safe_screen_command(["pkill", "-f", f"python3 -m AnonXMusic.*{folder}"])
            await message.reply_text(f"** ≭︰تم ايقاف البوت @{bot_username} بنجاح **")
            break

    if not bot_found:
        await message.reply_text(f"** ≭︰لم يتم العثور على البوت @{bot_username} **")

@bot.on_message(filters.command("❲ البوتات المشتغلة ❳", ""))
async def running_bots(client, message):
    """عرض البوتات المشتغلة"""
    if not await is_dev(message.from_user.id):
        await message.reply_text("** ≭︰هذا الامر يخص المطور **")
        return

    if not os.path.exists('Maked'):
        await message.reply_text("**~ خطأ: لا يوجد مجلد Maked.**")
        return

    running_bots = []
    for folder in os.listdir("Maked"):
        if re.search('[Bb][Oo][Tt]', folder, re.IGNORECASE) and is_screen_running(folder):
            running_bots.append(folder)

    if not running_bots:
        await message.reply_text("** ≭︰لا يوجد أي بوت يعمل حالياً **")
    else:
        bots_list = "\n".join(f"- @{b}" for b in running_bots)
        await message.reply_text(f"** ≭︰البوتات المشتغلة حالياً:**\n\n{bots_list}")

@bot.on_message(filters.command("❲ تشغيل البوتات ❳", ""))
async def start_all_bots(client, message):
    """تشغيل جميع البوتات"""
    if not await is_dev(message.from_user.id):
        await message.reply_text("** ≭︰هذا الامر يخص المطور **")
        return
    
    if not os.path.exists('Maked'):
        await message.reply_text("**~ خطأ: لا يوجد مجلد Maked.**")
        return

    count = 0
    for folder in os.listdir("Maked"):
        if re.search('[Bb][Oo][Tt]', folder, re.IGNORECASE):
            if is_screen_running(folder):
                continue
            
            screen_name = sanitize_path(folder)
            cmd = [
                "screen", "-dmS", screen_name, 
                "bash", "-c", 
                f"cd Maked/{folder} && python3 -m AnonXMusic"
            ]
            stdout, stderr, returncode = await safe_screen_command(cmd)
            
            if returncode == 0:
                count += 1

    if count == 0:
        await message.reply_text("** ≭︰كل البوتات تعمل بالفعل، لا يوجد بوتات لتشغيلها **")
    else:
        await message.reply_text(f"** ≭︰تم تشغيل {count} بوت بنجاح **")

@bot.on_message(filters.command("❲ ايقاف البوتات ❳", ""))
async def stop_all_bots(client, message):
    """ايقاف جميع البوتات"""
    if not await is_dev(message.from_user.id):
        await message.reply_text("** ≭︰هذا الامر يخص المطور **")
        return
    
    if not os.path.exists('Maked'):
        await message.reply_text("**~ خطأ: لا يوجد مجلد Maked.**")
        return
    
    count = 0
    for folder in os.listdir("Maked"):
        if re.search('[Bb][Oo][Tt]', folder, re.IGNORECASE):
            screen_name = sanitize_path(folder)
            await safe_screen_command(["screen", "-XS", screen_name, "quit"])
            count += 1
    
    if count == 0:
        await message.reply_text("** ≭︰لم يتم ايقاف أي بوتات **")
    else:
        await message.reply_text(f"** ≭︰تم ايقاف {count} بوت بنجاح **")

# بدء التحميل الأولي للبيانات عند التشغيل
async def on_start():
    await load_data()
    logger.info("تم بدء تشغيل صانع البوتات")

# معالج عام للرسائل الخاصة - يجب أن يكون في النهاية
@bot.on_message(filters.private, group=999)
async def chat_manager(client, message):
    """إدارة الدردشات والمستخدمين"""
    # إضافة المستخدم لقاعدة البيانات
    if message.chat.id not in mk:
        mk.append(message.chat.id)
        await mkchats_db.insert_one({"chat_id": message.chat.id})

    # التحقق من الحظر
    if message.chat.id in blocked:
        return await message.reply_text("انت محظور من صانع عزيزي")

    # استثناء المطورين من فحص الاشتراك
    if await is_dev(message.from_user.id):
        return

    # التحقق من الاشتراك للمستخدمين العاديين فقط
    try:
        await client.get_chat_member("@k55dd", message.from_user.id)
    except Exception as e:
        logger.error(f"خطأ في التحقق من العضوية: {e}")
        return await message.reply_text(
            f"**يجب ان تشترك ف قناة السورس أولا \n https://t.me/k55dd**"
        )

if __name__ == "__main__":
    bot.run()