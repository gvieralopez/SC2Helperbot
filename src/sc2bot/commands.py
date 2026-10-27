from enum import Enum

command_names = {
    "help": "help",
    "register": "register",
    "user": "user",
    "fetch": "fetch",
    "users": "users",
    "rank": "rank",
    "ladders": "ladders",
    "profile": "profile",
}


class Category(Enum):
    YOU = 1
    EVERYONE = 2


categories_dict = {Category.YOU: "You", Category.EVERYONE: "Everyone"}
