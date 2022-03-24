from sys import argv

from sc2bot.client.blizzard import resolvers
from sc2bot.database.schema import Player


def main(region_id: int, profile_id: int, resolver_index: int):
    resolver = resolvers[resolver_index]
    player = Player(region_id=region_id, profile_id=profile_id, display_name="")
    print(resolver.resolve_player_display_name(player), resolver.resolve_player_stats(player))


if __name__ == "__main__":
    main(int(argv[1]), int(argv[2]), int(argv[3]))
