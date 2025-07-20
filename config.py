import os
from dotenv import load_dotenv

# .env fayldan token yuklash (xavfsizlik uchun)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # .env faylga ko'chirish kerak
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda topilmadi!")

# Asosiy kanal
MAIN_CHANNEL_ID = -1002824123374

# Mashina modeliga qarab yuboriladigan kanallar
MODEL_CHANNEL_MAP = {
    "damas": [-1002551596312],
    "jentra": [-1002699354070],
    "malibu": [-1002627955129],
    "spark": [-1002755117114],
    "nexia": [-1002687717744],  # Admin config dan qo'shilgan
}

# Har doim yuboriladigan kanallar (masalan: umumiy kanal)
ALWAYS_SEND_TO = [
    -1002818922505,  # Umumiy kanal
    -1002811503820,  # Ikkinchi umumiy kanal
]

# Kanal nomlari – bu `/status` komandasi uchun
CHANNEL_NAMES = {
    -1002824123374: "Asosiy kanal",
    -1002551596312: "Damas kanal",
    -1002699354070: "Jentra kanal", 
    -1002627955129: "Malibu kanal",
    -1002755117114: "Spark kanal",
    -1002687717744: "Nexia kanal",
    -1002818922505: "Umumiy kanal 1",
    -1002811503820: "Umumiy kanal 2",
}