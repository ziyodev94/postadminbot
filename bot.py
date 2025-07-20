import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers import router, start_auto_delete_checker

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    # Auto-delete checker ni boshlash
    await start_auto_delete_checker(bot)
    
    print("🚀 Bot ishga tushdi!")
    print("✅ Post repost qilish funksiyasi yoqildi")
    print("✅ Reply tarqatish funksiyasi yoqildi") 
    print("✅ Post edit funksiyasi yoqildi (rasm, video, matn)")
    print("✅ Reply edit funksiyasi yoqildi")
    print("✅ Forward → Delete funksiyasi yoqildi")
    print("✅ Admin panel yoqildi (/admin)")
    print("✅ Model + Viloyat detection tizimi")
    print("✅ 45 kunlik mapping + kunlik tozalash")
    print("🗑 Postni o'chirish: asosiy kanaldan botga forward qiling")
    print("✏️ Postni edit qilish: asosiy kanalda edit qiling")
    print("🎛️ Admin panel: /admin")
    print("📝 Komandalar:")
    print("  /status - Bot holati")
    print("  /admin - Admin panel")
    print("  /add_model <nom> <kanal_id>")
    print("  /add_region <viloyat> <kanal_id>")
    print("  /add_keyword <model> <kalit_soz>")
    print("  /add_region_keyword <viloyat> <kalit_soz>")
    print("  /list_models, /list_regions, /list_keywords")
    print("💾 Mapping fayl hajmi avtomatik kichik ushlab turiladi")
    print("🎯 Model + Viloyat ikki turdagi detection tizimi")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())