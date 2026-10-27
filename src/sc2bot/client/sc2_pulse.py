"""Find the StarCraft II profiles of a Battle Tag on SC2 Pulse (https://sc2pulse.nephest.com/sc2).

Its API is free for non-commercial use with credit.
"""

import logging
from typing import Any

import requests

from sc2bot.client.config import REALM_ID
from sc2bot.database.schema import Player, User

logger = logging.getLogger(__name__)

API = "https://sc2pulse.nephest.com/sc2/api"
HEADERS = {"User-Agent": "SC2Helperbot (github.com/gvieralopez/SC2Helperbot)"}
REGION_IDS = {"US": 1, "EU": 2, "KR": 3, "CN": 5}


def get_battle_tag_info(user: User) -> list[Player]:
    try:
        characters = search_characters(user.battle_tag)
    except requests.RequestException as e:
        logger.warning("SC2 Pulse search failed: %s", e)
        return []
    players = []
    for character in characters:
        if character["realm"] != REALM_ID:
            # The Blizzard resolvers only ask for profiles on REALM_ID.
            logger.info("Skipping %s: realm %s", character["name"], character["realm"])
            continue
        player = Player(
            user_id=user.id,
            region_id=REGION_IDS[character["region"]],
            profile_id=character["battlenetId"],
            display_name=character["name"].split("#")[0],
        )
        players.append(player)
    return players


def search_characters(battle_tag: str) -> list[dict[str, Any]]:
    """The characters of the account with this Battle Tag (case-insensitive)."""
    response = requests.get(
        f"{API}/characters", params={"query": battle_tag}, headers=HEADERS, timeout=30
    )
    response.raise_for_status()
    return [result["members"]["character"] for result in response.json()]
