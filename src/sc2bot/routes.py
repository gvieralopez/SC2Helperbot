from dataclasses import dataclass
from dataclasses import field
from typing import Callable

from sc2bot.bot_response import BotResponse
from sc2bot.bot_response import render
from sc2bot.bot_response import text
from sc2bot.commands import Category
from sc2bot.commands import command_names as cn
from sc2bot.controller import add_new_player_stats
from sc2bot.controller import add_player
from sc2bot.controller import help
from sc2bot.controller import ladders
from sc2bot.controller import list_users
from sc2bot.controller import profile
from sc2bot.controller import rank
from sc2bot.controller import retrieve_user
from sc2bot.controller import set_battle_tag


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]
    category: Category
    help: BotResponse = field(init=False)
    description: str = field(init=False)
    error: BotResponse = field(init=False)

    def __post_init__(self):
        self.help = render(f"hlp_{self.name}")
        self.description = text(f"dsc_{self.name}")
        self.error = render("invalid_params", command=self.name)


_routes = [
    Route(cn["help"], help, Category.GENERAL),
    Route(cn["register"], set_battle_tag, Category.CONFIG),
    Route(cn["link"], add_player, Category.CONFIG),
    Route(cn["user"], retrieve_user, Category.GENERAL),
    Route(cn["fetch"], add_new_player_stats, Category.GENERAL),
    Route(cn["users"], list_users, Category.GENERAL),
    Route(cn["rank"], rank, Category.GENERAL),
    Route(cn["ladders"], ladders, Category.GENERAL),
    Route(cn["profile"], profile, Category.GENERAL),
]


def group_by_categories(routes: dict) -> dict:
    categories: dict = {c: {} for c in Category}
    for name, route in routes.items():
        categories[route.category][name] = route
    return categories


routes = {route.name: route for route in _routes}

routes_by_category = group_by_categories(routes)
