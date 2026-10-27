from datetime import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, Update
from telegram import User as TelegramUser
from telegram.error import BadRequest, TelegramError
from telegram.ext import Application, CallbackQueryHandler, MessageHandler
from tzlocal import get_localzone

from sc2bot import __main__ as bot_main
from sc2bot.bot_response import BotResponse, Button
from sc2bot.database.schema import User
from sc2bot.routes import routes
from tests.fakes import CHAT_ID, fake_bot, fake_message, sent_texts


async def test_command_is_answered(user: User) -> None:
    bot = fake_bot()
    await bot_main.handle_command(fake_message("/user"), bot)
    [text] = sent_texts(bot)
    assert user.battle_tag in text
    assert bot.send_message.await_args.args[0] == CHAT_ID


@pytest.mark.parametrize("text", ["/nope", "/rank@OtherBot", "/"])
async def test_unknown_or_foreign_commands_are_ignored(db: None, text: str) -> None:
    bot = fake_bot()
    await bot_main.handle_command(fake_message(text), bot)
    bot.send_message.assert_not_awaited()


async def test_sender_without_username_is_stored_as_a_link(db: None) -> None:
    bot = fake_bot()
    message = fake_message("/register Foo#1234", sender=5, username=None)
    message.from_user.full_name = "<Foo>"
    await bot_main.handle_command(message, bot)
    assert '<a href="tg://user?id=5">&lt;Foo&gt;</a>' in sent_texts(bot)[0]


async def test_failing_command_answers_its_usage(db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: str, **_kwargs: object) -> BotResponse:
        raise ValueError

    monkeypatch.setattr(routes["user"], "target", fail)
    bot = fake_bot()
    await bot_main.handle_command(fake_message("/user"), bot)
    assert "/help_user" in sent_texts(bot)[0]


async def test_image_is_sent_as_photo() -> None:
    bot = fake_bot()
    await bot_main.answer(bot, CHAT_ID, BotResponse("caption", b"\x89PNG"))
    bot.send_photo.assert_awaited_once()
    assert bot.send_photo.await_args.args == (CHAT_ID, b"\x89PNG")
    assert bot.send_photo.await_args.kwargs["caption"] == "caption"
    bot.send_message.assert_not_awaited()


async def test_daily_fetch_posts_and_pins(db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot_main, "LOG_CHANNEL_ID", "-100")
    bot = fake_bot()
    await bot_main.daily_fetch(bot)
    bot.send_message.assert_awaited_once()
    bot.pin_chat_message.assert_awaited_once_with("-100", 7)


async def test_daily_fetch_without_channel_only_fetches(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bot_main, "LOG_CHANNEL_ID", None)
    bot = fake_bot()
    await bot_main.daily_fetch(bot)
    bot.send_message.assert_not_awaited()


async def test_update_handler_answers_its_message(user: User) -> None:
    bot = fake_bot()
    update = SimpleNamespace(message=fake_message("/user"))
    await bot_main._on_command(update, SimpleNamespace(bot=bot))  # type: ignore[arg-type]
    assert user.battle_tag in sent_texts(bot)[0]

    await bot_main._on_command(SimpleNamespace(message=None), SimpleNamespace(bot=bot))  # type: ignore[arg-type]
    bot.send_message.assert_awaited_once()


async def test_daily_post_failure_is_logged(
    db: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(bot_main, "LOG_CHANNEL_ID", "-100")
    bot = fake_bot()
    bot.send_message.side_effect = TelegramError("Forbidden: bot was kicked")
    await bot_main.daily_fetch(bot)
    assert "Couldn't post the daily ranking" in caplog.text
    bot.pin_chat_message.assert_not_awaited()


def test_daily_fetch_is_scheduled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot_main, "DAILY_FETCH_TIME", "08:05")
    application = SimpleNamespace(job_queue=MagicMock())
    bot_main._schedule_daily_fetch(application)  # type: ignore[arg-type]
    application.job_queue.run_daily.assert_called_once_with(bot_main._daily_job, time(8, 5))


def test_daily_fetch_needs_the_job_queue() -> None:
    with pytest.raises(RuntimeError, match="job-queue"):
        bot_main._schedule_daily_fetch(SimpleNamespace(job_queue=None))  # type: ignore[arg-type]


