import requests

from sc2bot.database.schema import Player, User


def get_battle_tag_info(user: User) -> list[Player]:
    player_infos = make_get_request(user.battle_tag)
    return [
        Player(
            region_id=player_info["region"],
            profile_id=player_info["profile_id"],
            display_name=player_info["username"],
        )
        for player_info in player_infos
    ]


def make_get_request(battle_tag: str) -> list[dict]:
    response = requests.get(f"{BASE_URL}/api/player?query={battle_tag}")
    if response.status_code == 200:
        return response.json()
    raise ValueError(f"SC2 Ladder API Response status not ok: {response}({response.content})")


BASE_URL = "http://www.sc2ladder.com"
