from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from sc2bot import __main__ as bot_main
from sc2bot.bot_response import BotResponse
from sc2bot.database.schema import User
from sc2bot.routes import routes


def _message(text: str) -> Any:
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=1, username="foo"),
        answer=AsyncMock(),
        answer_photo=AsyncMock(),
    )


def _bot() -> Any:
    return SimpleNamespace(
        me=AsyncMock(return_value=SimpleNamespace(username="SC2Helperbot")),
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=7)),
        pin_chat_message=AsyncMock(),
    )


async def test_command_is_answered(user: User) -> None:
    message = _message("/user")
    await bot_main.handle_command(message, _bot())
    message.answer.assert_awaited_once()
    assert user.battle_tag in message.answer.await_args.args[0]


@pytest.mark.parametrize("text", ["/nope", "/rank@OtherBot", "/"])
async def test_unknown_or_foreign_commands_are_ignored(db: None, text: str) -> None:
    message = _message(text)
    await bot_main.handle_command(message, _bot())
    message.answer.assert_not_awaited()


async def test_failing_command_answers_its_usage(db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: str, **_kwargs: object) -> BotResponse:
        raise ValueError

    monkeypatch.setattr(routes["user"], "target", fail)
    message = _message("/user")
    await bot_main.handle_command(message, _bot())
    assert "/help user" in message.answer.await_args.args[0]


async def test_image_is_sent_as_photo() -> None:
    message = _message("/profile")
    await bot_main.answer(message, BotResponse("caption", b"\x89PNG"))
    message.answer_photo.assert_awaited_once()
    assert message.answer_photo.await_args.kwargs["caption"] == "caption"


async def test_daily_fetch_posts_and_pins(db: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot_main, "LOG_CHANNEL_ID", "-100")
    bot = _bot()
    await bot_main.daily_fetch(bot)
    bot.send_message.assert_awaited_once()
    bot.pin_chat_message.assert_awaited_once_with("-100", 7)


async def test_daily_fetch_without_channel_only_fetches(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bot_main, "LOG_CHANNEL_ID", None)
    bot = _bot()
    await bot_main.daily_fetch(bot)
    bot.send_message.assert_not_awaited()
