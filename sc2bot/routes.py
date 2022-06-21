from dataclasses import dataclass
from typing import Callable

from sc2bot.bot_response import BotResponse, render, text
from sc2bot.controller import add_new_player_stats, set_battle_tag, add_player, retrieve_user, help
from sc2bot.commands import Category
from sc2bot.commands import command_names as cn


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]
    help: BotResponse
    description: str
    category: Category


_routes = [
    Route(cn["help"], help, render("def"), text("dsc_help"), Category.GENERAL),
    Route(cn["register"], set_battle_tag, render("def"), text("dsc_register"), Category.CONFIG),
    Route(cn["link"], add_player, render("def"), text("dsc_link"), Category.CONFIG),
    Route(cn["user"], retrieve_user, render("def"), text("dsc_user"), Category.GENERAL),
    Route(
        cn["fetch"],
        add_new_player_stats,
        render("def"),
        text("dsc_fetch"),
        Category.GENERAL,
    ),
]


def group_by_categories(routes: dict) -> dict:
    categories: dict = {c: {} for c in Category}
    for name, route in routes.items():
        categories[route.category][name] = route
    return categories


routes = {route.name: route for route in _routes}

routes_by_category = group_by_categories(routes)
