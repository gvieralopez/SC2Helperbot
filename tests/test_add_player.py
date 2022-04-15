import pytest
import requests_mock

from sc2bot.controller import add_new_player_stats, add_player
from sc2bot.database import session
from sc2bot.database.helpers import create_or_update_user
from sc2bot.database.schema import User


@pytest.fixture
def user(db) -> User:
    return create_or_update_user(session.db_session, 1, "foo", "bar")


def test_add_player_wrong_user(db):
    response = add_player(1, "foo")
    assert "register" in response.text


def test_add_player_wrong_url(user: User):
    response = add_player(1, "invalid")
    assert "URL" in response.text


def test_add_player_no_api_response(user: User):
    response = add_player(1, "https://starcraft2.com/en-us/profile/1/2/1234")
    assert "display name" in response.text


def test_add_player(user: User, fake_metadata_response):
    with requests_mock.Mocker() as m:
        m.get(
            "https://starcraft2.com/en-us/api/sc2/metadata/profile/1/1/10993388",
            json=fake_metadata_response,
        )
        response = add_player(1, "https://starcraft2.com/en-us/profile/1/1/10993388")
    assert "10993388" in response.text
    assert user.battle_tag in response.text
    assert user.telegram_username in response.text
    assert len(user.players) == 1
    assert user.players[0].profile_id == 10993388
