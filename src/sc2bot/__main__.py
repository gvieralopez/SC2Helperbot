import asyncio
import logging
import os
from datetime import time
from html import escape

from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    Update,
)
from telegram.constants import ChatMemberStatus, ChatType, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    filters,
)
from tzlocal import get_localzone

from sc2bot.bot_response import BotResponse, split_text
from sc2bot.commands import command_names
from sc2bot.controller import fetch_all_users, ping_texts, profile_button, registered_users
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


def main() -> None:
    # httpx logs every request, a line per poll.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    application = (
        Application.builder()
        .token(os.environ["BOT_TOKEN"])
        # Jobs run in the server's time zone, not in UTC.
        .defaults(Defaults(parse_mode=ParseMode.HTML, tzinfo=get_localzone()))
        .build()
    )
    application.add_handler(MessageHandler(filters.COMMAND, _on_command))
    application.add_handler(CallbackQueryHandler(_on_button, pattern="^profile:"))
    _schedule_daily_fetch(application)
    # Telegram remembers the update types a bot last asked for: ask for all of them, or the
    # button taps (callback queries) of a bot that once asked only for messages never arrive.
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


async def _on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await handle_command(update.message, context.bot)


async def handle_command(message: Message, bot: Bot) -> None:
    parts = extract_command(message.text or "", bot.username)
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

    await answer(bot, message.chat.id, response)


async def ping(message: Message, bot: Bot) -> None:
    """Mention the registered users who are in this group, except whoever asked."""
    caller = message.from_user.id if message.from_user else None
    users = [user for user in registered_users() if user.telegram_id != caller]
    in_group = await asyncio.gather(*(_is_member(bot, message.chat.id, user) for user in users))
    members = [user for user, member in zip(users, in_group, strict=True) if member]
    for text in ping_texts(members):
        await bot.send_message(message.chat.id, text)


async def _is_member(bot: Bot, chat_id: int, user: User) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user.telegram_id)
    except TelegramError:
        return False  # never seen in this chat
    if member.status == ChatMemberStatus.RESTRICTED:
        return bool(getattr(member, "is_member", False))
    return member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED)


async def answer(bot: Bot, chat_id: int | str, response: BotResponse) -> None:
    """Send the response; its buttons go under the photo, or else under the last message."""
    text, markup = response.text, _keyboard(response)
    if response.image:
        if len(split_text(text, CAPTION_LIMIT)) == 1:
            await bot.send_photo(
                chat_id, response.image, caption=text, filename="mmr.png", reply_markup=markup
            )
            return
        await bot.send_photo(chat_id, response.image, filename="mmr.png", reply_markup=markup)
        markup = None
    parts = split_text(text, MESSAGE_LIMIT)
    for i, part in enumerate(parts):
        await bot.send_message(chat_id, part, reply_markup=markup if i == len(parts) - 1 else None)


async def _on_button(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the profile view a button asks for in place of the message's photo."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()
    response = profile_button(query.data)
    if response is None or response.image is None:
        return
    media = InputMediaPhoto(response.image, caption=response.text, filename="mmr.png")
    try:
        await query.edit_message_media(media, reply_markup=_keyboard(response))
    except BadRequest as error:
        if "not modified" not in error.message:  # the button of what is already shown
            raise


def _keyboard(response: BotResponse) -> InlineKeyboardMarkup | None:
    if not response.buttons:
        return None
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    button.label,
                    callback_data=button.data,
                    style="primary" if button.selected else None,  # blue
                )
                for button in row
            ]
            for row in response.buttons
        ]
    )


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
    except TelegramError:
        logger.exception("Couldn't post the daily ranking")


def _schedule_daily_fetch(application: Application) -> None:
    if application.job_queue is None:
        raise RuntimeError('The daily fetch needs "python-telegram-bot[job-queue]".')
    hour, minute = DAILY_FETCH_TIME.split(":")
    application.job_queue.run_daily(_daily_job, time(int(hour), int(minute)))


async def _daily_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await daily_fetch(context.bot)


if __name__ == "__main__":
    main()
