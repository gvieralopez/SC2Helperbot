import re
from typing import Any

import pytest

from sc2bot import __main__ as bot_main
from sc2bot.bot_response import BotResponse, split_text
from sc2bot.controller import ladders
from sc2bot.database import session
from sc2bot.database.data import League, Race
from sc2bot.database.schema import Player, PlayerStat, User
from tests.test_main import _bot, _message


def _utf16(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


@pytest.fixture()
def crowd(db: None) -> None:
    """150 users with one ladder each: a /ladders reply far over Telegram's 4096 limit."""
    for i in range(150):
        user = User(telegram_id=i, telegram_username=f"user{i}", battle_tag=f"Player{i}#1234")
        session.db_session.add(user)
        session.db_session.flush()
        player = Player(user_id=user.id, region_id=2, profile_id=i, display_name=f"Player{i}")
        session.db_session.add(player)
        session.db_session.flush()
        stat = PlayerStat(
            player_id=player.id,
            race=Race.ZERG,
            league=League.DIAMOND,
            mmr=5000 - i,
            wins=3,
            losses=1,
            clan_tag="CLAN",
        )
        session.db_session.add(stat)
    session.db_session.commit()


def _lines(text: str) -> list[str]:
    return [line for line in text.split("\n") if line]


def test_long_ranking_is_cut_between_lines(crowd: None) -> None:
    text = ladders().text
    assert _utf16(text) > bot_main.MESSAGE_LIMIT

    parts = split_text(text, bot_main.MESSAGE_LIMIT)

    assert len(parts) > 1
    assert all(_utf16(part) <= bot_main.MESSAGE_LIMIT for part in parts)
    for part in parts:
        for tag in ("b", "i", "code"):
            assert part.count(f"<{tag}>") == part.count(f"</{tag}>")
    assert [line for part in parts for line in _lines(part)] == _lines(text)


def test_short_text_is_one_part() -> None:
    assert split_text("<b>Title</b>\n\nline", 4096) == ["<b>Title</b>\n\nline"]


def test_limit_counts_utf16_like_telegram() -> None:
    flags = "🇪🇺" * 10  # 4 UTF-16 units each
    assert split_text(f"{flags}\n{flags}", 81) == [f"{flags}\n{flags}"]  # 40 + 1 + 40
    assert split_text(f"{flags}\n{flags}", 80) == [flags, flags]


async def test_long_answer_is_sent_in_parts(crowd: None) -> None:
    message = _message("/ladders")
    await bot_main.answer(message, ladders())
    sent = [call.args[0] for call in message.answer.await_args_list]
    assert len(sent) > 1
    assert all(_utf16(part) <= bot_main.MESSAGE_LIMIT for part in sent)


async def test_long_caption_goes_after_the_photo() -> None:
    message = _message("/profile")
    text = "\n".join(f"<code>#{i}</code> line" for i in range(100))
    await bot_main.answer(message, BotResponse(text, b"\x89PNG"))
    message.answer_photo.assert_awaited_once()
    assert "caption" not in message.answer_photo.await_args.kwargs
    sent = "\n".join(call.args[0] for call in message.answer.await_args_list)
    assert _lines(sent) == _lines(text)


async def test_long_daily_ranking_pins_its_first_part(
    crowd: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bot_main, "LOG_CHANNEL_ID", "-100")
    monkeypatch.setattr(bot_main, "fetch_all_users", ladders)
    bot: Any = _bot()
    await bot_main.daily_fetch(bot)
    assert bot.send_message.await_count > 1
    assert re.search("Ranking|ladders", bot.send_message.await_args_list[0].args[1])
    bot.pin_chat_message.assert_awaited_once_with("-100", 7)
