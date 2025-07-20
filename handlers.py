import json
import logging
import asyncio
import time
import os
from aiogram import Router, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import Command, CommandStart

# Config dan import qilish (xavfsiz versiya)
from config import (
    MAIN_CHANNEL_ID, 
    MODEL_CHANNEL_MAP, 
    ALWAYS_SEND_TO, 
    CHANNEL_NAMES,
    BOT_OWNER_ID,  # config.py dan import - hard-code emas!
    BOT_VERSION
)

router = Router()
logging.basicConfig(level=logging.INFO)
MAPPING_FILE = "mapping.json"

# Admin config fayllar
ADMIN_CONFIG_FILE = "admin_config.json"
MODEL_KEYWORDS_FILE = "model_keywords.json"
REGION_KEYWORDS_FILE = "region_keywords.json"
ADMIN_USERS_FILE = "admin_users.json"

# Global lock for file operations
file_lock = asyncio.Lock()

# Admin config yuklash/saqlash
async def load_admin_config():
    """Admin config ni yuklash"""
    try:
        with open(ADMIN_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config - config.py dan olish
        default_config = {
            "model_channels": dict(MODEL_CHANNEL_MAP),
            "region_channels": {},  # Yangi - viloyat kanallari
            "always_send_to": list(ALWAYS_SEND_TO),
            "channel_names": dict(CHANNEL_NAMES)
        }
        await save_admin_config(default_config)
        return default_config

async def save_admin_config(config):
    """Admin config ni saqlash"""
    try:
        with open(ADMIN_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Admin config saqlashda xato: {e}")

# Model keywords yuklash/saqlash
async def load_model_keywords():
    """Model keywords ni yuklash"""
    try:
        with open(MODEL_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default keywords
        default_keywords = {
            "damas": ["damas", "дамас", "#damas", "#дамас"],
            "jentra": ["jentra", "жентра", "#jentra", "#жентра", "gentra", "#gentra"],
            "malibu": ["malibu", "малибу", "#malibu", "#малибу"],
            "spark": ["spark", "спарк", "#spark", "#спарк"],
            "nexia": ["nexia", "нексия", "#nexia", "#нексия"]
        }
        await save_model_keywords(default_keywords)
        return default_keywords

async def save_model_keywords(keywords):
    """Model keywords ni saqlash"""
    try:
        with open(MODEL_KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Model keywords saqlashda xato: {e}")

# Region keywords yuklash/saqlash
async def load_region_keywords():
    """Viloyat keywords ni yuklash"""
    try:
        with open(REGION_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default region keywords
        default_keywords = {
            "toshkent": ["toshkent", "ташкент", "tashkent", "toshkent shahar", "тошкент"],
            "samarqand": ["samarqand", "самарканд", "samarkand", "samarqand shahar"],
            "buxoro": ["buxoro", "бухара", "bukhara", "buxoro shahar"],
            "andijon": ["andijon", "андижан", "andijan", "andijon shahar"],
            "fargona": ["fargona", "фергана", "fergana", "farg'ona"]
        }
        await save_region_keywords(default_keywords)
        return default_keywords

async def save_region_keywords(keywords):
    """Viloyat keywords ni saqlash"""
    try:
        with open(REGION_KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Region keywords saqlashda xato: {e}")

# Viloyat detection funksiyasi
async def detect_region(text: str) -> str | None:
    """Viloyat detection - keywords asosida"""
    if not text:
        return None
        
    text = text.lower()
    keywords = await load_region_keywords()
    
    for region, region_keywords in keywords.items():
        for keyword in region_keywords:
            if keyword.lower() in text:
                return region
    return None

async def detect_model_advanced(text: str) -> str | None:
    """Yangi model detection - keywords asosida"""
    if not text:
        return None
        
    text = text.lower()
    keywords = await load_model_keywords()
    
    for model, model_keywords in keywords.items():
        for keyword in model_keywords:
            if keyword.lower() in text:
                return model
    return None

# Dynamic config olish
async def get_current_config():
    """Hozirgi config ni olish"""
    admin_config = await load_admin_config()
    return {
        "model_channels": admin_config.get("model_channels", MODEL_CHANNEL_MAP),
        "region_channels": admin_config.get("region_channels", {}),  # Yangi
        "always_send_to": admin_config.get("always_send_to", ALWAYS_SEND_TO),
        "channel_names": admin_config.get("channel_names", CHANNEL_NAMES)
    }

# Admin users yuklash/saqlash
async def load_admin_users():
    """Admin foydalanuvchilar ro'yxatini yuklash"""
    try:
        with open(ADMIN_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default - faqat kanal adminlari
        default_users = {
            "channel_admins": True,  # Kanal adminlari ham admin
            "custom_admins": []      # Qo'shimcha admin user ID lar
        }
        await save_admin_users(default_users)
        return default_users

async def save_admin_users(users):
    """Admin foydalanuvchilar ro'yxatini saqlash"""
    try:
        with open(ADMIN_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Admin users saqlashda xato: {e}")

# Yaxshilangan admin tekshirish
async def is_admin(user_id: int, bot) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish - owner, kanal va custom adminlar"""
    try:
        # 1. Bot owner tekshiruvi (eng yuqori huquq)
        if user_id == BOT_OWNER_ID:
            return True
        
        admin_users = await load_admin_users()
        
        # 2. Custom admin ro'yxatida tekshirish
        if user_id in admin_users.get("custom_admins", []):
            return True
        
        # 3. Kanal adminlari tekshiruvi (agar yoqilgan bo'lsa)
        if admin_users.get("channel_admins", True):
            member = await bot.get_chat_member(MAIN_CHANNEL_ID, user_id)
            return member.status in ["administrator", "creator"]
            
        return False
    except:
        # Xato bo'lsa, owner tekshiruvi
        return user_id == BOT_OWNER_ID

# Optimallashtirilgan mapping saqlash (katta kanallar uchun)
async def save_mapping_optimized(data):
    """Mapping ni kichik hajmda saqlash"""
    async with file_lock:
        try:
            # Backup yaratish
            import shutil
            try:
                shutil.copy(MAPPING_FILE, f"{MAPPING_FILE}.backup")
            except FileNotFoundError:
                pass
            
            # Eski mapping ni yuklash
            old_mapping = {}
            try:
                with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                    old_mapping = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            # Yangi ma'lumotlarni qo'shish va timestamp qo'shish
            current_timestamp = int(time.time())
            
            for post_id, post_data in data.items():
                if post_id not in old_mapping:
                    # Yangi post - timestamp va siqilgan format
                    if isinstance(post_data, dict) and "reply_to" not in post_data:
                        # Oddiy post - faqat kerakli ma'lumotlar
                        old_mapping[post_id] = {
                            "c": post_data,  # channels - qisqa nom
                            "t": current_timestamp  # timestamp - qisqa nom
                        }
                    elif isinstance(post_data, dict) and "reply_to" in post_data:
                        # Reply post  
                        old_mapping[post_id] = {
                            "r": post_data["reply_to"],  # reply_to - qisqa
                            "c": post_data["targets"],   # channels - qisqa
                            "t": current_timestamp       # timestamp - qisqa
                        }
                else:
                    old_mapping[post_id] = data[post_id]
            
            # Atomic write - temp fayl orqali
            temp_file = f"{MAPPING_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(old_mapping, f, ensure_ascii=False, separators=(',', ':'))  # Compact JSON
            
            # Temp faylni asosiy faylga ko'chirish
            os.replace(temp_file, MAPPING_FILE)
            
        except Exception as e:
            logging.error(f"❌ Mapping saqlashda xato: {e}")

# Optimallashtirilgan mapping yuklash
async def load_mapping_optimized():
    """Siqilgan mapping ni yuklash va o'qish"""
    async with file_lock:
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                compressed_mapping = json.load(f)
            
            # Eski formatdan yangi formatga o'tkazish
            normal_mapping = {}
            for post_id, post_data in compressed_mapping.items():
                if isinstance(post_data, dict):
                    if "c" in post_data and "t" in post_data:
                        if "r" in post_data:
                            # Reply format
                            normal_mapping[post_id] = {
                                "reply_to": post_data["r"],
                                "targets": post_data["c"],
                                "_timestamp": post_data["t"]
                            }
                        else:
                            # Oddiy post format
                            normal_mapping[post_id] = post_data["c"]
                            normal_mapping[post_id]["_timestamp"] = post_data["t"]
                    else:
                        # Eski format - o'zgartirishsiz
                        normal_mapping[post_id] = post_data
                else:
                    normal_mapping[post_id] = post_data
            
            return normal_mapping
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logging.error("❌ JSON fayl buzilgan, yangi mapping yaratilmoqda")
            return {}

# Mapping yuklash (optimallashtirilgan)
async def load_mapping():
    return await load_mapping_optimized()

# Mapping saqlash (optimallashtirilgan)  
async def save_mapping(data):
    await save_mapping_optimized(data)

# Aggressive 45 kunlik tozalash (katta kanallar uchun)
async def aggressive_45day_cleanup():
    """Katta kanallar uchun - 45 kundan eski mapping larni tezda o'chirish"""
    try:
        mapping = await load_mapping_optimized()
        if not mapping:
            return 0
            
        current_time = int(time.time())
        cutoff_time = current_time - (45 * 24 * 60 * 60)  # 45 kun
        
        old_entries = []
        total_size = len(mapping)
        
        for post_id, post_data in list(mapping.items()):
            if post_id in ["reply_to", "targets"]:
                continue
                
            try:
                # Timestamp tekshirish
                timestamp = current_time  # Default - hozirgi vaqt
                
                if isinstance(post_data, dict):
                    timestamp = post_data.get("_timestamp", timestamp)
                    if timestamp is None or timestamp == 0:
                        # Eski format yoki noto'g'ri timestamp
                        try:
                            post_id_int = int(post_id)
                            # Taxminiy vaqt - Telegram message ID asosida
                            if post_id_int < 1000000:
                                # Juda eski ID - 45 kundan eski deb hisoblash
                                timestamp = cutoff_time - 1
                            else:
                                timestamp = current_time
                        except ValueError:
                            timestamp = cutoff_time - 1  # Noto'g'ri format - o'chirish
                
                # 45 kundan eski ekanligini tekshirish
                if timestamp < cutoff_time:
                    old_entries.append(post_id)
                    
            except Exception as e:
                # Xato bo'lsa, o'chirish
                old_entries.append(post_id)
                continue
        
        # Eski yozuvlarni o'chirish
        cleaned_count = 0
        if old_entries:
            fresh_mapping = await load_mapping_optimized()
            
            for old_post_id in old_entries:
                if old_post_id in fresh_mapping:
                    del fresh_mapping[old_post_id]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                await save_mapping_optimized(fresh_mapping)
                logging.info(f"🗑 Aggressive tozalash: {cleaned_count}/{total_size} ta eski yozuv o'chirildi")
                
                # Mapping fayl hajmini ko'rsatish
                try:
                    file_size = os.path.getsize(MAPPING_FILE) / (1024 * 1024)  # MB
                    logging.info(f"💾 Mapping fayl hajmi: {file_size:.2f} MB")
                except:
                    pass
        
        return cleaned_count
                
    except Exception as e:
        logging.error(f"❌ Aggressive tozalashda xato: {e}")
        return 0

# Kunlik tozalash (45 kundan eski mapping lar uchun)
async def daily_mapping_cleanup(bot):
    """Kuniga bir marta 45 kundan eski mapping larni tozalash"""
    while True:
        try:
            # 24 soat (1 kun) kutish
            await asyncio.sleep(24 * 60 * 60)
            
            mapping = await load_mapping_optimized()
            if not mapping:
                continue
                
            mapping_size = len(mapping)
            logging.info(f"📊 Kunlik mapping tekshiruvi: {mapping_size} ta yozuv")
            
            # 45 kunlik tozalash
            cleaned = await aggressive_45day_cleanup()
            
            if cleaned > 0:
                new_mapping = await load_mapping_optimized()
                new_size = len(new_mapping)
                logging.info(f"✅ Kunlik tozalash tugadi: {cleaned} ta eski yozuv o'chirildi")
                logging.info(f"📊 Mapping hajmi: {mapping_size} → {new_size}")
                
                # Fayl hajmini ko'rsatish
                try:
                    file_size = os.path.getsize(MAPPING_FILE) / (1024 * 1024)  # MB
                    logging.info(f"💾 Mapping fayl hajmi: {file_size:.2f} MB")
                except:
                    pass
            else:
                logging.info("✅ Kunlik tekshiruv: 45 kundan eski mapping yozuv yo'q")
            
        except Exception as e:
            logging.error(f"❌ Kunlik mapping tozalashda xato: {e}")

# Auto-delete checker (faqat kunlik mapping tozalash)
async def start_auto_delete_checker(bot):
    """Faqat kunlik mapping tozalash"""
    asyncio.create_task(daily_mapping_cleanup(bot))
    logging.info("🔄 Kunlik mapping tozalash tizimi yoqildi (45 kun)")

# Test komandalar
@router.message(Command("ping"))
async def ping(msg: Message):
    await msg.answer("Pong! Bot ishlayapti")

@router.message(Command("test_admin"))
async def test_admin(msg: Message, bot):
    admin_status = await is_admin(msg.from_user.id, bot)
    await msg.answer(f"Admin: {admin_status}\nUser ID: {msg.from_user.id}")

# Asosiy kanalga yangi post (reply emas)
@router.channel_post(F.chat.id == MAIN_CHANNEL_ID, ~F.reply_to_message)
async def handle_post(msg: Message, bot):
    try:
        logging.info(f"🆕 Yangi post aniqlandi: {msg.message_id}")
        
        # Model va viloyat detection
        model = await detect_model_advanced(msg.text or msg.caption or "")
        region = await detect_region(msg.text or msg.caption or "")
        
        config = await get_current_config()
        targets = set(config["always_send_to"])

        # Model kanallari qo'shish
        if model and model in config["model_channels"]:
            targets.update(config["model_channels"][model])
            logging.info(f"🎯 Model aniqlandi: {model}")
        
        # Viloyat kanallari qo'shish
        if region and region in config["region_channels"]:
            targets.update(config["region_channels"][region])
            logging.info(f"🗺️ Viloyat aniqlandi: {region}")
        
        if model or region:
            logging.info(f"📍 Targets: {targets} (Model: {model}, Viloyat: {region})")
        else:
            logging.info(f"🎯 Model/Viloyat aniqlanmadi, faqat ALWAYS_SEND_TO: {targets}")

        # Mapping'ni OLDIN yuklash
        mapping = await load_mapping()
        post_mapping = {}
        successful_targets = []

        for chat_id in targets:
            try:
                sent = await bot.copy_message(chat_id, msg.chat.id, msg.message_id)
                post_mapping[str(chat_id)] = sent.message_id
                successful_targets.append(chat_id)
                logging.info(f"✅ Post yuborildi: {chat_id} → {sent.message_id}")
            except Exception as e:
                logging.error(f"❌ Post yuborishda xato {chat_id}: {e}")

        # Faqat muvaffaqiyatli yuborilgan postlar uchun mapping saqlash
        if post_mapping:
            # Mapping'ni QAYTA yuklash (boshqa jarayonlar o'zgartirgan bo'lishi mumkin)
            fresh_mapping = await load_mapping()
            fresh_mapping[str(msg.message_id)] = post_mapping
            await save_mapping(fresh_mapping)
            
            logging.info(f"✅ Post mapping saqlandi: {msg.message_id}")
            logging.info(f"📋 Mapping ma'lumotlari: {post_mapping}")
            
            # Tekshirish uchun mapping'ni qayta yuklash
            verify_mapping = await load_mapping()
            if str(msg.message_id) in verify_mapping:
                logging.info(f"✅ Mapping tekshirildi - muvaffaqiyatli saqlandi")
            else:
                logging.error(f"❌ Mapping tekshiruvi - saqlanmagan!")
        else:
            logging.warning(f"⚠️ Hech qanday post yuborilmadi: {msg.message_id}")
            
    except Exception as e:
        logging.error(f"❌ POSTDA XATO: {e}")
        import traceback
        logging.error(traceback.format_exc())

# Asosiy kanalga reply
@router.channel_post(F.chat.id == MAIN_CHANNEL_ID, F.reply_to_message)
async def handle_reply(msg: Message, bot):
    try:
        # Reply ekanligini tekshirish
        if not msg.reply_to_message:
            logging.warning("⚠️ Reply to message yo'q")
            return
            
        reply_to_id = msg.reply_to_message.message_id
        reply_to = str(reply_to_id)
        
        logging.info(f"📨 Reply aniqlandi: {msg.message_id} → {reply_to}")
        
        # Mappingni yuklash
        mapping = await load_mapping()
        logging.info(f"📋 Mapping keys: {list(mapping.keys())}")
        
        # Agar mapping'da yo'q bo'lsa
        if reply_to not in mapping:
            logging.warning(f"⚠️ Reply uchun mos post topilmadi: {reply_to}")
            
            # Qo'shimcha debug ma'lumotlari
            logging.info(f"🔍 Qidirilayotgan kalit: '{reply_to}' (type: {type(reply_to)})")
            debug_keys = [f"'{k}' (type: {type(k)})" for k in mapping.keys()]
            logging.info(f"🔍 Mavjud kalitlar: {debug_keys}")
            
            # Kichik kechikish va qayta yuklash
            await asyncio.sleep(0.2)
            mapping = await load_mapping()
            
            if reply_to not in mapping:
                logging.error(f"❌ Reply uchun mos post hali ham topilmadi: {reply_to}")
                
                # Raqamli kalitlarni tekshirish
                int_key = int(reply_to)
                if int_key in mapping:
                    logging.info(f"🔧 Integer kalit topildi: {int_key}")
                    reply_to = int_key
                else:
                    logging.error(f"📋 Mavjud mapping keys: {list(mapping.keys())}")
                    return

        original_mapping = mapping[reply_to]
        logging.info(f"📋 Original mapping: {original_mapping}")
        
        reply_map = {}
        
        for chat_id_str, target_msg_id in original_mapping.items():
            # "reply_to" va "targets" kalitlarini o'tkazib yuborish
            if chat_id_str in ["reply_to", "targets", "_timestamp"]:
                continue
                
            chat_id = int(chat_id_str)
            try:
                sent = await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=msg.chat.id,
                    message_id=msg.message_id,
                    reply_to_message_id=target_msg_id
                )
                reply_map[chat_id_str] = sent.message_id
                logging.info(f"✅ Reply yuborildi: {chat_id} → {target_msg_id} (yangi: {sent.message_id})")
            except Exception as e:
                logging.error(f"❌ Reply nusxalashda xato {chat_id}: {e}")

        if reply_map:
            # Mapping ni qayta yuklash (boshqa jarayonlar tomonidan o'zgarishi mumkin)
            mapping = await load_mapping()
            mapping[str(msg.message_id)] = {
                "reply_to": str(reply_to), 
                "targets": reply_map
            }
            await save_mapping(mapping)
            logging.info(f"✅ Reply mapping saqlandi: {msg.message_id} → {reply_map}")
        else:
            logging.warning(f"⚠️ Hech qanday reply yuborilmadi: {msg.message_id}")

    except Exception as e:
        logging.error(f"❌ REPLYDA XATO: {e}")
        import traceback
        logging.error(traceback.format_exc())

# Asosiy kanalda post edit qilinganda - faqat adminlar
@router.edited_channel_post(F.chat.id == MAIN_CHANNEL_ID)
async def handle_edit_post(msg: Message, bot):
    # Channel post da from_user yo'q, shuning uchun admin tekshiruvini o'tkazib yuboramiz
    # Chunki faqat channel adminlari edit qila oladi
    
    try:
        post_id = str(msg.message_id)
        logging.info(f"✏️ Post edit aniqlandi: {post_id}")
        
        # Mapping dan postni topish
        mapping = await load_mapping()
        
        if post_id not in mapping:
            logging.warning(f"⚠️ Edit qilingan post mapping'da topilmadi: {post_id}")
            return
            
        post_mapping = mapping[post_id]
        logging.info(f"📋 Edit post mapping: {post_mapping}")
        
        edit_count = 0
        failed_count = 0
        
        # Post turini aniqlash va nusxalarni edit qilish
        if isinstance(post_mapping, dict) and "reply_to" in post_mapping:
            # Bu reply xabar - reply nusxalarini edit qilish
            logging.info(f"📩 Reply xabar edit qilinmoqda: {post_id}")
            targets = post_mapping.get("targets", {})
            
            for chat_id_str, target_msg_id in targets.items():
                try:
                    chat_id = int(chat_id_str)
                    
                    # Reply postni edit qilish
                    if msg.text:
                        # Faqat matn
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            text=msg.text,
                            entities=msg.entities
                        )
                    elif msg.photo:
                        # Rasm + caption
                        from aiogram.types import InputMediaPhoto
                        media = InputMediaPhoto(
                            media=msg.photo[-1].file_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            media=media
                        )
                    elif msg.video:
                        # Video + caption
                        from aiogram.types import InputMediaVideo
                        media = InputMediaVideo(
                            media=msg.video.file_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            media=media
                        )
                    elif msg.document:
                        # Document + caption
                        from aiogram.types import InputMediaDocument
                        media = InputMediaDocument(
                            media=msg.document.file_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            media=media
                        )
                    elif msg.caption:
                        # Faqat caption
                        await bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                    
                    edit_count += 1
                    logging.info(f"✅ Reply edit qilindi: {chat_id} → {target_msg_id}")
                    
                    # Rate limit uchun kichik kechikish
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    failed_count += 1
                    logging.error(f"❌ Reply edit qilishda xato {chat_id}: {e}")
        else:
            # Oddiy post - barcha nusxalarni edit qilish
            channels_to_edit = {}
            
            # Eski yoki yangi format bo'yicha channels olish
            if isinstance(post_mapping, dict) and "c" in post_mapping:
                # Compressed format
                channels_to_edit = post_mapping["c"]
            else:
                # Oddiy format
                channels_to_edit = post_mapping
            
            for chat_id_str, target_msg_id in channels_to_edit.items():
                if chat_id_str in ["_timestamp", "t"]:
                    continue
                    
                try:
                    chat_id = int(chat_id_str)
                    
                    # Postni edit qilish
                    if msg.text:
                        # Faqat matn
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            text=msg.text,
                            entities=msg.entities
                        )
                    elif msg.photo:
                        # Rasm + caption
                        from aiogram.types import InputMediaPhoto
                        media = InputMediaPhoto(
                            media=msg.photo[-1].file_id,  # Eng katta o'lcham
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            media=media
                        )
                    elif msg.video:
                        # Video + caption
                        from aiogram.types import InputMediaVideo
                        media = InputMediaVideo(
                            media=msg.video.file_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            media=media
                        )
                    elif msg.document:
                        # Document + caption
                        from aiogram.types import InputMediaDocument
                        media = InputMediaDocument(
                            media=msg.document.file_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            media=media
                        )
                    elif msg.caption:
                        # Faqat caption (fallback)
                        await bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=target_msg_id,
                            caption=msg.caption,
                            caption_entities=msg.caption_entities
                        )
                    else:
                        # Boshqa media turlari
                        logging.info(f"📷 Qo'llab-quvvatlanmagan media edit: {chat_id} → {target_msg_id}")
                        continue
                    
                    edit_count += 1
                    logging.info(f"✅ Post edit qilindi: {chat_id} → {target_msg_id}")
                    
                    # Rate limit uchun kichik kechikish
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    failed_count += 1
                    logging.error(f"❌ Post edit qilishda xato {chat_id}: {e}")
        
        if edit_count > 0:
            logging.info(f"✅ Edit jarayoni tugadi: {edit_count} ta muvaffaqiyatli, {failed_count} ta xato")
        else:
            logging.warning(f"⚠️ Hech qanday post edit qilinmadi: {post_id}")
            
    except Exception as e:
        logging.error(f"❌ EDIT POSTDA XATO: {e}")
        import traceback
        logging.error(traceback.format_exc())

# Forward qilinganda tugma chiqarish - faqat adminlar
@router.message(F.forward_from_chat.id == MAIN_CHANNEL_ID)
async def handle_forward(msg: Message, bot):
    # Admin tekshiruvi
    if not await is_admin(msg.from_user.id, bot):
        return  # Admin bo'lmasa, delete tugmasi chiqmaydi
    
    mapping = await load_mapping()
    source_id = str(msg.forward_from_message_id)

    if source_id in mapping:
        # Post mappingida mavjudligini tekshirish
        post_mapping = mapping[source_id]
        
        # Reply xabar ekanligini tekshirish
        if isinstance(post_mapping, dict) and "reply_to" in post_mapping:
            # Bu reply xabar
            reply_info = f"\n📩 Bu reply xabar (javob: {post_mapping['reply_to']})"
        else:
            # Bu oddiy post
            reply_info = ""
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O'chirilsin", callback_data=f"delete:{source_id}")]
        ])
        await msg.reply(f"Bu xabar nishon kanallarda ham mavjud.{reply_info} O'chirilsinmi?", reply_markup=keyboard)
    else:
        await msg.reply("❌ Bu xabar mapping'da topilmadi yoki allaqachon o'chirilgan.")

# Tugma bosilganda postni o'chirish (asosiy post + barcha nusxalar)
@router.callback_query(F.data.startswith("delete:"))
async def handle_delete_btn(callback: CallbackQuery, bot):
    source_id = callback.data.split(":")[1]
    mapping = await load_mapping()

    if source_id in mapping:
        post_mapping = mapping[source_id]
        deleted_count = 0
        
        # Reply xabar yoki oddiy post ekanligini tekshirish
        if isinstance(post_mapping, dict) and "reply_to" in post_mapping:
            # Bu reply xabar - "targets" ichidagi nusxalarni o'chirish
            logging.info(f"🔄 Reply xabarni o'chirish: {source_id}")
            targets = post_mapping.get("targets", {})
            
            for chat_id_str, msg_id in targets.items():
                try:
                    await bot.delete_message(int(chat_id_str), msg_id)
                    deleted_count += 1
                    logging.info(f"✅ Reply nusxasi o'chirildi: {chat_id_str} → {msg_id}")
                except Exception as e:
                    logging.error(f"❌ Reply nusxasini o'chirishda xato {chat_id_str}: {e}")
        else:
            # Bu oddiy post - to'g'ridan-to'g'ri nusxalarni o'chirish
            logging.info(f"📝 Oddiy postni o'chirish: {source_id}")
            
            for chat_id_str, msg_id in post_mapping.items():
                if chat_id_str in ["reply_to", "targets", "_timestamp"]:
                    continue
                try:
                    await bot.delete_message(int(chat_id_str), msg_id)
                    deleted_count += 1
                    logging.info(f"✅ Post nusxasi o'chirildi: {chat_id_str} → {msg_id}")
                except Exception as e:
                    logging.error(f"❌ Post nusxasini o'chirishda xato {chat_id_str}: {e}")
        
        # Asosiy kanaldagi xabarni ham o'chirish
        try:
            await bot.delete_message(MAIN_CHANNEL_ID, int(source_id))
            deleted_count += 1
            logging.info(f"✅ Asosiy xabar o'chirildi: {source_id}")
        except Exception as e:
            logging.error(f"❌ Asosiy xabarni o'chirishda xato: {e}")

        # Mapping'dan o'chirish
        fresh_mapping = await load_mapping()
        if source_id in fresh_mapping:
            del fresh_mapping[source_id]
            await save_mapping(fresh_mapping)
            logging.info(f"✅ Mapping'dan o'chirildi: {source_id}")

        if deleted_count > 1:
            await callback.message.edit_text(f"✅ Xabar va {deleted_count-1} ta nusxasi o'chirildi!")
        else:
            await callback.message.edit_text("✅ Xabar o'chirildi!")
        
    else:
        await callback.answer("❌ Bu xabar mapping'da topilmadi!", show_alert=True)

# Admin panel komandalar

# Admin panel menusi
@router.message(Command("admin"))
async def cmd_admin_panel(msg: Message, bot):
    """Admin panel asosiy menusi"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Adminlar", callback_data="admin_users")],
        [InlineKeyboardButton(text="🤖 Modellar", callback_data="admin_models")],
        [InlineKeyboardButton(text="🗺️ Viloyatlar", callback_data="admin_regions")],
        [InlineKeyboardButton(text="📢 Umumiy kanallar", callback_data="admin_always")],
        [InlineKeyboardButton(text="🔤 Kalit so'zlar", callback_data="admin_keywords")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")]
    ])
    
    await msg.answer(
        "🎛️ <b>Admin Panel</b>\n\n"
        "Botni boshqarish uchun tugmalardan foydalaning:",
        reply_markup=keyboard
    )

# Komanda orqali model qo'shish
@router.message(Command("add_model"))
async def cmd_add_model(msg: Message, bot):
    """Model qo'shish: /add_model <nom> <kanal_id>"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    args = msg.text.split()
    if len(args) != 3:
        await msg.answer("📝 Foydalanish: /add_model <model_nomi> <kanal_id>\n\n"
                        "Misol: /add_model nexia -1002123456789")
        return
    
    model_name = args[1].lower()
    try:
        channel_id = int(args[2])
    except ValueError:
        await msg.answer("❌ Kanal ID raqam bo'lishi kerak!")
        return
    
    # Config ni yangilash
    config = await load_admin_config()
    if model_name not in config["model_channels"]:
        config["model_channels"][model_name] = []
    
    if channel_id not in config["model_channels"][model_name]:
        config["model_channels"][model_name].append(channel_id)
        await save_admin_config(config)
        
        await msg.answer(f"✅ <b>{model_name.upper()}</b> modeli uchun kanal qo'shildi!\n"
                        f"📢 Kanal: <code>{channel_id}</code>")
    else:
        await msg.answer(f"⚠️ Bu kanal allaqachon <b>{model_name.upper()}</b> modelida mavjud!")

# Komanda orqali kalit so'z qo'shish
@router.message(Command("add_keyword"))
async def cmd_add_keyword(msg: Message, bot):
    """Kalit so'z qo'shish: /add_keyword <model> <so'z>"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    args = msg.text.split(maxsplit=2)
    if len(args) != 3:
        await msg.answer("📝 Foydalanish: /add_keyword <model> <kalit_soz>\n\n"
                        'Misol: /add_keyword nexia "ZAZ Nexia"')
        return
    
    model_name = args[1].lower()
    keyword = args[2].strip('"')
    
    # Keywords ni yangilash
    keywords = await load_model_keywords()
    if model_name not in keywords:
        keywords[model_name] = []
    
    if keyword.lower() not in [k.lower() for k in keywords[model_name]]:
        keywords[model_name].append(keyword)
        await save_model_keywords(keywords)
        
        await msg.answer(f"✅ <b>{model_name.upper()}</b> modeli uchun kalit so'z qo'shildi!\n"
                        f"🔤 Kalit so'z: <code>{keyword}</code>")
    else:
        await msg.answer(f"⚠️ Bu kalit so'z allaqachon <b>{model_name.upper()}</b> modelida mavjud!")

# Komanda orqali umumiy kanal qo'shish
@router.message(Command("add_always"))
async def cmd_add_always(msg: Message, bot):
    """Umumiy kanal qo'shish: /add_always <kanal_id>"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /add_always <kanal_id>\n\n"
                        "Misol: /add_always -1002123456789")
        return
    
    try:
        channel_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Kanal ID raqam bo'lishi kerak!")
        return
    
    # Config ni yangilash
    config = await load_admin_config()
    if channel_id not in config["always_send_to"]:
        config["always_send_to"].append(channel_id)
        await save_admin_config(config)
        
        await msg.answer(f"✅ Umumiy kanal qo'shildi!\n"
                        f"📢 Kanal: <code>{channel_id}</code>")
    else:
        await msg.answer("⚠️ Bu kanal allaqachon umumiy kanallar ro'yxatida mavjud!")

# Modellar ro'yxati
@router.message(Command("list_models"))
async def cmd_list_models(msg: Message, bot):
    """Barcha modellar ro'yxati"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    config = await load_admin_config()
    models = config.get("model_channels", {})
    channel_names = config.get("channel_names", {})
    
    if not models:
        await msg.answer("📭 Hech qanday model topilmadi!")
        return
    
    text = "🤖 <b>Barcha modellar:</b>\n\n"
    for model, channels in models.items():
        text += f"🔹 <b>{model.upper()}</b> ({len(channels)} ta kanal):\n"
        for channel_id in channels:
            name = channel_names.get(str(channel_id), f"Kanal {channel_id}")
            text += f"   • {name}\n"
        text += "\n"
    
    await msg.answer(text)

# Kalit so'zlar ro'yxati
@router.message(Command("list_keywords"))
async def cmd_list_keywords(msg: Message, bot):
    """Barcha kalit so'zlar ro'yxati"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    keywords = await load_model_keywords()
    
    if not keywords:
        await msg.answer("📭 Hech qanday kalit so'z topilmadi!")
        return
    
    text = "🔤 <b>Barcha kalit so'zlar:</b>\n\n"
    for model, words in keywords.items():
        text += f"🔹 <b>{model.upper()}</b> ({len(words)} ta):\n"
        for word in words:
            text += f"   • <code>{word}</code>\n"
        text += "\n"
    
    await msg.answer(text)

# Umumiy kanallar ro'yxati
@router.message(Command("list_always"))
async def cmd_list_always(msg: Message, bot):
    """Umumiy kanallar ro'yxati"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    config = await load_admin_config()
    always_channels = config.get("always_send_to", [])
    channel_names = config.get("channel_names", {})
    
    if not always_channels:
        await msg.answer("📭 Hech qanday umumiy kanal topilmadi!")
        return
    
    text = "📢 <b>Umumiy kanallar:</b>\n\n"
    for channel_id in always_channels:
        name = channel_names.get(str(channel_id), f"Kanal {channel_id}")
        text += f"• {name} (<code>{channel_id}</code>)\n"
    
    await msg.answer(text)

# Kalit so'z o'chirish
@router.message(Command("remove_keyword"))
async def cmd_remove_keyword(msg: Message, bot):
    """Kalit so'z o'chirish: /remove_keyword <model> <so'z>"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    args = msg.text.split(maxsplit=2)
    if len(args) != 3:
        await msg.answer("📝 Foydalanish: /remove_keyword <model> <kalit_soz>\n\n"
                        'Misol: /remove_keyword nexia "ZAZ Nexia"')
        return
    
    model_name = args[1].lower()
    keyword = args[2].strip('"')
    
    # Keywords dan o'chirish
    keywords = await load_model_keywords()
    if model_name not in keywords:
        await msg.answer(f"❌ <b>{model_name.upper()}</b> modeli topilmadi!")
        return
    
    # Kalit so'zni topish va o'chirish
    removed = False
    for i, k in enumerate(keywords[model_name]):
        if k.lower() == keyword.lower():
            keywords[model_name].pop(i)
            removed = True
            break
    
    if removed:
        await save_model_keywords(keywords)
        await msg.answer(f"✅ <b>{model_name.upper()}</b> modelidan kalit so'z o'chirildi!\n"
                        f"🗑️ O'chirilgan: <code>{keyword}</code>")
    else:
        await msg.answer(f"❌ <b>{model_name.upper()}</b> modelida bunday kalit so'z topilmadi!")

# Model o'chirish
@router.message(Command("remove_model"))
async def cmd_remove_model(msg: Message, bot):
    """Model o'chirish: /remove_model <model>"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /remove_model <model_nomi>\n\n"
                        "Misol: /remove_model nexia")
        return
    
    model_name = args[1].lower()
    
    # Config dan o'chirish
    config = await load_admin_config()
    if model_name in config["model_channels"]:
        del config["model_channels"][model_name]
        await save_admin_config(config)
        
        await msg.answer(f"✅ <b>{model_name.upper()}</b> modeli o'chirildi!")
    else:
        await msg.answer(f"❌ <b>{model_name.upper()}</b> modeli topilmadi!")

# Owner ma'lumotlarini ko'rish
@router.message(Command("owner"))
async def cmd_owner_info(msg: Message, bot):
    """Bot owner ma'lumotlarini ko'rish"""
    if not await is_admin(msg.from_user.id, bot):
        return  # Admin bo'lmasa javob bermaydi
    
    try:
        owner_info = await bot.get_chat(BOT_OWNER_ID)
        owner_name = owner_info.full_name or owner_info.username or "Bot egasi"
        owner_username = f"@{owner_info.username}" if owner_info.username else ""
        
        text = f"👑 <b>Bot egasi:</b>\n\n"
        text += f"📝 <b>Ism:</b> {owner_name}\n"
        text += f"🔗 <b>Username:</b> {owner_username}\n"
        text += f"🆔 <b>ID:</b> <code>{BOT_OWNER_ID}</code>\n"
        text += f"🛡️ <b>Huquq:</b> To'liq (Owner)\n"
        text += f"📊 <b>Bot versiya:</b> {BOT_VERSION}\n\n"
        text += f"ℹ️ Owner ma'lumotlari .env fayldan yuklanadi."
        
        await msg.answer(text)
    except Exception as e:
        await msg.answer(f"👑 <b>Bot egasi ID:</b> <code>{BOT_OWNER_ID}</code>\n\n"
                        f"🛡️ Bot egasi har doim to'liq huquqga ega.\n"
                        f"⚠️ Ma'lumot olishda xato: {e}")

# Viloyat qo'shish
@router.message(Command("add_region"))
async def cmd_add_region(msg: Message, bot):
    """Viloyat qo'shish: /add_region <nom> <kanal_id>"""
    if not await is_admin(msg.from_user.id, bot):
        return
    
    args = msg.text.split()
    if len(args) != 3:
        await msg.answer("📝 Foydalanish: /add_region <viloyat_nomi> <kanal_id>\n\n"
                        "Misol: /add_region toshkent -1002123456789")
        return
    
    region_name = args[1].lower()
    try:
        channel_id = int(args[2])
    except ValueError:
        await msg.answer("❌ Kanal ID raqam bo'lishi kerak!")
        return
    
    # Config ni yangilash
    config = await load_admin_config()
    if region_name not in config.get("region_channels", {}):
        config.setdefault("region_channels", {})[region_name] = []
    
    if channel_id not in config["region_channels"][region_name]:
        config["region_channels"][region_name].append(channel_id)
        await save_admin_config(config)
        
        await msg.answer(f"✅ <b>{region_name.upper()}</b> viloyati uchun kanal qo'shildi!\n"
                        f"📢 Kanal: <code>{channel_id}</code>")
    else:
        await msg.answer(f"⚠️ Bu kanal allaqachon <b>{region_name.upper()}</b> viloyatida mavjud!")

# Viloyat kalit so'z qo'shish
@router.message(Command("add_region_keyword"))
async def cmd_add_region_keyword(msg: Message, bot):
    """Viloyat kalit so'z qo'shish: /add_region_keyword <viloyat> <so'z>"""
    if not await is_admin(msg.from_user.id, bot):
        return
    
    args = msg.text.split(maxsplit=2)
    if len(args) != 3:
        await msg.answer("📝 Foydalanish: /add_region_keyword <viloyat> <kalit_soz>\n\n"
                        'Misol: /add_region_keyword toshkent "Toshkent shahar"')
        return
    
    region_name = args[1].lower()
    keyword = args[2].strip('"')
    
    # Keywords ni yangilash
    keywords = await load_region_keywords()
    if region_name not in keywords:
        keywords[region_name] = []
    
    if keyword.lower() not in [k.lower() for k in keywords[region_name]]:
        keywords[region_name].append(keyword)
        await save_region_keywords(keywords)
        
        await msg.answer(f"✅ <b>{region_name.upper()}</b> viloyati uchun kalit so'z qo'shildi!\n"
                        f"🔤 Kalit so'z: <code>{keyword}</code>")
    else:
        await msg.answer(f"⚠️ Bu kalit so'z allaqachon <b>{region_name.upper()}</b> viloyatida mavjud!")

# Viloyatlar ro'yxati
@router.message(Command("list_regions"))
async def cmd_list_regions(msg: Message, bot):
    """Barcha viloyatlar ro'yxati - kanal nomlari bilan"""
    if not await is_admin(msg.from_user.id, bot):
        return
    
    config = await load_admin_config()
    regions = config.get("region_channels", {})
    channel_names = config.get("channel_names", {})
    
    if not regions:
        await msg.answer("📭 Hech qanday viloyat topilmadi!")
        return
    
    text = "🗺️ <b>Barcha viloyatlar:</b>\n\n"
    for region, channels in regions.items():
        text += f"🔹 <b>{region.upper()}</b> ({len(channels)} ta kanal):\n"
        for channel_id in channels:
            # Kanal nomini olishga harakat qilish
            channel_name = channel_names.get(str(channel_id))
            
            if not channel_name:
                try:
                    # Bot orqali kanal ma'lumotlarini olish
                    chat = await bot.get_chat(channel_id)
                    channel_name = chat.title or chat.username or f"Kanal {channel_id}"
                    # Nomni config ga saqlash
                    config["channel_names"][str(channel_id)] = channel_name
                    await save_admin_config(config)
                except:
                    channel_name = f"Kanal {channel_id}"
            
            text += f"   📍 {channel_name}\n"
            text += f"      ID: <code>{channel_id}</code>\n"
        text += "\n"
    
    await msg.answer(text)

# Viloyat kalit so'zlari ro'yxati
@router.message(Command("list_region_keywords"))
async def cmd_list_region_keywords(msg: Message, bot):
    """Barcha viloyat kalit so'zlar ro'yxati"""
    if not await is_admin(msg.from_user.id, bot):
        return
    
    keywords = await load_region_keywords()
    
    if not keywords:
        await msg.answer("📭 Hech qanday viloyat kalit so'z topilmadi!")
        return
    
    text = "🗺️ <b>Barcha viloyat kalit so'zlar:</b>\n\n"
    for region, words in keywords.items():
        text += f"🔹 <b>{region.upper()}</b> ({len(words)} ta):\n"
        for word in words:
            text += f"   • <code>{word}</code>\n"
        text += "\n"
    
    await msg.answer(text)

# Viloyat o'chirish
@router.message(Command("remove_region"))
async def cmd_remove_region(msg: Message, bot):
    """Viloyat o'chirish: /remove_region <viloyat>"""
    if not await is_admin(msg.from_user.id, bot):
        return
    
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /remove_region <viloyat_nomi>\n\n"
                        "Misol: /remove_region toshkent")
        return
    
    region_name = args[1].lower()
    
    # Config dan o'chirish
    config = await load_admin_config()
    if region_name in config.get("region_channels", {}):
        del config["region_channels"][region_name]
        await save_admin_config(config)
        
        await msg.answer(f"✅ <b>{region_name.upper()}</b> viloyati o'chirildi!")
    else:
        await msg.answer(f"❌ <b>{region_name.upper()}</b> viloyati topilmadi!")

