import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import requests_mock

from sc2bot.controller import add_new_player_stats, fetch_all_users
from sc2bot.database import session
from sc2bot.database.data import League, Race
from sc2bot.database.schema import PlayerStat, User

API = "https://sc2pulse.nephest.com/sc2/api"


@pytest.fixture()
def pulse_seasons(data_folder: Path) -> Any:
    return json.loads((data_folder / "pulse_seasons.json").read_text())


@pytest.fixture()
def pulse_teams(data_folder: Path) -> Any:
    return json.loads((data_folder / "pulse_teams.json").read_text())


@pytest.fixture()
def farseer(db: None) -> User:
    user = User(telegram_id=1, telegram_username="foo", battle_tag="FarSeer#11726")
    session.db_session.add(user)
    session.db_session.commit()
    return user


def _mock_pulse(m: requests_mock.Mocker, characters: Any, seasons: Any, teams: Any) -> None:
    m.get(f"{API}/characters", json=characters)
    m.get(f"{API}/seasons", json=seasons)
    m.get(f"{API}/character-teams", json=teams)


def _stats() -> list[tuple[Any, ...]]:
    stats = session.db_session.query(PlayerStat).order_by(PlayerStat.id).all()
    return [(s.player.region_id, s.race, s.league, s.mmr, s.wins, s.losses) for s in stats]


def test_fetch_wrong_user(db: None) -> None:
    response = add_new_player_stats(telegram_id=1)
    assert "register" in response.text


def test_fetch_adds_profiles_and_ladders(
    farseer: User, fake_battle_tag_response: Any, pulse_seasons: Any, pulse_teams: Any
) -> None:
    with requests_mock.Mocker() as m:
        _mock_pulse(m, fake_battle_tag_response, pulse_seasons, pulse_teams)
        response = add_new_player_stats(telegram_id=1)

    assert {p.profile_id for p in farseer.players} == {8972769, 10993388}
    assert "8972769" in response.text and "10993388" in response.text
    teams_request = m.request_history[-1]
    assert teams_request.qs["season"] == ["68"]
    assert set(teams_request.qs["toonhandle"]) == {"2-s2-1-8972769", "1-s2-1-10993388"}
    assert (2, Race.ZERG, League.DIAMOND, 3572, 18, 16) in _stats()
    assert len(_stats()) == 5
    eu = session.db_session.query(PlayerStat).filter_by(mmr=3572).one()
    assert (eu.clan_tag, eu.created_at) == ("H2OKT", datetime(2026, 8, 16, 19, 19, 53))


def test_fetch_skips_unchanged_ladders(
    farseer: User, fake_battle_tag_response: Any, pulse_seasons: Any, pulse_teams: Any
) -> None:
    with requests_mock.Mocker() as m:
        _mock_pulse(m, fake_battle_tag_response, pulse_seasons, pulse_teams)
        add_new_player_stats(telegram_id=1)
        add_new_player_stats(telegram_id=1)
    assert len(_stats()) == 5

    pulse_teams[2].update(rating=3600, wins=19, lastPlayed="2026-10-27T18:00:00Z")
    with requests_mock.Mocker() as m:
        _mock_pulse(m, fake_battle_tag_response, pulse_seasons, pulse_teams)
        add_new_player_stats(telegram_id=1)
    assert len(_stats()) == 6
    assert _stats()[-1] == (2, Race.ZERG, League.DIAMOND, 3600, 19, 16)


def test_fetch_with_pulse_down(farseer: User) -> None:
    with requests_mock.Mocker() as m:
        _mock_pulse(m, [], [], [])
        m.get(f"{API}/characters", status_code=503)
        m.get(f"{API}/seasons", status_code=503)
        response = add_new_player_stats(telegram_id=1)
    assert farseer.battle_tag in response.text
    assert _stats() == []


def test_fetch_all_users(ladders: tuple[User, User], pulse_seasons: Any) -> None:
    with requests_mock.Mocker() as m:
        _mock_pulse(m, [], pulse_seasons, [])
        response = fetch_all_users()
    searches = [r.qs["query"] for r in m.request_history if r.path.endswith("/characters")]
    assert searches == [["bar"], ["qux#1234"]]
    teams_request = m.request_history[-1]
    assert set(teams_request.qs["toonhandle"]) == {"2-s2-1-11", "1-s2-1-12", "2-s2-1-21"}
    assert "Bot Ranking" in response.text and "QuxEU" in response.text
