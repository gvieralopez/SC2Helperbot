from enum import Enum


class Race(Enum):
    PROTOSS = 0
    ZERG = 1
    TERRAN = 2
    RANDOM = 3


class League(Enum):
    BRONZE = 0
    SILVER = 1
    GOLD = 2
    PLATINUM = 3
    DIAMOND = 4
    MASTER = 5
    GRAND_MASTER = 6


def get_enum_value(enum_type, entry_name: str) -> Race | None:
    if hasattr(enum_type, entry_name):
        return enum_type[entry_name]
    return None