# Viloyat kalit so'z o'chirish
@router.message(Command("remove_region_keyword"))
async def cmd_remove_region_keyword(msg: Message, bot):
    """Viloyat kalit so'z o'chirish: /remove_region_keyword <viloyat> <so'z>"""
    if not await is_admin(msg.from_user.id, bot):
        return
    
    args = msg.text.split(maxsplit=2)
    if len(args) != 3:
        await msg.answer("📝 Foydalanish: /remove_region_keyword <viloyat> <kalit_soz>\n\n"
                        'Misol: /remove_region_keyword toshkent "Toshkent shahar"')
        return
    
    region_name = args[1].lower()
    keyword = args[2].strip('"')
    
    # Keywords dan o'chirish
    keywords = await load_region_keywords()
    if region_name not in keywords:
        await msg.answer(f"❌ <b>{region_name.upper()}</b> viloyati topilmadi!")
        return
    
    # Kalit so'zni topish va o'chirish
    removed = False
    for i, k in enumerate(keywords[region_name]):
        if k.lower() == keyword.lower():
            keywords[region_name].pop(i)
            removed = True
            break
    
    if removed:
        await save_region_keywords(keywords)
        await msg.answer(f"✅ <b>{region_name.upper()}</b> viloyatidan kalit so'z o'chirildi!\n"
                        f"🗑️ O'chirilgan: <code>{keyword}</code>")
    else:
        await msg.answer(f"❌ <b>{region_name.upper()}</b> viloyatida bunday kalit so'z topilmadi!")

