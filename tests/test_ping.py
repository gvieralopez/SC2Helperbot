from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from sc2bot import __main__ as bot_main
from sc2bot.controller import ping_texts
from sc2bot.database import session
from sc2bot.database.schema import User
from sc2bot.routes import routes

LEFT = {7: ChatMemberStatus.LEFT, 8: ChatMemberStatus.KICKED}


@pytest.fixture()
def nine_users(db: None) -> list[User]:
    """Users 1-9; user 9 has no username, so it is stored as a link."""
    users = [
        User(telegram_id=i, telegram_username=f"user{i}", battle_tag=f"Player{i}#1234")
        for i in range(1, 9)
    ]
    users.append(
        User(
            telegram_id=9,
            telegram_username='<a href="tg://user?id=9">Nine</a>',
            battle_tag="N#1234",
        )
    )
    session.db_session.add_all(users)
    session.db_session.commit()
    return users


def _message(chat_type: str, sender: int = 1) -> Any:
    return SimpleNamespace(
        text="/ping",
        chat=SimpleNamespace(id=-100, type=chat_type),
        from_user=SimpleNamespace(id=sender, username=f"user{sender}", full_name="One"),
        answer=AsyncMock(),
        answer_photo=AsyncMock(),
    )


def _bot(not_in_group: tuple[int, ...] = ()) -> Any:
    async def get_chat_member(chat_id: int, user_id: int) -> Any:
        if user_id in not_in_group:
            raise TelegramBadRequest(method=None, message="Bad Request: user not found")  # type: ignore[arg-type]
        status = LEFT.get(user_id, ChatMemberStatus.MEMBER)
        if user_id == 6:  # restricted but still in the group
            return SimpleNamespace(status=ChatMemberStatus.RESTRICTED, is_member=True)
        return SimpleNamespace(status=status)

    return SimpleNamespace(
        me=AsyncMock(return_value=SimpleNamespace(username="SC2Helperbot")),
        get_chat_member=AsyncMock(side_effect=get_chat_member),
    )


def _sent(message: Any) -> list[str]:
    return [call.args[0] for call in message.answer.await_args_list]


def test_four_mentions_per_message(nine_users: list[User]) -> None:
    texts = ping_texts(nine_users)
    assert [text.count("@") + text.count("tg://") for text in texts] == [4, 4, 1]
    assert "@user1 @user2 @user3 @user4" in texts[0]
    assert '<a href="tg://user?id=9">Nine</a>' in texts[2]


async def test_ping_in_a_private_chat_is_its_help(nine_users: list[User]) -> None:
    message = _message("private")
    await bot_main.handle_command(message, _bot())
    assert _sent(message) == [routes["ping"].help.text]


async def test_ping_mentions_the_group_members_but_the_caller(nine_users: list[User]) -> None:
    message = _message("supergroup", sender=1)
    await bot_main.handle_command(message, _bot(not_in_group=(5,)))
    sent = _sent(message)
    # 2, 3, 4, 6 (restricted, still a member), 9; not 1 (the caller), 5 (never here), 7, 8 (gone).
    assert sent == ["📣 @user2 @user3 @user4 @user6", '📣 <a href="tg://user?id=9">Nine</a>']


async def test_ping_with_nobody_else(nine_users: list[User]) -> None:
    message = _message("group", sender=1)
    await bot_main.handle_command(message, _bot(not_in_group=(2, 3, 4, 5, 6, 9)))
    [text] = _sent(message)
    assert "Nobody else" in text and "/register" in text
