import os
import asyncio
from datetime import datetime, timedelta
import pytz

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from apscheduler.schedulers.asyncio import AsyncIOScheduler


# ================== TIMEZONE ==================
TZ = pytz.timezone("Asia/Tashkent")

def now():
    return datetime.now(TZ)


# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))      # -100xxxxxxxxxx
OPERATOR_ID = int(os.getenv("OPERATOR_ID"))    # test uchun o‘zingizning ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================== SCHEDULER ==================
scheduler = AsyncIOScheduler(timezone=TZ)


# ================== STATE ==================
user_step = {}
report_data = {}


# ================== HELPERS ==================
def build_report(d: dict) -> str:
    return (
        f"👤 @{d.get('username','')}\n\n"
        "🔹 1-BLOK (UMUMIY)\n"
        f"📥 Jami leadlar: {d['jami']}\n"
        f"📞 Gaplashilgan: {d['gaplashilgan']}\n"
        f"✅ Sifatli: {d['sifatli']}\n"
        f"❌ Sifatsiz: {d['sifatsiz']}\n"
        f"🎓 Sinov darsi: {d['sinov']}\n"
        f"🤔 O‘ylab ko‘radi: {d['oylab']}\n"
        f"📵 Ko‘tarmagan: {d['kotarmagan']}\n"
    )


# ================== COMMANDS ==================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Kunlikhisob bot ishlayapti.")


@dp.message(Command("time"))
async def time_cmd(message: Message):
    await message.answer(f"🕒 Bot vaqti: {now().strftime('%Y-%m-%d %H:%M:%S')}")


# ================== REPORT FLOW ==================
async def start_report(user_id: int):
    report_data[user_id] = {
        "username": None
    }
    user_step[user_id] = "jami"

    await bot.send_message(
        user_id,
        "📥 Jami leadlar sonini kiriting:"
    )


@dp.message()
async def handle_report(message: Message):
    uid = message.from_user.id

    if uid not in user_step:
        return

    try:
        value = int(message.text)
    except:
        await message.answer("❗ Faqat raqam kiriting")
        return

    step = user_step[uid]
    d = report_data[uid]
    d["username"] = message.from_user.username

    order = [
        ("jami", "📞 Gaplashilgan sonini kiriting:"),
        ("gaplashilgan", "✅ Sifatli sonini kiriting:"),
        ("sifatli", "❌ Sifatsiz sonini kiriting:"),
        ("sifatsiz", "🎓 Sinov darsi sonini kiriting:"),
        ("sinov", "🤔 O‘ylab ko‘radi sonini kiriting:"),
        ("oylab", "📵 Ko‘tarmagan sonini kiriting:"),
        ("kotarmagan", None),
    ]

    d[step] = value

    for i, (key, question) in enumerate(order):
        if step == key:
            if question:
                user_step[uid] = order[i + 1][0]
                await message.answer(question)
            else:
                user_step.pop(uid)
                await bot.send_message(
                    CHANNEL_ID,
                    build_report(d)
                )
                await message.answer("✅ Hisobot qabul qilindi va kanalga yuborildi")
            return


# ================== AUTOMATIC TIME ==================
def setup_scheduler():
    # TEST MODE: 10 soniyadan keyin avtomatik boshlaydi
    scheduler.add_job(
        start_report,
        "date",
        run_date=now() + timedelta(seconds=10),
        args=[OPERATOR_ID]
    )

    scheduler.start()


# ================== MAIN ==================
async def main():
    setup_scheduler()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