# Admin foydalanuvchi qo'shish
@router.message(Command("add_admin"))
async def cmd_add_admin(msg: Message, bot):
    """Admin qo'shish: /add_admin <user_id>"""
    if not await is_admin(msg.from_user.id, bot):
        return  # Admin bo'lmasa javob bermaydi
    
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /add_admin &lt;user_id&gt;\n\n"
                        "Misol: /add_admin 123456789\n\n"
                        "💡 User ID ni olish uchun:\n"
                        "• @userinfobot ga yuboring\n"
                        "• Yoki forward qilingan xabardan")
        return
    
    try:
        new_admin_id = int(args[1])
    except ValueError:
        await msg.answer("❌ User ID raqam bo'lishi kerak!")
        return
    
    # Admin users ni yangilash
    admin_users = await load_admin_users()
    if new_admin_id not in admin_users["custom_admins"]:
        admin_users["custom_admins"].append(new_admin_id)
        await save_admin_users(admin_users)
        
        await msg.answer(f"✅ Yangi admin qo'shildi!\n"
                        f"👤 User ID: <code>{new_admin_id}</code>\n\n"
                        "Endi u barcha bot funksiyalaridan foydalanishi mumkin.")
    else:
        await msg.answer("⚠️ Bu foydalanuvchi allaqachon admin!")

