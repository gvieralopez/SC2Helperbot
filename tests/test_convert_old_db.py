import json
import sqlite3
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sc2bot.database.data import League
from sc2bot.database.data import Race
from sc2bot.database.schema import Player
from sc2bot.database.schema import PlayerStat
from sc2bot.database.schema import User
from scripts.convert_old_db import main

OLD_SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY, arroba VARCHAR(150), tgid INTEGER NOT NULL,
    "US_id" INTEGER, "EU_id" INTEGER, "KR_id" INTEGER, "TW_id" INTEGER,
    display_name VARCHAR(50), battle_tag VARCHAR(50),
    created_at DATETIME NOT NULL, modified_at DATETIME NOT NULL
);
CREATE TABLE usersmmr (
    id INTEGER PRIMARY KEY, region INTEGER NOT NULL, race VARCHAR(10) NOT NULL,
    user_id INTEGER, ladder_id INTEGER NOT NULL, league VARCHAR(15) NOT NULL,
    mmr INTEGER NOT NULL, wins INTEGER NOT NULL, losses INTEGER NOT NULL,
    clan VARCHAR(15), history VARCHAR(30),
    created_at DATETIME NOT NULL, modified_at DATETIME NOT NULL
);
"""
CREATED = "2022-02-01 10:00:00.000000"
UPDATED = "2022-03-21 17:30:05.123456"


@pytest.fixture()
def old_data(tmp_path):
    old_db = tmp_path / "sc2.db"
    connection = sqlite3.connect(old_db)
    connection.executescript(OLD_SCHEMA)
    connection.executemany(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?)",
        [
            (1, "@foo", 100, 111, 222, "Foo", "Foo#1234", CREATED, UPDATED),
            (2, "@bar", 200, None, 333, None, "Bar#5678", CREATED, UPDATED),
        ],
    )
    connection.executemany(
        "INSERT INTO usersmmr VALUES (?, ?, ?, ?, 9, ?, ?, ?, ?, ?, NULL, ?, ?)",
        [
            (1, 2, "zerg", 1, "diamond", 3100, 30, 20, "CLAN", CREATED, UPDATED),
            (2, 1, "terran", 1, "gold", 2500, 5, 5, "", CREATED, UPDATED),
            (3, 2, "protoss", 2, "master", 4000, 40, 10, "", CREATED, UPDATED),
            (4, 1, "zerg", 2, "bronze", 1000, 1, 1, "", CREATED, UPDATED),  # no US profile
        ],
    )
    connection.commit()
    history = tmp_path / "history"
    history.mkdir()
    # Ladder 1: two old points plus a last one on the day of the last update (not repeated).
    points = {"mmrs": [3000, 3050, 3100], "dates": ["04-02-2022", "05-02-2022", "21-03-2022"]}
    (history / "h1.json").write_text(json.dumps(points))
    (history / "h3.json").write_text(json.dumps({"mmrs": [3900], "dates": ["10-03-2022"]}))
    (history / "h16.json").write_text(json.dumps({"mmrs": [1], "dates": ["01-01-2022"]}))
    return old_db, history


def test_convert_old_db(old_data, tmp_path):
    new_db = f"sqlite:///{tmp_path / 'new.db'}"
    report = main(*old_data, new_db)

    assert (report.users, report.players, report.stats) == (2, 3, 6)
    assert report.skipped == ["ladder 4: user has no profile in region", "h16.json: no ladder"]
    with Session(create_engine(new_db)) as db_session:
        foo = db_session.query(User).filter_by(telegram_id=100).one()
        assert (foo.telegram_username, foo.battle_tag) == ("@foo", "Foo#1234")
        players = {player.region_id: player for player in foo.players}  # type: ignore
        assert {r: (p.profile_id, p.display_name) for r, p in players.items()} == {
            1: (111, "Foo"),
            2: (222, "Foo"),
        }
        zerg = players[2].stats  # type: ignore
        assert [stat.mmr for stat in zerg] == [3000, 3050, 3100]
        assert zerg[0].created_at == datetime(2022, 2, 4)
        assert {(s.race, s.league, s.wins, s.losses, s.clan_tag) for s in zerg} == {
            (Race.ZERG, League.DIAMOND, 30, 20, "CLAN")
        }
        terran = players[1].stats  # type: ignore
        assert [(stat.mmr, stat.clan_tag) for stat in terran] == [(2500, None)]
        assert terran[0].created_at == datetime(2022, 3, 21, 17, 30, 5, 123456)

        bar = db_session.query(Player).filter_by(profile_id=333).one()
        assert bar.display_name == "Bar"
        assert [stat.mmr for stat in bar.stats] == [3900, 4000]  # type: ignore
        assert db_session.query(PlayerStat).count() == 6


def test_convert_refuses_a_database_with_users(old_data, tmp_path):
    new_db = f"sqlite:///{tmp_path / 'new.db'}"
    main(*old_data, new_db)
    with pytest.raises(SystemExit):
        main(*old_data, new_db)
