from enum import Enum
from dataclasses import dataclass
from typing import Callable

from sc2bot.bot_response import BotResponse, render
from sc2bot.controller import add_new_player_stats, set_battle_tag, add_player, retrieve_user
from sc2bot.commands import command_names


class Category(Enum):
    CONFIG = 1
    GENERAL = 2


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]
    help: BotResponse
    category: Category


_routes = [
    Route(command_names["register"], set_battle_tag, render("help"), Category.CONFIG),
    Route(command_names["link"], add_player, render("help"), Category.CONFIG),
    Route(command_names["user"], retrieve_user, render("help"), Category.GENERAL),
    Route(command_names["fetch"], add_new_player_stats, render("help"), Category.GENERAL),
]

routes = {route.name: route for route in _routes}