# Admin foydalanuvchi o'chirish
@router.message(Command("remove_admin"))
async def cmd_remove_admin(msg: Message, bot):
    """Admin o'chirish: /remove_admin <user_id>"""
    if not await is_admin(msg.from_user.id, bot):
        return  # Admin bo'lmasa javob bermaydi
    
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /remove_admin &lt;user_id&gt;\n\n"
                        "Misol: /remove_admin 123456789")
        return
    
    try:
        remove_admin_id = int(args[1])
    except ValueError:
        await msg.answer("❌ User ID raqam bo'lishi kerak!")
        return
    
    # Admin users dan o'chirish
    admin_users = await load_admin_users()
    if remove_admin_id in admin_users["custom_admins"]:
        admin_users["custom_admins"].remove(remove_admin_id)
        await save_admin_users(admin_users)
        
        await msg.answer(f"✅ Admin o'chirildi!\n"
                        f"👤 User ID: <code>{remove_admin_id}</code>")
    else:
        await msg.answer("❌ Bu foydalanuvchi admin ro'yxatida topilmadi!")

# Admin ro'yxati - yaxshilangan
@router.message(Command("list_admins"))
async def cmd_list_admins(msg: Message, bot):
    """Barcha adminlar ro'yxati - ismlar bilan"""
    if not await is_admin(msg.from_user.id, bot):
        return  # Admin bo'lmasa javob bermaydi
    
    admin_users = await load_admin_users()
    custom_admins = admin_users.get("custom_admins", [])
    channel_admins_enabled = admin_users.get("channel_admins", True)
    
    text = "👥 <b>Admin foydalanuvchilar:</b>\n\n"
    
    # Bot owner
    text += "🔹 <b>Bot egasi:</b>\n"
    try:
        # Owner ma'lumotlarini olish
        owner_info = await bot.get_chat(BOT_OWNER_ID)
        owner_name = owner_info.full_name or owner_info.username or "Bot egasi"
        owner_username = f"@{owner_info.username}" if owner_info.username else ""
        text += f"   👑 <b>{owner_name}</b> {owner_username}\n"
        text += f"      ID: <code>{BOT_OWNER_ID}</code>\n"
    except:
        text += f"   👑 <b>Bot egasi</b>\n"
        text += f"      ID: <code>{BOT_OWNER_ID}</code>\n"
    
    text += "\n"
    
    # Kanal adminlari
    text += "🔹 <b>Kanal adminlari:</b>\n"
    try:
        # Kanal adminlarini olish
        admins = await bot.get_chat_administrators(MAIN_CHANNEL_ID)
        admin_count = 0
        for admin in admins:
            if admin.status in ["administrator", "creator"] and admin.user.id != BOT_OWNER_ID:
                name = admin.user.full_name or admin.user.username or "Noma'lum"
                username = f"@{admin.user.username}" if admin.user.username else ""
                status_emoji = "👑" if admin.status == "creator" else "⚡"
                text += f"   {status_emoji} <b>{name}</b> {username}\n"
                text += f"      ID: <code>{admin.user.id}</code>\n"
                admin_count += 1
        
        if admin_count == 0:
            text += "   ℹ️ Bot owner dan boshqa kanal admin yo'q\n"
            
    except Exception as e:
        text += f"   ❌ Ma'lumot olishda xato: {e}\n"
    
    text += "\n"
    
    # Custom adminlar
    if custom_admins:
        text += f"🔹 <b>Qo'shimcha adminlar:</b> {len(custom_admins)} ta\n"
        for admin_id in custom_admins:
            try:
                # Foydalanuvchi ma'lumotlarini olishga harakat qilish
                user_info = await bot.get_chat(admin_id)
                name = user_info.full_name or user_info.username or "Noma'lum"
                username = f"@{user_info.username}" if user_info.username else ""
                text += f"   👤 <b>{name}</b> {username}\n"
                text += f"      ID: <code>{admin_id}</code>\n"
            except:
                # Agar ma'lumot olishda xato bo'lsa
                text += f"   👤 <b>Foydalanuvchi</b>\n"
                text += f"      ID: <code>{admin_id}</code>\n"
    else:
        text += "🔹 <b>Qo'shimcha adminlar:</b> Yo'q\n"
    
    text += "\n📝 <b>Komandalar:</b>\n"
    text += "• /add_admin &lt;user_id&gt;\n"
    text += "• /remove_admin &lt;user_id&gt;"
    
    await msg.answer(text)

