from sys import argv

from sc2bot.client import resolvers
from sc2bot.database.schema import Player


def main(region_id: int, profile_id: int, resolver_index: int):
    resolver = resolvers[resolver_index]
    name = resolver.resolve_player_display_name(region_id=region_id, profile_id=profile_id)
    player = Player(region_id=region_id, profile_id=profile_id, display_name=name)
    print(name, resolver.resolve_player_stats(player))


if __name__ == "__main__":
    main(int(argv[1]), int(argv[2]), int(argv[3]))
