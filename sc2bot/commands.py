from enum import Enum

command_names = {
    "help": "help",
    "register": "register",
    "link": "link",
    "user": "user",
    "fetch": "fetch",
    "users": "users",
    "rank": "rank",
    "ladders": "ladders",
    "profile": "profile",
}


class Category(Enum):
    CONFIG = 1
    GENERAL = 2


categories_dict = {
    Category.GENERAL: "General purpose",
    Category.CONFIG: "Setting up your credentials",
}