# Kanal adminlarini yoqish/o'chirish
@router.message(Command("toggle_channel_admins"))
async def cmd_toggle_channel_admins(msg: Message, bot):
    """Kanal adminlarini yoqish/o'chirish"""
    if not await is_admin(msg.from_user.id, bot):
        return  # Admin bo'lmasa javob bermaydi
    
    admin_users = await load_admin_users()
    current_status = admin_users.get("channel_admins", True)
    
    # Status ni o'zgartirish
    admin_users["channel_admins"] = not current_status
    await save_admin_users(admin_users)
    
    new_status = "Yoqildi ✅" if not current_status else "O'chirildi ❌"
    await msg.answer(f"🔄 Kanal adminlari: {new_status}\n\n"
                    f"Agar kanal adminlari o'chirilsa, faqat qo'shimcha adminlar botdan foydalanishi mumkin.")

@router.message(Command("remove_always"))
async def cmd_remove_always(msg: Message, bot):
    """Umumiy kanalni o'chirish: /remove_always <kanal_id>"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return
    
    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /remove_always <kanal_id>\n\n"
                        "Misol: /remove_always -1002123456789")
        return
    
    try:
        channel_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Kanal ID raqam bo'lishi kerak!")
        return
    
    # Config dan o'chirish
    config = await load_admin_config()
    if channel_id in config["always_send_to"]:
        config["always_send_to"].remove(channel_id)
        await save_admin_config(config)
        
        await msg.answer(f"✅ Umumiy kanal o'chirildi!\n"
                        f"🗑️ Kanal: <code>{channel_id}</code>")
    else:
        await msg.answer("❌ Bu kanal umumiy kanallar ro'yxatida topilmadi!")

# Admin callback handlers
@router.callback_query(F.data == "admin_models")
async def admin_models_menu(callback: CallbackQuery):
    """Modellar boshqaruvi menusi"""
    config = await load_admin_config()
    models = config.get("model_channels", {})
    
    text = "🤖 <b>Modellar boshqaruvi</b>\n\n"
    for model, channels in models.items():
        text += f"• <b>{model.upper()}</b> → {len(channels)} ta kanal\n"
    
    text += "\n📝 <b>Komandalar:</b>\n"
    text += "• /add_model nexia -1002123456789\n"
    text += "• /remove_model nexia\n"
    text += "• /list_models"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_always")
async def admin_always_menu(callback: CallbackQuery):
    """Umumiy kanallar boshqaruvi"""
    config = await load_admin_config()
    always_channels = config.get("always_send_to", [])
    channel_names = config.get("channel_names", {})
    
    text = "📢 <b>Umumiy kanallar boshqaruvi</b>\n\n"
    for channel_id in always_channels:
        name = channel_names.get(str(channel_id), f"Kanal {channel_id}")
        text += f"• {name}\n"
    
    text += "\n📝 <b>Komandalar:</b>\n"
    text += "• /add_always -1002123456789\n"
    text += "• /remove_always -1002123456789\n"
    text += "• /list_always"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_regions")
async def admin_regions_menu(callback: CallbackQuery):
    """Viloyatlar boshqaruvi menusi"""
    config = await load_admin_config()
    regions = config.get("region_channels", {})
    
    text = "🗺️ <b>Viloyatlar boshqaruvi</b>\n\n"
    for region, channels in regions.items():
        text += f"• <b>{region.upper()}</b> → {len(channels)} ta kanal\n"
    
    text += "\n📝 <b>Komandalar:</b>\n"
    text += "• /add_region toshkent -1002123456789\n"
    text += "• /remove_region toshkent\n"
    text += "• /list_regions\n"
    text += "• /add_region_keyword toshkent \"Toshkent shahar\"\n"
    text += "• /list_region_keywords"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_keywords")
async def admin_keywords_menu(callback: CallbackQuery):
    """Kalit so'zlar boshqaruvi"""
    model_keywords = await load_model_keywords()
    region_keywords = await load_region_keywords()
    
    text = "🔤 <b>Kalit so'zlar boshqaruvi</b>\n\n"
    
    text += "🤖 <b>Model kalit so'zlari:</b>\n"
    for model, words in model_keywords.items():
        text += f"• <b>{model.upper()}</b>: {len(words)} ta\n"
    
    text += "\n🗺️ <b>Viloyat kalit so'zlari:</b>\n"
    for region, words in region_keywords.items():
        text += f"• <b>{region.upper()}</b>: {len(words)} ta\n"
    
    text += '\n📝 <b>Komandalar:</b>\n'
    text += '• /add_keyword nexia "ZAZ Nexia"\n'
    text += '• /add_region_keyword toshkent "Toshkent shahar"\n'
    text += "• /list_keywords\n"
    text += "• /list_region_keywords"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_stats")
