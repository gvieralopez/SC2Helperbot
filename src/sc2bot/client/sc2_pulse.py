"""StarCraft II profiles and ladders from SC2 Pulse (https://sc2pulse.nephest.com/sc2).

Its API is free for non-commercial use with credit. Ids (leagues 0-6 from bronze, races 1-4)
are documented in its API docs.
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import requests

from sc2bot.database.data import League, Race
from sc2bot.database.schema import Player, PlayerStat, User

logger = logging.getLogger(__name__)

API = "https://sc2pulse.nephest.com/sc2/api"
HEADERS = {"User-Agent": "SC2Helperbot (github.com/gvieralopez/SC2Helperbot)"}
REGION_IDS = {"US": 1, "EU": 2, "KR": 3, "CN": 5}
# Players only store region and profile id, so every profile is taken to be on realm 1.
REALM = 1
TOONS_PER_CALL = 500  # the API's maximum

# The last part of a team legacy uid ("201-0-2-1.8972769.3") is the race.
RACES = {"1": Race.TERRAN, "2": Race.PROTOSS, "3": Race.ZERG, "4": Race.RANDOM}
LEAGUES = {league.value: league for league in League}


def get_battle_tag_info(user: User) -> list[Player]:
    try:
        characters = search_characters(user.battle_tag)
    except requests.RequestException as e:
        logger.warning("SC2 Pulse search failed: %s", e)
        return []
    players = []
    for character in characters:
        if character["realm"] != REALM:
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
    return [result["members"]["character"] for result in _get("characters", query=battle_tag)]


def current_ladders(players: list[Player]) -> list[PlayerStat]:
    """The 1v1 ladders of the players in the current season of their region, one per race."""
    if not players:
        return []
    seasons = current_seasons()
    handles_by_season = defaultdict(list)
    players_by_key = {(player.region_id, player.profile_id): player for player in players}
    for player in players:
        if player.region_id in seasons:
            handles_by_season[seasons[player.region_id]].append(toon_handle(player))

    stats = []
    for season, handles in handles_by_season.items():
        for start in range(0, len(handles), TOONS_PER_CALL):
            chunk = handles[start : start + TOONS_PER_CALL]
            teams = _get("character-teams", toonHandle=chunk, queue="LOTV_1V1", season=season)
            for team in teams:
                character = team["members"][0]["character"]
                player = players_by_key[(REGION_IDS[character["region"]], character["battlenetId"])]
                stats.append(_stat(player, team))
    return stats


def current_seasons() -> dict[int, int]:
    """The current season of each region, by region id."""
    seasons: dict[int, int] = {}
    for season in _get("seasons"):
        region_id = REGION_IDS[season["region"]]
        seasons[region_id] = max(seasons.get(region_id, 0), season["battlenetId"])
    return seasons


def tier(tier_type: int | str) -> int:
    """The league tier, 1 (top) to 3, from SC2 Pulse's tier type (0 is the top tier)."""
    return int(tier_type) + 1


def toon_handle(player: Player) -> str:
    return f"{player.region_id}-S2-{REALM}-{player.profile_id}"


def _stat(player: Player, team: dict[str, Any]) -> PlayerStat:
    clan = team["members"][0].get("clan") or {}
    # Naive UTC, like the CURRENT_TIMESTAMP default of the bot's own stats.
    last_played = datetime.fromisoformat(team["lastPlayed"]).astimezone(UTC).replace(tzinfo=None)
    return PlayerStat(
        player_id=player.id,
        race=RACES[team["legacyUid"].rsplit(".", 1)[1]],
        league=LEAGUES[team["league"]["type"]],
        tier=tier(team["tierType"]),
        mmr=team["rating"],
        wins=team["wins"],
        losses=team["losses"],
        clan_tag=clan.get("tag"),
        created_at=last_played,
    )


def _get(endpoint: str, **params: str | int | list[str]) -> list[Any]:
    response = requests.get(f"{API}/{endpoint}", params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data: list[Any] = response.json()
    return data
