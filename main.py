import os
import asyncio
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from apscheduler.schedulers.asyncio import AsyncIOScheduler


# ================== TIMEZONE ==================
TZ = pytz.timezone("Asia/Tashkent")


def now():
    return datetime.now(TZ)


# ================== BOT ==================
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ================== SCHEDULER ==================
scheduler = AsyncIOScheduler(
    timezone=TZ,
    job_defaults={
        "misfire_grace_time": 300,
        "coalesce": True,
        "max_instances": 1
    }
)


# ================== BOT COMMANDS ==================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Kunlikhisob bot ishlayapti.")


@dp.message(Command("time"))
async def time_check(message: Message):
    t = now().strftime("%Y-%m-%d %H:%M:%S")
    await message.answer(f"🕒 Bot vaqti: {t}")


# ================== HISOBOT ESLATMALARI ==================
async def remind_1930():
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="⏰ Eslatma: 20:00 da hisobot topshirishingiz kerak"
    )


# ================== TEST COMMAND (CRON O‘RNIGA) ==================
@dp.message(Command("test1930"))
async def test_1930(message: Message):
    await remind_1930()
    await message.answer("✅ 19:30 logikasi qo‘lda test qilindi")


# ================== SCHEDULER SETUP ==================
def setup_scheduler():
    print("SCHEDULER STARTED")

    # REAL ISH VAQTI (dushanba–shanba)
    scheduler.add_job(
        remind_1930,
        trigger="cron",
        day_of_week="mon-sat",
        hour=19,
        minute=30,
        id="remind_1930",
        replace_existing=True
    )

    scheduler.start()


# ================== MAIN ==================
async def main():
    setup_scheduler()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