async def admin_stats_menu(callback: CallbackQuery):
    """Statistika ko'rish"""
    try:
        # Mapping fayl hajmi
        mapping_size = len(await load_mapping())
        file_size = 0
        try:
            file_size = os.path.getsize(MAPPING_FILE) / 1024  # KB
        except:
            pass
        
        # Modellar statistikasi
        config = await load_admin_config()
        models_count = len(config.get("model_channels", {}))
        regions_count = len(config.get("region_channels", {}))  # Yangi
        always_count = len(config.get("always_send_to", []))
        
        # Keywords statistikasi
        model_keywords = await load_model_keywords()
        region_keywords = await load_region_keywords()  # Yangi
        total_model_keywords = sum(len(words) for words in model_keywords.values())
        total_region_keywords = sum(len(words) for words in region_keywords.values())  # Yangi
        
        text = "📊 <b>Bot statistikasi</b>\n\n"
        text += f"🗂️ <b>Mapping:</b> {mapping_size} ta yozuv\n"
        text += f"💾 <b>Fayl hajmi:</b> {file_size:.1f} KB\n\n"
        text += f"🤖 <b>Modellar:</b> {models_count} ta\n"
        text += f"🗺️ <b>Viloyatlar:</b> {regions_count} ta\n"
        text += f"📢 <b>Umumiy kanallar:</b> {always_count} ta\n\n"
        text += f"🔤 <b>Model kalit so'zlari:</b> {total_model_keywords} ta\n"
        text += f"🗺️ <b>Viloyat kalit so'zlari:</b> {total_region_keywords} ta\n"
        text += f"📊 <b>Bot versiya:</b> {BOT_VERSION}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Statistika olishda xato: {e}")

