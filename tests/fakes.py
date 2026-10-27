"""Stand-ins for python-telegram-bot's Bot and Message, holding only what the bot uses."""

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

CHAT_ID = -100


def fake_message(
    text: str, chat_type: str = "private", sender: int = 1, username: str | None = "foo"
) -> Any:
    return SimpleNamespace(
        text=text,
        chat=SimpleNamespace(id=CHAT_ID, type=chat_type),
        from_user=SimpleNamespace(id=sender, username=username, full_name="Foo Bar"),
    )


def fake_bot(get_chat_member: Callable[..., Any] | None = None) -> Any:
    return SimpleNamespace(
        username="SC2Helperbot",
        send_message=AsyncMock(return_value=SimpleNamespace(message_id=7)),
        send_photo=AsyncMock(),
        pin_chat_message=AsyncMock(),
        get_chat_member=AsyncMock(side_effect=get_chat_member),
    )


def sent_texts(bot: Any) -> list[str]:
    return [call.args[1] for call in bot.send_message.await_args_list]
