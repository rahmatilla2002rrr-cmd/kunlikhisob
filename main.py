import os
import asyncio
from datetime import datetime, time
import pytz

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from apscheduler.schedulers.asyncio import AsyncIOScheduler


# ================== SOZLAMALAR ==================
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

TZ = pytz.timezone("Asia/Tashkent")

bot = Bot(token=TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler(timezone=TZ)

# user holatlari
users_state = {}      # ishlayaptimi, qaysi bosqich
reports = {}          # hisobot ma'lumotlari


# ================== YORDAMCHI ==================
def now():
    return datetime.now(TZ)

def is_sunday():
    return now().weekday() == 6  # 6 = yakshanba


def report_template(data):
    return f"""
👤 @{data['username']}

🔹 1-BLOK (UMUMIY)
📥 Jami leadlar: {data['jami']}
📞 Gaplashilgan: {data['gaplashilgan']}
✅ Sifatli: {data['sifatli']}
❌ Sifatsiz: {data['sifatsiz']}
🎓 Sinov darsi: {data['sinov']}
🤔 O‘ylab ko‘radi: {data['oylab']}
📵 Ko‘tarmagan: {data['kotarmagan']}
"""


# ================== START ==================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ Kunlik hisob bot ishlayapti. Habarlar faqat belgilangan vaqtda yuboriladi.")


# ================== YAKSHANBA SO‘ROV ==================
async def sunday_check():
    if not is_sunday():
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha", callback_data="work_yes")
    kb.button(text="❌ Yo‘q", callback_data="work_no")

    for uid in users_state.keys():
        await bot.send_message(
            uid,
            "❓ Bugun ishdamisiz?",
            reply_markup=kb.as_markup()
        )


@dp.callback_query(F.data == "work_no")
async def not_working(call: CallbackQuery):
    await bot.send_message(
        CHANNEL_ID,
        f"📅 Yakshanba\n❌ Bugun ish kuni emas\n👤 @{call.from_user.username}"
    )
    users_state[call.from_user.id] = {"working": False}
    await call.answer("Bugun yopildi")


@dp.callback_query(F.data == "work_yes")
async def working(call: CallbackQuery):
    users_state[call.from_user.id] = {"working": True}
    await call.answer("Ish kuni belgilandi")


# ================== 19:30 ESLATMA ==================
async def remind_1930():
    for uid, st in users_state.items():
        if st.get("working", True):
            await bot.send_message(
                uid,
                "⏰ Eslatma: 20:00 da hisobot topshirishingiz kerak"
            )


# ================== 20:00 TANLOV ==================
async def choose_2000():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Hisobot topshirish", callback_data="report_20")
    kb.button(text="⏳ Yana ishlayman", callback_data="work_more")

    for uid, st in users_state.items():
        if st.get("working", True):
            await bot.send_message(
                uid,
                "🕗 Hisobot vaqti keldi",
                reply_markup=kb.as_markup()
            )


@dp.callback_query(F.data == "work_more")
async def work_more(call: CallbackQuery):
    await call.answer("Davom etyapsiz")
    await bot.send_message(
        call.from_user.id,
        "⏰ Eslatma: 21:00 da hisobot topshirishingiz kerak"
    )


# ================== HISOBOT KIRITISH ==================
@dp.callback_query(F.data == "report_20")
async def start_report(call: CallbackQuery):
    uid = call.from_user.id
    reports[uid] = {"username": call.from_user.username}
    users_state[uid]["step"] = "jami"
    await bot.send_message(uid, "📥 Jami leadlar sonini kiriting:")
    await call.answer()


@dp.message()
async def report_steps(message: Message):
    uid = message.from_user.id
    if uid not in users_state or "step" not in users_state[uid]:
        return

    step = users_state[uid]["step"]

    try:
        val = int(message.text)
    except:
        await message.answer("❗ Faqat raqam kiriting")
        return

    data = reports[uid]

    order = [
        ("jami", "📞 Gaplashilgan sonini kiriting:"),
        ("gaplashilgan", "✅ Sifatli sonini kiriting:"),
        ("sifatli", "❌ Sifatsiz sonini kiriting:"),
        ("sifatsiz", "🎓 Sinov darsi sonini kiriting:"),
        ("sinov", "🤔 O‘ylab ko‘radi sonini kiriting:"),
        ("oylab", "📵 Ko‘tarmagan sonini kiriting:"),
    ]

    data[step] = val

    for i, (k, txt) in enumerate(order):
        if step == k:
            if i + 1 < len(order):
                users_state[uid]["step"] = order[i + 1][0]
                await message.answer(txt)
                return
            else:
                users_state[uid].pop("step")
                await bot.send_message(
                    CHANNEL_ID,
                    report_template(data)
                )
                await message.answer("✅ Hisobot qabul qilindi")
                return


# ================== SCHEDULER ==================
def setup_scheduler():
    scheduler.add_job(
    remind_1930,
    "cron",
    day_of_week="*",
    hour=11,
    minute=40
)
    scheduler.start()


# ================== MAIN ==================
async def main():
    setup_scheduler()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
