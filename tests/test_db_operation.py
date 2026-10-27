from collections.abc import Iterator
from datetime import UTC, datetime
from time import sleep
from typing import Any

import pytest
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from sc2bot.database.data import League, Race
from sc2bot.database.helpers import add_player_stat, create_or_update_player, create_or_update_user
from sc2bot.database.schema import Base, Player, User


@pytest.fixture()
def sqlalchemy_connect_url() -> str:
    return "sqlite:///:memory:"


@pytest.fixture()
def db_engine(sqlalchemy_connect_url: str) -> Iterator[Engine]:
    engine_ = create_engine(sqlalchemy_connect_url)

    yield engine_

    engine_.dispose()


@pytest.fixture()
def connection(db_engine: Engine) -> Iterator[Connection]:
    with db_engine.connect() as connection_:
        yield connection_


@pytest.fixture()
def setup_database(connection: Connection) -> Iterator[None]:
    Base.metadata.create_all(connection)
    connection.commit()

    yield

    Base.metadata.drop_all(connection)
    connection.commit()


@pytest.fixture
def db_session(setup_database: None, connection: Connection) -> Iterator[Session]:
    transaction = connection.begin()
    with sessionmaker(autoflush=False, bind=connection)() as session:
        yield session
    # A failed commit (the unique-constraint tests) already rolled it back.
    if transaction.is_active:
        transaction.rollback()


@pytest.fixture
def user_list() -> list[dict[str, Any]]:
    return [
        {"telegram_id": 1, "telegram_username": "foo", "battle_tag": "bar"},
        {"telegram_id": 2, "telegram_username": "baz", "battle_tag": "quz"},
    ]


@pytest.fixture
def user(db_session: Session) -> User:
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def player(db_session: Session, user: User) -> Player:
    player = Player(user_id=user.id, region_id=1, profile_id=2, display_name="baz")
    db_session.add(player)
    db_session.commit()
    return player


def test_user_create(user_list: list[dict[str, Any]], db_session: Session) -> None:
    for user_data in user_list:
        create_or_update_user(db_session, **user_data)

    assert db_session.query(User).count() == 2
    assert all(get_seconds_elapsed(user.modified_at) < 5 for user in db_session.query(User).all())
    assert all(get_seconds_elapsed(user.created_at) < 5 for user in db_session.query(User).all())


def test_user_update(user_list: list[dict[str, Any]], db_session: Session) -> None:
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


def test_player_create(db_session: Session, user: User) -> None:
    player = create_or_update_player(db_session, user, 1, 2, "foo")
    assert db_session.query(Player).count() == 1
    assert get_seconds_elapsed(player.modified_at) < 5
    assert get_seconds_elapsed(player.created_at) < 5


def test_player_update(db_session: Session, player: Player) -> None:
    created_at = player.created_at
    modified_at = player.modified_at

    sleep(1)
    player = create_or_update_player(db_session, player.user, 1, 2, "quz")
    assert db_session.query(Player).count() == 1
    assert player.display_name == "quz"
    assert player.created_at == created_at
    assert player.modified_at != modified_at


def test_player_stat(db_session: Session, player: Player) -> None:
    stat = add_player_stat(db_session, player, Race.PROTOSS, League.PLATINUM, 1234, 12, 1, "foo")
    assert db_session.query(Player).count() == 1
    assert get_seconds_elapsed(stat.created_at) < 5


def get_seconds_elapsed(since: datetime) -> float:
    return (datetime.now(tz=UTC) - since.replace(tzinfo=UTC)).total_seconds()


def test_telegram_id_is_unique(db_session: Session, user: User) -> None:
    db_session.add(User(telegram_id=user.telegram_id, telegram_username="other", battle_tag="x"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_profile_is_unique(db_session: Session, player: Player) -> None:
    db_session.add(
        Player(
            user_id=player.user_id,
            region_id=player.region_id,
            profile_id=player.profile_id,
            display_name="other",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
