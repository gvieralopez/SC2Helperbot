import logging

from sc2bot.client.blizzard import Resolver, BlizzardAuthorizedResolver, BlizzardResolver
from sc2bot.client.config import BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET
from sc2bot.client.sc2_ladder import get_battle_tag_info as _get_battle_tag_info
from sc2bot.database.schema import PlayerStat, User, Player


logger = logging.getLogger(__name__)


def resolve_player_display_name(region_id: int, profile_id: int) -> str:
    for resolver in resolvers:
        try:
            return resolver.resolve_player_display_name(region_id, profile_id)
        except Exception as e:
            logger.warning(
                f"The resolver {resolver.base_url} couldn't retrieve the player display name: {e}"
            )
    return ""


def resolve_player_stats(player: Player) -> list[PlayerStat]:
    for resolver in resolvers:
        try:
            return resolver.resolve_player_stats(player)
        except Exception as e:
            logger.warning(
                f"The resolver {resolver.base_url} couldn't retrieve the player stats: {e}"
            )
    return []


def get_battle_tag_info(user: User) -> list[Player]:
    return _get_battle_tag_info(user)


resolvers: list[BlizzardResolver] = [
    BlizzardAuthorizedResolver(
        "https://us.api.blizzard.com",
        "https://us.battle.net",
        BLIZZARD_CLIENT_ID,
        BLIZZARD_CLIENT_SECRET,
    ),
    BlizzardAuthorizedResolver(
        "https://eu.api.blizzard.com",
        "https://us.battle.net",
        BLIZZARD_CLIENT_ID,
        BLIZZARD_CLIENT_SECRET,
    ),
    BlizzardResolver("https://starcraft2.com/en-us/api"),
]