@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery):
    """Admin foydalanuvchilar boshqaruvi"""
    admin_users = await load_admin_users()
    custom_count = len(admin_users.get("custom_admins", []))
    
    text = "👥 <b>Admin foydalanuvchilar boshqaruvi</b>\n\n"
    text += f"• Qo'shimcha adminlar: {custom_count} ta\n"
    
    text += "\n📝 <b>Komandalar:</b>\n"
    text += "• /add_admin &lt;user_id&gt;\n"
    text += "• /remove_admin &lt;user_id&gt;\n"
    text += "• /list_admins"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Admin panelga qaytish"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Adminlar", callback_data="admin_users")],
        [InlineKeyboardButton(text="🤖 Modellar", callback_data="admin_models")],
        [InlineKeyboardButton(text="🗺️ Viloyatlar", callback_data="admin_regions")],
        [InlineKeyboardButton(text="📢 Umumiy kanallar", callback_data="admin_always")],
        [InlineKeyboardButton(text="🔤 Kalit so'zlar", callback_data="admin_keywords")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(
        "🎛️ <b>Admin Panel</b>\n\n"
        "Botni boshqarish uchun tugmalardan foydalaning:",
        reply_markup=keyboard
    )

# /start komandasi - faqat adminlar uchun
@router.message(CommandStart())
async def start_command(msg: Message, bot):
    # Admin tekshiruvi
    if not await is_admin(msg.from_user.id, bot):
        return  # Javob bermaydi
    
    text = f"""👋 Salom! Men avtomatik repost botman.

📝 Asosiy kanalga e'lon tashlansa, tegishli kanallarga yuboraman.
✉️ Reply xabaringizni ham tarqataman.
✏️ Post/Reply edit qilsangiz, nusxalar ham edit bo'ladi.
🗑 Forward qilsangiz — o'chirish tugmasi chiqaraman.
📅 Mapping 45 kun saqlanadi.

🎛️ Admin panel: /admin
📊 Versiya: {BOT_VERSION}

🛡️ Xavfsizlik: Barcha muhim ma'lumotlar .env faylda saqlangan."""
    
    await msg.answer(text, parse_mode=None)

# /status komandasi - faqat adminlar uchun
@router.message(Command("status"))
async def cmd_status(msg: Message, bot):
    # Admin tekshiruvi
    if not await is_admin(msg.from_user.id, bot):
        return  # Javob bermaydi
    
    config = await get_current_config()
    all_channels = set(config["always_send_to"])
    for ch_list in config["model_channels"].values():
        all_channels.update(ch_list)
    for ch_list in config["region_channels"].values():
        all_channels.update(ch_list)
    all_channels.add(MAIN_CHANNEL_ID)

    report = "📊 <b>Bot holati:</b>\n\n"

    for ch_id in all_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=bot.id)
            status = "✅ <b>Bot admin</b>" if member.status in ["administrator", "creator"] else "⚠️ <b>Bot oddiy a'zo</b>"
        except Exception as e:
            status = f"❌ <b>Xatolik:</b> {str(e)}"

        name = config["channel_names"].get(str(ch_id), f"<code>{ch_id}</code>")
        report += f"📌 {name} → {status}\n"

    await msg.answer(report)

