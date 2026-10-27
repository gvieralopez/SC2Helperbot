import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from sc2bot.database import session
from sc2bot.database.data import League, Race
from sc2bot.database.schema import Base, Player, PlayerStat, User


@pytest.fixture()
def data_folder() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture()
def db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_maker = sessionmaker(bind=engine)
    db_session = session_maker()
    monkeypatch.setattr(session, "db_session", db_session)
    yield
    db_session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def unbound_session(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """A session for session.connect() to bind, closed with its engine afterwards."""
    monkeypatch.setattr(session, "db_session", Session())
    yield
    engine = session.db_session.bind
    session.db_session.close()
    if isinstance(engine, Engine):
        engine.dispose()


@pytest.fixture
def user(db: None) -> User:
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    session.db_session.add(user)
    session.db_session.commit()
    return user


@pytest.fixture()
def fake_battle_tag_response(data_folder: Path) -> Any:
    with Path(data_folder / "fake_battle_tag_info.json").open() as f:
        return json.load(f)


@pytest.fixture()
def add_stat() -> Callable[..., PlayerStat]:
    def _add_stat(player: Player, race: Race, mmr: int, league: League = League.GOLD) -> PlayerStat:
        stat = PlayerStat(
            player_id=player.id,
            race=race,
            league=league,
            mmr=mmr,
            wins=3,
            losses=1,
            clan_tag="CLAN",
        )
        session.db_session.add(stat)
        session.db_session.commit()
        return stat

    return _add_stat


@pytest.fixture()
def ladders(user: User, add_stat: Callable[..., PlayerStat]) -> tuple[User, User]:
    """Two users: foo (EU zerg + US terran, zerg played twice) and qux (EU protoss)."""
    other = User(telegram_id=2, telegram_username="qux", battle_tag="Qux#1234")
    session.db_session.add(other)
    session.db_session.commit()
    foo_eu = Player(user_id=user.id, region_id=2, profile_id=11, display_name="FooEU")
    foo_us = Player(user_id=user.id, region_id=1, profile_id=12, display_name="FooUS")
    qux_eu = Player(user_id=other.id, region_id=2, profile_id=21, display_name="QuxEU")
    session.db_session.add_all([foo_eu, foo_us, qux_eu])
    session.db_session.commit()
    add_stat(foo_eu, Race.ZERG, 3000)
    add_stat(foo_eu, Race.ZERG, 3100, League.DIAMOND)
    add_stat(foo_us, Race.TERRAN, 2500)
    add_stat(qux_eu, Race.PROTOSS, 3500, League.MASTER)
    return user, other
