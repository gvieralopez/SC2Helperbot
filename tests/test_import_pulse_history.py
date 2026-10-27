from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import requests_mock
from scripts import import_pulse_history
from scripts.import_pulse_history import main
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sc2bot.database.data import League, Race
from sc2bot.database.schema import Base, Player, PlayerStat, User

API = import_pulse_history.API
DAY_1 = int(datetime(2022, 2, 4, 12, tzinfo=UTC).timestamp())
DAY_2 = int(datetime(2022, 2, 5, 12, tzinfo=UTC).timestamp())
SEASON_43 = int(datetime(2020, 6, 10, tzinfo=UTC).timestamp())


@pytest.fixture(autouse=True)
def no_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(import_pulse_history, "PAUSE", 0)


@pytest.fixture()
def database(tmp_path: Path) -> Iterator[tuple[str, sessionmaker[Session]]]:
    connection_string = f"sqlite:///{tmp_path / 'db.db'}"
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    user = User(telegram_id=1, telegram_username="foo", battle_tag="Foo#1234")
    db_session.add(user)
    db_session.commit()
    eu = Player(user_id=user.id, region_id=2, profile_id=8972769, display_name="Foo")
    us = Player(user_id=user.id, region_id=1, profile_id=111, display_name="Foo")
    db_session.add_all([eu, us])
    db_session.commit()
    # A hand-made sample that SC2 Pulse also has (same day and MMR): not imported twice.
    sample = PlayerStat(
        player_id=eu.id,
        race=Race.ZERG,
        league=League.DIAMOND,
        mmr=3500,
        wins=1,
        losses=1,
        created_at=datetime(2022, 2, 4, 17, 30),
    )
    db_session.add(sample)
    db_session.commit()
    db_session.close()
    yield connection_string, sessionmaker(bind=engine)
    engine.dispose()


def _team(uid: str) -> dict:
    return {"legacyUid": uid, "members": [{"clan": {"tag": "H2OKT"}}]}


def _history(uid: str, points: list[tuple[int, int, int, int | None, int]]) -> dict:
    timestamps, ratings, leagues, wins, games = (
        list(column) for column in zip(*points, strict=True)
    )
    return {
        "staticData": {"LEGACY_UID": uid},
        "history": {
            "TIMESTAMP": timestamps,
            "RATING": ratings,
            "LEAGUE_TYPE": leagues,
            "WINS": wins,
            "GAMES": games,
        },
    }


def _mock_pulse(mocker: requests_mock.Mocker) -> None:
    zerg, random = "201-0-2-1.8972769.3", "201-0-2-1.8972769.4"
    mocker.get(
        f"{API}/character-teams?toonHandle=2-S2-1-8972769",
        json=[_team(zerg), _team(zerg), _team(random)],
    )
    mocker.get(f"{API}/character-teams?toonHandle=1-S2-1-111", json=[])
    mocker.get(
        f"{API}/team-histories",
        json=[
            _history(zerg, [(SEASON_43, 2900, 2, 10, 20), (DAY_1, 3500, 4, 30, 50)]),
            _history(random, [(DAY_2, 3100, 4, 5, 8), (DAY_2 + 3600, 3120, 4, None, 9)]),
        ],
    )


def test_import_pulse_history(database: tuple[str, sessionmaker[Session]]) -> None:
    connection_string, session_maker = database
    with requests_mock.Mocker() as mocker:
        _mock_pulse(mocker)
        report = main(connection_string)

    assert (report.players, report.added, report.skipped) == (1, 3, 1)
    assert report.not_found == ["1-S2-1-111"]
    histories = [r for r in mocker.request_history if "team-histories" in r.url]
    assert len(histories) == 1
    assert set(histories[0].qs["teamlegacyuid"]) == {"201-0-2-1.8972769.3", "201-0-2-1.8972769.4"}

    with session_maker() as db_session:
        stats = db_session.query(PlayerStat).order_by(PlayerStat.created_at).all()
    season_43, sample, random, random_no_wins = stats
    assert (season_43.race, season_43.league, season_43.mmr) == (Race.ZERG, League.GOLD, 2900)
    assert (season_43.wins, season_43.losses, season_43.clan_tag) == (10, 10, "H2OKT")
    assert season_43.created_at == datetime(2020, 6, 10)
    assert sample.created_at == datetime(2022, 2, 4, 17, 30)
    assert (random.race, random.league, random.mmr, random.losses) == (
        Race.RANDOM,
        League.DIAMOND,
        3100,
        3,
    )
    assert (random_no_wins.wins, random_no_wins.losses) == (5, 4)


def test_import_twice_adds_nothing(database: tuple[str, sessionmaker[Session]]) -> None:
    connection_string, session_maker = database
    with requests_mock.Mocker() as mocker:
        _mock_pulse(mocker)
        main(connection_string)
        report = main(connection_string)
    assert (report.added, report.skipped) == (0, 4)
    with session_maker() as db_session:
        assert db_session.query(PlayerStat).count() == 4