# /del komandasi - yangi
@router.message(Command("del"))
async def cmd_delete_post(msg: Message, bot):
    """/del <post_id> - Asosiy kanaldagi postni nusxalari bilan o'chirish"""
    if not await is_admin(msg.from_user.id, bot):
        await msg.answer("❌ Sizda admin huquqi yo'q!")
        return

    args = msg.text.split()
    if len(args) != 2:
        await msg.answer("📝 Foydalanish: /del <post_id>\n\nMisol: /del 12345")
        return

    try:
        post_id = str(int(args[1]))  # Faqat raqam
    except ValueError:
        await msg.answer("❌ Post ID raqam bo'lishi kerak!")
        return

    mapping = await load_mapping()
    if post_id not in mapping:
        await msg.answer("❌ Bu post mapping'da topilmadi!")
        return

    post_mapping = mapping[post_id]
    deleted_count = 0

    # 1️⃣ Asosiy kanaldagi postni o'chirish
    try:
        await bot.delete_message(MAIN_CHANNEL_ID, int(post_id))
        deleted_count += 1
    except Exception as e:
        logging.error(f"❌ Asosiy postni o'chirishda xato: {e}")

    # 2️⃣ Nusxalarni o'chirish
    if isinstance(post_mapping, dict) and "reply_to" in post_mapping:
        # Reply xabarlar
        targets = post_mapping.get("targets", {})
        for chat_id_str, msg_id in targets.items():
            try:
                await bot.delete_message(int(chat_id_str), msg_id)
                deleted_count += 1
            except Exception as e:
                logging.error(f"❌ Reply nusxasini o'chirishda xato: {e}")
    else:
        # Oddiy postlar
        for chat_id_str, msg_id in post_mapping.items():
            if chat_id_str in ["reply_to", "targets", "_timestamp", "_forwarded", "t"]:
                continue
            try:
                await bot.delete_message(int(chat_id_str), msg_id)
                deleted_count += 1
            except Exception as e:
                logging.error(f"❌ Post nusxasini o'chirishda xato: {e}")

    # 3️⃣ Mapping'dan o'chirish
    fresh_mapping = await load_mapping()
    if post_id in fresh_mapping:
        del fresh_mapping[post_id]
        await save_mapping(fresh_mapping)

    await msg.answer(f"✅ {deleted_count} ta xabar o'chirildi!")

# Environment ma'lumotlari (faqat owner uchun)
@router.message(Command("env_info"))
async def cmd_env_info(msg: Message, bot):
    """Environment ma'lumotlari - faqat owner uchun"""
    if msg.from_user.id != BOT_OWNER_ID:
        return
    
    # Faqat bot owner ko'ra oladi
    env_debug = os.getenv("DEBUG", "false").lower() == "true"
    
    text = f"🔧 <b>Environment Info</b>\n\n"
    text += f"📊 <b>Versiya:</b> {BOT_VERSION}\n"
    text += f"🔍 <b>Debug:</b> {env_debug}\n"
    text += f"📁 <b>Model kanallar:</b> {len(MODEL_CHANNEL_MAP)} ta\n"
    text += f"📢 <b>Umumiy kanallar:</b> {len(ALWAYS_SEND_TO)} ta\n"
    text += f"🏠 <b>Asosiy kanal:</b> <code>{MAIN_CHANNEL_ID}</code>\n"
    text += f"👑 <b>Owner ID:</b> <code>{BOT_OWNER_ID}</code>\n"
    
    if env_debug:
        text += f"\n🔧 <b>DEBUG ma'lumotlari:</b>\n"
        text += f"MODEL_CHANNEL_MAP: {MODEL_CHANNEL_MAP}\n"
        text += f"ALWAYS_SEND_TO: {ALWAYS_SEND_TO}"
    
    await msg.answer(text)
