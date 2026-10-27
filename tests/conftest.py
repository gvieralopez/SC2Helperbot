import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sc2bot.database import session
from sc2bot.database.data import League, Race
from sc2bot.database.schema import Base, Player, PlayerStat, User


@pytest.fixture()
def data_folder():
    return Path(__file__).parent / "data"


@pytest.fixture()
def db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_maker = sessionmaker(bind=engine)
    monkeypatch.setattr(session, "db_session", session_maker())
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user(db) -> User:
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    session.db_session.add(user)
    session.db_session.commit()
    return user


@pytest.fixture()
def fake_metadata_response(data_folder):
    with Path(data_folder / "fake_metadata.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_battle_tag_response(data_folder):
    with Path(data_folder / "fake_battle_tag_info.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_ladder_info_response_1(data_folder):
    with Path(data_folder / "fake_ladder_info_1.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_ladder_info_response_2(data_folder):
    with Path(data_folder / "fake_ladder_info_2.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_ladder_summary_response(data_folder):
    with Path(data_folder / "fake_ladder_summary.json").open() as f:
        return json.load(f)


@pytest.fixture()
def add_stat():
    def _add_stat(player: Player, race: Race, mmr: int, league: League = League.GOLD) -> PlayerStat:
        stat = PlayerStat(
            player_id=player.id,
            race=race,  # type: ignore
            league=league,  # type: ignore
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
def ladders(user: User, add_stat):
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
