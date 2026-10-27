from sc2bot.controller import retrieve_user
from sc2bot.database.schema import User


def test_retrieve_user_not_exist(db: None) -> None:
    response = retrieve_user(telegram_id=1)
    assert "register" in response.text


def test_retrieve_user(user: User) -> None:
    response = retrieve_user(telegram_id=1)
    assert user.battle_tag in response.text
    assert user.telegram_username and user.telegram_username in response.text
