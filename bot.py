import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import Command
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL")

if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in the environment")
if not WEB_APP_URL:
    raise RuntimeError("WEB_APP_URL is not set in the environment")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Web Appni ochish",
                    web_app=WebAppInfo(url=WEB_APP_URL),
                )
            ]
        ]
    )
    await message.answer(
        "POS tizimga kirish uchun quyidagi tugmachani bosing:",
        reply_markup=keyboard,
    )


async def main() -> None:
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

