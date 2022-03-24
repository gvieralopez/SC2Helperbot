from datetime import datetime, timezone
from time import sleep

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from sc2bot.database.helpers import create_or_update_user, create_or_update_player
from sc2bot.database.schema import Base, User, Player


@pytest.fixture()
def sqlalchemy_connect_url():
    return "sqlite:///:memory:"


@pytest.fixture()
def db_engine(sqlalchemy_connect_url):
    engine_ = create_engine(sqlalchemy_connect_url)

    yield engine_

    engine_.dispose()


@pytest.fixture()
def connection(db_engine):
    return db_engine.connect()


@pytest.fixture()
def setup_database(connection):
    Base.metadata.bind = connection
    Base.metadata.create_all()

    yield

    Base.metadata.drop_all()


@pytest.fixture
def db_session(setup_database, connection):
    transaction = connection.begin()
    yield scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=connection))
    transaction.rollback()


@pytest.fixture
def user_list():
    return [
        {
            "telegram_id": 1,
            "telegram_username": "foo",
            "battle_tag": "bar",
        },
        {
            "telegram_id": 2,
            "telegram_username": "baz",
            "battle_tag": "quz",
        },
    ]


def test_user_create(user_list, db_session):
    for user_data in user_list:
        create_or_update_user(db_session, **user_data)

    assert db_session.query(User).count() == 2
    now = datetime.now(tz=timezone.utc)
    assert all(
        (now - user.modified_at.replace(tzinfo=timezone.utc)).total_seconds() < 5
        for user in db_session.query(User).all()
    )
    assert all(
        (now - user.created_at.replace(tzinfo=timezone.utc)).total_seconds() < 5
        for user in db_session.query(User).all()
    )


def test_user_update(user_list, db_session):
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    db_session.add(user)
    db_session.commit()
    created_at = user.created_at
    modified_at = user.modified_at
    sleep(1)
    user = create_or_update_user(db_session, 1, "baz", "quz")
    assert user.created_at == created_at
    assert user.modified_at != modified_at
    assert user.telegram_id == 1
    assert user.telegram_username == "baz"
    assert user.battle_tag == "quz"


def test_player_create(db_session):
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    db_session.add(user)
    db_session.commit()

    player = create_or_update_player(db_session, user, 1, 2, "foo")
    assert db_session.query(Player).count() == 1
    now = datetime.now(tz=timezone.utc)
    assert (now - player.modified_at.replace(tzinfo=timezone.utc)).total_seconds() < 5
    assert (now - player.created_at.replace(tzinfo=timezone.utc)).total_seconds() < 5


def test_player_update(db_session):
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    player = Player(user_id=user.id, region_id=1, profile_id=2, display_name="baz")
    db_session.add(user)
    db_session.add(player)
    db_session.commit()
    created_at = player.created_at
    modified_at = player.modified_at

    sleep(1)
    player = create_or_update_player(db_session, user, 1, 2, "quz")
    assert db_session.query(Player).count() == 1
    assert player.display_name == "quz"
    assert player.created_at == created_at
    assert player.modified_at != modified_at
