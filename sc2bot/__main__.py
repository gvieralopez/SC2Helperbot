import logging
import os

from aiogram import Bot, Dispatcher, executor, types

from sc2bot.bot_response import BotResponse
from sc2bot.routes import routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=os.environ.get("BOT_TOKEN"))
dp = Dispatcher(bot)


@dp.message_handler(state="*")
async def router(message: types.Message):
    if not message.is_command():
        return

    command_name, *arguments = extract_command(message.text)

    if command_name not in routes:
        return

    try:
        telegram_id = int(message["from"]["id"])
        telegram_username = message["from"]["username"]
        response = routes[command_name].target(
            *arguments, telegram_id=telegram_id, telegram_username=telegram_username
        )
    except Exception as e:
        logger.warning(f"There was an error executing the command: {e}")
        response = routes[command_name].help

    await answer(message, response)


async def answer(message: types.Message, response: BotResponse):
    if response.image:
        await message.answer_photo(response.image, response.text, parse_mode="html")
        return

    await message.answer(response.text, parse_mode="html")


def extract_command(text: str) -> list[str]:
    raw_without_slash = text[1:]
    return raw_without_slash.split(" ")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
