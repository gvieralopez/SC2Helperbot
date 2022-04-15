import pytest
import requests_mock

from sc2bot.controller import add_new_player_stats
from sc2bot.database import session
from sc2bot.database.data import League, Race
from sc2bot.database.schema import Player


@pytest.fixture()
def player_1(user) -> Player:
    player = Player(user_id=user.id, region_id=1, profile_id=10993388, display_name="baz")
    session.db_session.add(player)
    session.db_session.commit()
    return player


@pytest.fixture()
def player_2(user) -> Player:
    player = Player(user_id=user.id, region_id=1, profile_id=10993388, display_name="quz")
    session.db_session.add(player)
    session.db_session.commit()
    return player


def test_add_player_wrong_user(db):
    response = add_new_player_stats(telegram_id=1)
    assert "register" in response.text


def test_add_player_stats_no_player(user):
    response = add_new_player_stats(telegram_id=1)
    assert user.battle_tag in response.text
    assert user.telegram_username and user.telegram_username in response.text


def test_add_player_stats(
    player_1: Player,
    player_2: Player,
    fake_ladder_summary_response,
    fake_ladder_info_response_1,
    fake_ladder_info_response_2,
):
    with requests_mock.Mocker() as m:
        m.get(
            f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{player_1.profile_id}/ladder/summary",
            json=fake_ladder_summary_response,
        )
        m.get(
            f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{player_2.profile_id}/ladder/summary",
            json=fake_ladder_summary_response,
        )
        m.get(
            f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{player_1.profile_id}/ladder/307413",
            json=fake_ladder_info_response_1,
        ),
        m.get(
            f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{player_2.profile_id}/ladder/307413",
            json=fake_ladder_info_response_1,
        ),
        m.get(
            f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{player_1.profile_id}/ladder/307173",
            json=fake_ladder_info_response_2,
        )
        m.get(
            f"https://starcraft2.com/en-us/api/sc2/profile/1/1/{player_2.profile_id}/ladder/307173",
            json=fake_ladder_info_response_2,
        )
        response = add_new_player_stats(telegram_id=1)
    assert str(player_1.profile_id) in response.text
    assert str(player_2.profile_id) in response.text
    assert len(player_1.stats) == 2  # type: ignore
    assert len(player_2.stats) == 2  # type: ignore
    expected_s1 = Race.PROTOSS, League.MASTER, 3038, 0, 1, "LRCUB"
    expected_s2 = Race.ZERG, League.DIAMOND, 3422, 10, 8, "LRCUB"
    s1p1 = player_1.stats[0]  # type: ignore
    s2p1 = player_1.stats[1]  # type: ignore
    s1p2 = player_2.stats[0]  # type: ignore
    s2p2 = player_2.stats[1]  # type: ignore
    assert (s1p1.race, s1p1.league, s1p1.mmr, s1p1.wins, s1p1.losses, s1p1.clan_tag) == expected_s1
    assert (s2p1.race, s2p1.league, s2p1.mmr, s2p1.wins, s2p1.losses, s2p1.clan_tag) == expected_s2
    assert (s1p2.race, s1p2.league, s1p2.mmr, s1p2.wins, s1p2.losses, s1p2.clan_tag) == expected_s1
    assert (s2p2.race, s2p2.league, s2p2.mmr, s2p2.wins, s2p2.losses, s2p2.clan_tag) == expected_s2
