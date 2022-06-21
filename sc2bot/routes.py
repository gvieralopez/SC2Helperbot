from dataclasses import dataclass
from typing import Callable

from sc2bot.bot_response import BotResponse, render
from sc2bot.controller import add_new_player_stats, set_battle_tag, add_player, retrieve_user, help
from sc2bot.commands import Category, command_names


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]
    help: BotResponse
    description: str
    category: Category


_routes = [
    Route(command_names["help"], help, render("def"), "...", Category.CONFIG),
    Route(command_names["register"], set_battle_tag, render("def"), "...", Category.CONFIG),
    Route(command_names["link"], add_player, render("def"), "...", Category.CONFIG),
    Route(command_names["user"], retrieve_user, render("def"), "...", Category.GENERAL),
    Route(command_names["fetch"], add_new_player_stats, render("def"), "...", Category.GENERAL),
]


def group_by_categories(routes: dict) -> dict:
    categories: dict = {c: {} for c in Category}
    for name, route in routes.items():
        categories[route.category][name] = route
    return categories


routes = {route.name: route for route in _routes}

routes_by_category = group_by_categories(routes)
