from sc2bot.controller import list_users
from sc2bot.database import session
from sc2bot.database.schema import User


def test_list_users_empty(db):
    response = list_users(telegram_id=1)
    assert "No users" in response.text


def test_list_users(user: User):
    session.db_session.add(User(telegram_id=2, telegram_username="qux", battle_tag="Qux#1234"))
    session.db_session.commit()
    response = list_users(telegram_id=1)
    assert "foo" in response.text and "bar" in response.text
    assert "qux" in response.text and "Qux#1234" in response.text
