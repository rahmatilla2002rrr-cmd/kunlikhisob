import os
import asyncio
from datetime import datetime, timedelta
import pytz

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from apscheduler.schedulers.asyncio import AsyncIOScheduler


# ================= TIMEZONE =================
TZ = pytz.timezone("Asia/Tashkent")

def now():
    return datetime.now(TZ)


# ================= BOT =================
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ================= SCHEDULER =================
scheduler = AsyncIOScheduler(timezone=TZ)


# ================= COMMANDS =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Bot ishlayapti. Vaqt testi tayyor.")


@dp.message(Command("time"))
async def time_cmd(message: Message):
    await message.answer(
        f"🕒 Bot vaqti: {now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


@dp.message(Command("testauto"))
async def test_auto(message: Message):
    run_time = now() + timedelta(seconds=10)

    scheduler.add_job(
        send_auto_message,
        trigger="date",
        run_date=run_time,
        args=[message.from_user.id]
    )

    await message.answer("⏳ 10 soniyadan keyin avtomatik xabar keladi.")


# ================= AUTO MESSAGE =================
async def send_auto_message(chat_id: int):
    await bot.send_message(
        chat_id,
        "⏰ Avtomatik xabar keldi. Scheduler ISHLAYDI ✅"
    )


# ================= MAIN =================
async def main():
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
