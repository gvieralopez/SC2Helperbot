from sys import argv

from sc2bot.client.sc2_ladder import get_battle_tag_info
from sc2bot.database.schema import User


def main(battle_tag: str):
    print(get_battle_tag_info(User(battle_tag=battle_tag)))


if __name__ == "__main__":
    main(argv[1])
