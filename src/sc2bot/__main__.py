import asyncio
import io
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sc2bot.bot_response import BotResponse
from sc2bot.controller import fetch_all_users
from sc2bot.parsing import extract_command
from sc2bot.routes import routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=os.environ.get("BOT_TOKEN"))
dp = Dispatcher(bot)

# Where the daily ranking is posted and pinned (unset: fetch only).
LOG_CHANNEL_ID = os.environ.get("LOG_CHANNEL_ID")
DAILY_FETCH_TIME = os.environ.get("DAILY_FETCH_TIME", "17:30")


@dp.message_handler(state="*")
async def router(message: types.Message):
    if not message.is_command():
        return

    me = await bot.me
    parts = extract_command(message.text, me.username)
    if not parts or parts[0] not in routes:
        return
    command_name, *arguments = parts

    try:
        telegram_id = int(message["from"]["id"])
        telegram_username = message["from"]["username"]
        response = routes[command_name].target(
            *arguments, telegram_id=telegram_id, telegram_username=telegram_username
        )
    except Exception as e:
        logger.warning(f"There was an error executing the command: {e}")
        response = routes[command_name].error

    await answer(message, response)


async def answer(message: types.Message, response: BotResponse):
    if response.image:
        photo = types.InputFile(io.BytesIO(response.image), filename="mmr.png")
        await message.answer_photo(photo, response.text, parse_mode="html")
        return

    await message.answer(response.text, parse_mode="html")


async def daily_fetch():
    response = await asyncio.to_thread(fetch_all_users)
    if not LOG_CHANNEL_ID:
        return
    try:
        message = await bot.send_message(LOG_CHANNEL_ID, response.text, parse_mode="html")
        await bot.pin_chat_message(LOG_CHANNEL_ID, message.message_id)
    except TelegramAPIError as e:
        logger.warning(f"Couldn't post the daily ranking: {e}")


def schedule_daily_fetch(_dispatcher: Dispatcher):
    hour, minute = DAILY_FETCH_TIME.split(":")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_fetch, "cron", hour=int(hour), minute=int(minute))
    scheduler.start()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=schedule_daily_fetch)
