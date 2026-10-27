import json
from pathlib import Path
from typing import Any

import requests_mock

from sc2bot.client.sc2_pulse import current_ladders, current_seasons, get_battle_tag_info
from sc2bot.database.schema import Player, User

SEARCH = "https://sc2pulse.nephest.com/sc2/api/characters"


def test_battle_tag_info(fake_battle_tag_response: Any) -> None:
    with requests_mock.Mocker() as m:
        m.get(SEARCH, json=fake_battle_tag_response)
        players = get_battle_tag_info(User(id=111, battle_tag="FarSeer#11726"))

    assert m.last_request.qs == {"query": ["farseer#11726"]}
    found = [(p.user_id, p.region_id, p.profile_id, p.display_name) for p in players]
    assert found == [(111, 1, 10993388, "FarSeer"), (111, 2, 8972769, "FarSeer")]


def test_battle_tag_info_skips_other_realms(fake_battle_tag_response: Any) -> None:
    fake_battle_tag_response[0]["members"]["character"]["realm"] = 2
    with requests_mock.Mocker() as m:
        m.get(SEARCH, json=fake_battle_tag_response)
        players = get_battle_tag_info(User(id=111, battle_tag="FarSeer#11726"))

    assert [p.profile_id for p in players] == [8972769]


def test_battle_tag_info_failure() -> None:
    with requests_mock.Mocker() as m:
        m.get(SEARCH, status_code=503)
        assert get_battle_tag_info(User(id=111, battle_tag="FarSeer#11726")) == []


def test_current_seasons(data_folder: Path) -> None:
    seasons = json.loads((data_folder / "pulse_seasons.json").read_text())
    with requests_mock.Mocker() as m:
        m.get("https://sc2pulse.nephest.com/sc2/api/seasons", json=seasons)
        assert current_seasons() == {1: 68, 2: 68, 3: 68}


def test_current_ladders_without_a_season() -> None:
    china = Player(id=1, region_id=5, profile_id=1, display_name="Foo")
    with requests_mock.Mocker() as m:
        m.get("https://sc2pulse.nephest.com/sc2/api/seasons", json=[])
        assert current_ladders([china]) == []
    assert len(m.request_history) == 1


def test_current_ladders_of_nobody_asks_nothing() -> None:
    with requests_mock.Mocker() as m:
        assert current_ladders([]) == []
    assert m.request_history == []