async def test_daily_job_fetches_with_its_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = AsyncMock()
    monkeypatch.setattr(bot_main, "daily_fetch", fetch)
    bot = fake_bot()
    await bot_main._daily_job(SimpleNamespace(bot=bot))  # type: ignore[arg-type]
    fetch.assert_awaited_once_with(bot)


def _callback_update(data: str) -> Update:
    tapper = TelegramUser(id=1, first_name="Foo", is_bot=False)
    query = CallbackQuery(id="1", from_user=tapper, chat_instance="chat", data=data)
    return Update(update_id=1, callback_query=query)


def test_main_polls_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    polled: dict[str, Any] = {}

    def run_polling(application: Application, **kwargs: Any) -> None:
        polled.update(kwargs, application=application)

    monkeypatch.setenv("BOT_TOKEN", "123:abc")
    monkeypatch.setattr(Application, "run_polling", run_polling)
    bot_main.main()
    application = polled["application"]
    commands, buttons = application.handlers[0]
    assert isinstance(commands, MessageHandler) and commands.callback is bot_main._on_command
    assert isinstance(buttons, CallbackQueryHandler) and buttons.callback is bot_main._on_button
    assert buttons.check_update(_callback_update("profile:1:2:1:6m"))
    assert not buttons.check_update(_callback_update("something else"))
    assert application.bot.defaults.parse_mode == "HTML"
    assert application.bot.defaults.tzinfo == get_localzone()
    [job] = application.job_queue.jobs()
    assert job.callback is bot_main._daily_job
    assert polled["drop_pending_updates"] is True
    assert "callback_query" in polled["allowed_updates"]


def _buttons() -> list[list[Button]]:
    return [
        [Button("🇺🇸 US", "profile:1:1:1:6m", selected=True), Button("🇪🇺 EU", "profile:1:2:1:6m")]
    ]


async def test_buttons_go_under_the_photo() -> None:
    bot = fake_bot()
    await bot_main.answer(bot, CHAT_ID, BotResponse("caption", b"\x89PNG", _buttons()))
    markup = bot.send_photo.await_args.kwargs["reply_markup"]
    us, eu = markup.inline_keyboard[0]
    assert (us.text, us.style, eu.text, eu.style) == ("🇺🇸 US", "primary", "🇪🇺 EU", None)
    assert eu.callback_data == "profile:1:2:1:6m"


async def test_buttons_of_a_text_go_under_its_last_part() -> None:
    bot = fake_bot()
    text = "\n".join(f"line {i}" for i in range(1000))
    await bot_main.answer(bot, CHAT_ID, BotResponse(text, buttons=_buttons()))
    markups = [call.kwargs["reply_markup"] for call in bot.send_message.await_args_list]
    assert len(markups) > 1 and markups[-1] is not None
    assert all(markup is None for markup in markups[:-1])


def _tap(data: str | None, edit: Any = None) -> Any:
    query = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_media=edit or AsyncMock())
    return SimpleNamespace(callback_query=query)


async def test_a_tap_replaces_the_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bot_main, "profile_button", lambda data: BotResponse(data, b"\x89PNG", _buttons())
    )
    update = _tap("profile:1:2:1:6m")
    await bot_main._on_button(update, SimpleNamespace())  # type: ignore[arg-type]
    query = update.callback_query
    query.answer.assert_awaited_once()
    media = query.edit_message_media.await_args.args[0]
    assert media.caption == "profile:1:2:1:6m"
    assert query.edit_message_media.await_args.kwargs["reply_markup"] is not None


async def test_tapping_what_is_shown_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot_main, "profile_button", lambda data: BotResponse(data, b"\x89PNG"))
    not_modified = AsyncMock(side_effect=BadRequest("Message is not modified: same content"))
    await bot_main._on_button(_tap("profile:1:1:1:6m", not_modified), SimpleNamespace())  # type: ignore[arg-type]

    other = AsyncMock(side_effect=BadRequest("Message to edit not found"))
    with pytest.raises(BadRequest):
        await bot_main._on_button(_tap("profile:1:1:1:6m", other), SimpleNamespace())  # type: ignore[arg-type]


async def test_a_stale_tap_changes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot_main, "profile_button", lambda data: None)
    update = _tap("profile:999:1:1:6m")
    await bot_main._on_button(update, SimpleNamespace())  # type: ignore[arg-type]
    update.callback_query.answer.assert_awaited_once()
    update.callback_query.edit_message_media.assert_not_awaited()
    await bot_main._on_button(_tap(None), SimpleNamespace())  # type: ignore[arg-type]
