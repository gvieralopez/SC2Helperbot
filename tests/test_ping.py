from types import SimpleNamespace
from typing import Any

import pytest
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest

from sc2bot import __main__ as bot_main
from sc2bot.controller import ping_texts
from sc2bot.database import session
from sc2bot.database.schema import User
from sc2bot.routes import routes
from tests.fakes import fake_bot, fake_message, sent_texts

LEFT = {7: ChatMemberStatus.LEFT, 8: ChatMemberStatus.BANNED}


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


def _bot(not_in_group: tuple[int, ...] = ()) -> Any:
    async def get_chat_member(chat_id: int, user_id: int) -> Any:
        if user_id in not_in_group:
            raise BadRequest("User not found")
        if user_id == 6:  # restricted but still in the group
            return SimpleNamespace(status=ChatMemberStatus.RESTRICTED, is_member=True)
        return SimpleNamespace(status=LEFT.get(user_id, ChatMemberStatus.MEMBER))

    return fake_bot(get_chat_member)


def test_four_mentions_per_message(nine_users: list[User]) -> None:
    texts = ping_texts(nine_users)
    assert [text.count("@") + text.count("tg://") for text in texts] == [4, 4, 1]
    assert "@user1 @user2 @user3 @user4" in texts[0]
    assert '<a href="tg://user?id=9">Nine</a>' in texts[2]


async def test_ping_in_a_private_chat_is_its_help(nine_users: list[User]) -> None:
    bot = _bot()
    await bot_main.handle_command(fake_message("/ping", "private"), bot)
    assert sent_texts(bot) == [routes["ping"].help.text]


async def test_ping_mentions_the_group_members_but_the_caller(nine_users: list[User]) -> None:
    bot = _bot(not_in_group=(5,))
    await bot_main.handle_command(fake_message("/ping", "supergroup", sender=1), bot)
    sent = sent_texts(bot)
    # 2, 3, 4, 6 (restricted, still a member), 9; not 1 (the caller), 5 (never here), 7, 8 (gone).
    assert sent == ["📣 @user2 @user3 @user4 @user6", '📣 <a href="tg://user?id=9">Nine</a>']


async def test_ping_with_nobody_else(nine_users: list[User]) -> None:
    bot = _bot(not_in_group=(2, 3, 4, 5, 6, 9))
    await bot_main.handle_command(fake_message("/ping", "group", sender=1), bot)
    [text] = sent_texts(bot)
    assert "Nobody else" in text and "/register" in text
