from typing import Any

import requests_mock

from sc2bot.controller import set_battle_tag
from sc2bot.database import session
from sc2bot.database.schema import User


def test_register_wrong_battle_tag(db: None) -> None:
    response = set_battle_tag("bar", telegram_id=1, telegram_username="foo")
    assert "battletag" in response.text.lower()


def test_register(db: None, fake_battle_tag_response: Any) -> None:
    battle_tag = "quuz#1234"
    with requests_mock.Mocker() as m:
        m.get("https://sc2pulse.nephest.com/sc2/api/characters", json=fake_battle_tag_response)
        response = set_battle_tag(battle_tag, telegram_id=1, telegram_username="foo")
    assert "8972769" in response.text
    assert battle_tag in response.text
    assert "foo" in response.text
    user = session.db_session.query(User).filter_by(telegram_id=1).one()
    assert user.telegram_username == "foo"
    assert user.battle_tag == battle_tag
    assert sorted(player.profile_id for player in user.players) == [8972769, 10993388]


def test_register_existing(db: None, user: User, fake_battle_tag_response: Any) -> None:
    battle_tag = "quuz#1234"
    with requests_mock.Mocker() as m:
        m.get("https://sc2pulse.nephest.com/sc2/api/characters", json=fake_battle_tag_response)
        set_battle_tag(battle_tag, telegram_id=user.telegram_id, telegram_username="baz")
    assert user.telegram_username == "baz"
    assert user.battle_tag == battle_tag
