import requests_mock

from sc2bot.client.sc2_ladder import get_battle_tag_info
from sc2bot.database.schema import User


def test_battle_tag_info(fake_battle_tag_response):
    battle_tag = "foo"
    with requests_mock.Mocker() as m:
        m.get(
            f"http://www.sc2ladder.com/api/player?query={battle_tag}", json=fake_battle_tag_response
        )
        players = get_battle_tag_info(User(id=111, battle_tag=battle_tag))

    assert len(players) == 1
    p = players[0]
    expected = 111, 2, 8972769, "FarSeer"
    assert (p.user_id, p.region_id, p.profile_id, p.display_name) == expected
