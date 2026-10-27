import asyncio
import logging
import os
from html import escape

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType, ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sc2bot.bot_response import BotResponse, split_text
from sc2bot.commands import command_names
from sc2bot.controller import fetch_all_users, ping_texts, registered_users
from sc2bot.database.schema import User
from sc2bot.parsing import extract_command
from sc2bot.routes import routes

logger = logging.getLogger(__name__)

# Where the daily ranking is posted and pinned (unset: fetch only).
LOG_CHANNEL_ID = os.environ.get("LOG_CHANNEL_ID")
DAILY_FETCH_TIME = os.environ.get("DAILY_FETCH_TIME", "17:30")
# Telegram's limits for a message and for a photo caption.
MESSAGE_LIMIT = 4096
CAPTION_LIMIT = 1024

router = Router()


def main() -> None:
    asyncio.run(_run())


@router.message(F.text.startswith("/"))
async def handle_command(message: Message, bot: Bot) -> None:
    me = await bot.me()
    parts = extract_command(message.text or "", me.username)
    if not parts or parts[0] not in routes or message.from_user is None:
        return
    command_name, *arguments = parts
    if command_name == command_names["ping"] and message.chat.type != ChatType.PRIVATE:
        await ping(message, bot)
        return

    sender = message.from_user
    # Without a username, a link to the user, like the old bot stored (shown as is by mention).
    username = (
        sender.username or f'<a href="tg://user?id={sender.id}">{escape(sender.full_name)}</a>'
    )
    try:
        response = routes[command_name].target(
            *arguments, telegram_id=sender.id, telegram_username=username
        )
    except Exception:
        logger.exception("There was an error executing the command")
        response = routes[command_name].error

    await answer(message, response)


async def ping(message: Message, bot: Bot) -> None:
    """Mention the registered users who are in this group, except whoever asked."""
    caller = message.from_user.id if message.from_user else None
    users = [user for user in registered_users() if user.telegram_id != caller]
    in_group = await asyncio.gather(*(_is_member(bot, message.chat.id, user) for user in users))
    members = [user for user, member in zip(users, in_group, strict=True) if member]
    for text in ping_texts(members):
        await message.answer(text)


async def _is_member(bot: Bot, chat_id: int, user: User) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user.telegram_id)
    except TelegramAPIError:
        return False  # never seen in this chat
    if member.status == ChatMemberStatus.RESTRICTED:
        return bool(getattr(member, "is_member", False))
    return member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)


async def answer(message: Message, response: BotResponse) -> None:
    text = response.text
    if response.image:
        photo = BufferedInputFile(response.image, filename="mmr.png")
        if len(split_text(text, CAPTION_LIMIT)) == 1:
            await message.answer_photo(photo, caption=text)
            return
        await message.answer_photo(photo)
    for part in split_text(text, MESSAGE_LIMIT):
        await message.answer(part)


async def daily_fetch(bot: Bot) -> None:
    # On the loop's own thread: the database session can't be shared with a worker thread.
    response = fetch_all_users()
    if not LOG_CHANNEL_ID:
        return
    try:
        parts = split_text(response.text, MESSAGE_LIMIT)
        first = await bot.send_message(LOG_CHANNEL_ID, parts[0])
        for part in parts[1:]:
            await bot.send_message(LOG_CHANNEL_ID, part)
        await bot.pin_chat_message(LOG_CHANNEL_ID, first.message_id)
    except TelegramAPIError:
        logger.exception("Couldn't post the daily ranking")


async def _run() -> None:
    bot = Bot(os.environ["BOT_TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    _schedule_daily_fetch(bot)
    await dispatcher.start_polling(bot, drop_pending_updates=True)


def _schedule_daily_fetch(bot: Bot) -> None:
    hour, minute = DAILY_FETCH_TIME.split(":")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_fetch, "cron", hour=int(hour), minute=int(minute), args=[bot])
    scheduler.start()


if __name__ == "__main__":
    main()
