import os
from dotenv import load_dotenv

# .env fayldan muhim ma'lumotlarni yuklash
load_dotenv()

# Bot token (majburiy)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN .env faylda topilmadi!")

# Bot owner ID (majburiy)
try:
    BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))
except ValueError:
    raise ValueError("❌ BOT_OWNER_ID noto'g'ri format!")

if BOT_OWNER_ID == 0:
    raise ValueError("❌ BOT_OWNER_ID .env faylda topilmadi!")

# Asosiy kanal ID (majburiy)
try:
    MAIN_CHANNEL_ID = int(os.getenv("MAIN_CHANNEL_ID", "0"))
except ValueError:
    raise ValueError("❌ MAIN_CHANNEL_ID noto'g'ri format!")

if MAIN_CHANNEL_ID == 0:
    raise ValueError("❌ MAIN_CHANNEL_ID .env faylda topilmadi!")

# Xavfsiz kanal ID olish funksiyasi
def get_channel_id(env_name, default=0):
    try:
        return int(os.getenv(env_name, default))
    except ValueError:
        print(f"⚠️ {env_name} noto'g'ri format, 0 qo'yildi")
        return 0

# Model kanallari
MODEL_CHANNEL_MAP = {
    "damas": [get_channel_id("DAMAS_CHANNEL")],
    "jentra": [get_channel_id("JENTRA_CHANNEL")],
    "malibu": [get_channel_id("MALIBU_CHANNEL")],
    "spark": [get_channel_id("SPARK_CHANNEL")],
    "nexia": [get_channel_id("NEXIA_CHANNEL")],
}

# Umumiy kanallar
ALWAYS_SEND_TO = [
    get_channel_id("GENERAL_CHANNEL_1"),
    get_channel_id("GENERAL_CHANNEL_2"),
]

# 0 qiymatlarni olib tashlash
ALWAYS_SEND_TO = [ch for ch in ALWAYS_SEND_TO if ch != 0]
for model in MODEL_CHANNEL_MAP:
    MODEL_CHANNEL_MAP[model] = [ch for ch in MODEL_CHANNEL_MAP[model] if ch != 0]

# Kanal nomlari
CHANNEL_NAMES = {
    MAIN_CHANNEL_ID: "Asosiy kanal",
    get_channel_id("DAMAS_CHANNEL"): "Damas kanal",
    get_channel_id("JENTRA_CHANNEL"): "Jentra kanal",
    get_channel_id("MALIBU_CHANNEL"): "Malibu kanal",
    get_channel_id("SPARK_CHANNEL"): "Spark kanal",
    get_channel_id("NEXIA_CHANNEL"): "Nexia kanal",
    get_channel_id("GENERAL_CHANNEL_1"): "Umumiy kanal 1",
    get_channel_id("GENERAL_CHANNEL_2"): "Umumiy kanal 2",
}

# Debug va versiya
BOT_VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

if DEBUG:
    print("🔧 DEBUG rejimi yoqildi")
    print(f"📊 MODEL_CHANNEL_MAP: {MODEL_CHANNEL_MAP}")
    print(f"📊 ALWAYS_SEND_TO: {ALWAYS_SEND_TO}")

print(f"🤖 Bot versiya: {BOT_VERSION}")
print(f"✅ Config yuklandi: {len(ALWAYS_SEND_TO)} umumiy, {sum(len(v) for v in MODEL_CHANNEL_MAP.values())} model kanal")
