from sc2bot.controller import add_player, retrieve_user
from sc2bot.database import session
from sc2bot.database.helpers import create_or_update_user
from sc2bot.database.schema import User


def test_retrieve_user_not_exist(db):
    response = retrieve_user(1)
    assert "register" in response.text


def test_retrieve_user(user: User):
    response = retrieve_user(1)
    assert user.battle_tag in response.text
    assert user.telegram_username and user.telegram_username in response.text
