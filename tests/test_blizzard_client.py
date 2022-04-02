import base64
import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests_mock

from sc2bot.client.blizzard import BlizzardResolver, BlizzardAuthorizedResolver
from sc2bot.database.data import Race, League
from sc2bot.database.schema import Player


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
def fake_metadata_response(data_folder):
    with Path(data_folder / "fake_metadata.json").open() as f:
        return json.load(f)


def test_player_stats(
    fake_ladder_info_response_1, fake_ladder_info_response_2, fake_ladder_summary_response
):
    base_url = "http://api.com"
    profile_id = 10993388
    with requests_mock.Mocker() as m:
        m.get(
            f"{base_url}/sc2/profile/1/1/{profile_id}/ladder/summary",
            json=fake_ladder_summary_response,
        )
        m.get(
            f"{base_url}/sc2/profile/1/1/{profile_id}/ladder/307413",
            json=fake_ladder_info_response_1,
        ),
        m.get(
            f"{base_url}/sc2/profile/1/1/{profile_id}/ladder/307173",
            json=fake_ladder_info_response_2,
        )
        stats = BlizzardResolver(base_url).resolve_player_stats(
            Player(id=111, region_id=1, profile_id=profile_id)
        )
    assert len(stats) == 2
    stats.sort(key=lambda l: l.mmr)
    s = stats[0]
    expected = 111, Race.PROTOSS, League.MASTER, 3038, 0, 1, "LRCUB"
    assert (s.player_id, s.race, s.league, s.mmr, s.wins, s.losses, s.clan_tag) == expected
    s = stats[1]
    expected = 111, Race.ZERG, League.DIAMOND, 3422, 10, 8, "LRCUB"
    assert (s.player_id, s.race, s.league, s.mmr, s.wins, s.losses, s.clan_tag) == expected


def test_player_display_name(fake_metadata_response):
    base_url = "http://api.com"
    profile_id = 10993388
    with requests_mock.Mocker() as m:
        m.get(f"{base_url}/sc2/metadata/profile/1/1/{profile_id}", json=fake_metadata_response)
        display_name = BlizzardResolver(base_url).resolve_player_display_name(
            Player(id=111, region_id=1, profile_id=profile_id)
        )
    assert display_name == "FarSeer"


def test_obtain_token(monkeypatch):
    pass
