import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("✅ /start ishladi")


@dp.message(Command("ping"))
async def ping_handler(message: Message):
    await message.answer("🏓 pong")


@dp.message()
async def echo_handler(message: Message):
    await message.answer("🟢 oddiy text keldi")


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
