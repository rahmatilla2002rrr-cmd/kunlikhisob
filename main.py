import os
import asyncio
from datetime import datetime, timedelta
import pytz

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from apscheduler.schedulers.asyncio import AsyncIOScheduler
TEST_MODE = True  # hozir test uchun

# ================= TIMEZONE =================
TZ = pytz.timezone("Asia/Tashkent")

def now():
    return datetime.now(TZ)


# ================= BOT =================
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ================= SCHEDULER =================
scheduler = AsyncIOScheduler(
    timezone=TZ,
    job_defaults={"misfire_grace_time": 300, "coalesce": True, "max_instances": 1}
)


# ================= STATE =================
user_step = {}   # user_id -> step
report_data = {} # user_id -> dict
submitted_users = set()
late_users = set()

# ================= HELPERS =================
def report_text(d):
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


# ================= COMMANDS =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Kunlikhisob bot ishlayapti.")


@dp.message(Command("time"))
async def time_cmd(message: Message):
    await message.answer(f"🕒 Bot vaqti: {now().strftime('%Y-%m-%d %H:%M:%S')}")


# ================= AUTOMATIC MESSAGES =================
async def remind_1930_all():
    # 19:30 eslatma
    # (real ishda bu yerda operatorlar ro‘yxati bo‘lishi mumkin)
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="⏰ 19:30: Bugun 20:00 da hisobot topshiriladi."
    )

async def choose_2000_all():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Hisobot topshirish", callback_data="report_start")
    kb.button(text="⏳ Yana ishlayman", callback_data="work_more")
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="🕗 20:00: Hisobot vaqti keldi",
        reply_markup=kb.as_markup()
    )

async def remind_2100_all():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Hisobot topshirish", callback_data="report_start")
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="⏰ 21:00: Oxirgi imkoniyat — hisobot topshiring",
        reply_markup=kb.as_markup()
    )


# ================= REPORT FLOW =================
@dp.callback_query(F.data == "report_start")
async def report_start(call: CallbackQuery):
    uid = call.from_user.id
    report_data[uid] = {"username": call.from_user.username}
    user_step[uid] = "jami"
    await call.message.answer("📥 Jami leadlar sonini kiriting:")
    await call.answer()

@dp.callback_query(F.data == "work_more")
async def work_more(call: CallbackQuery):
    await call.answer("Davom etyapsiz")
    await call.message.answer("⏳ Qabul qilindi. 21:00 da oxirgi hisobot so‘raladi.")

@dp.message()
async def report_steps(message: Message):
    uid = message.from_user.id
    if uid not in user_step:
        return

    try:
        val = int(message.text)
    except:
        await message.answer("❗ Faqat raqam kiriting")
        return

    step = user_step[uid]
    d = report_data[uid]
    d[step] = val

    order = [
        ("jami", "📞 Gaplashilgan sonini kiriting:"),
        ("gaplashilgan", "✅ Sifatli sonini kiriting:"),
        ("sifatli", "❌ Sifatsiz sonini kiriting:"),
        ("sifatsiz", "🎓 Sinov darsi sonini kiriting:"),
        ("sinov", "🤔 O‘ylab ko‘radi sonini kiriting:"),
        ("oylab", "📵 Ko‘tarmagan sonini kiriting:"),
        ("kotarmagan", None),
    ]

    for i, (k, next_q) in enumerate(order):
        if step == k:
            if next_q:
                user_step[uid] = order[i+1][0]
                await message.answer(next_q)
            else:
                user_step.pop(uid)
                submitted_users.add(uid)
                await bot.send_message(CHANNEL_ID, report_text(d))
                await message.answer("✅ Hisobot kanalga yuborildi")
            return


# ================= SCHEDULER SETUP =================
def setup_scheduler():
    # Dushanba–Shanba
    scheduler.add_job(
        remind_1930_all, "cron", day_of_week="mon-sat", hour=19, minute=30,
        id="remind_1930", replace_existing=True
    )
    scheduler.add_job(
        choose_2000_all, "cron", day_of_week="mon-sat", hour=20, minute=0,
        id="choose_2000", replace_existing=True
    )
    scheduler.add_job(
        remind_2100_all, "cron", day_of_week="mon-sat", hour=21, minute=0,
        id="remind_2100", replace_existing=True
    )
    scheduler.start()


# ================= MAIN =================
async def main():
    setup_scheduler()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
