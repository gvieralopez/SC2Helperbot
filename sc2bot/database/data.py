from enum import Enum


class Race(Enum):
    PROTOSS = 0
    ZERG = 1
    TERRAN = 2
    RANDOM = 3

    @classmethod
    def from_raw(cls, raw: str) -> "Race":
        return {
            "protoss": Race.PROTOSS,
            "zerg": Race.ZERG,
            "terran": Race.TERRAN,
            "random": Race.RANDOM,
        }[raw.lower()]


class League(Enum):
    BRONZE = 0
    SILVER = 1
    GOLD = 2
    PLATINUM = 3
    DIAMOND = 4
    MASTER = 5
    GRAND_MASTER = 6

    @classmethod
    def from_raw(cls, raw: str) -> "League":
        return {
            "bronze": League.BRONZE,
            "silver": League.SILVER,
            "gold": League.GOLD,
            "platinum": League.PLATINUM,
            "diamond": League.DIAMOND,
            "master": League.MASTER,
            "grand master": League.GRAND_MASTER,
        }[raw.lower()]


def get_enum_value(enum_type, entry_name: str) -> Race | None:
    if hasattr(enum_type, entry_name):
        return enum_type[entry_name]
    return None
