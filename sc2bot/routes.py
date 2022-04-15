from dataclasses import dataclass
from typing import Callable

from sc2bot.bot_response import BotResponse, render
from sc2bot.controller import add_new_player_stats, set_battle_tag, add_player, retrieve_user
from sc2bot.commands import register, link, user, fetch


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]
    help: BotResponse


_routes = [
    Route(register, set_battle_tag, render("help")),
    Route(link, add_player, render("help")),
    Route(user, retrieve_user, render("help")),
    Route(fetch, add_new_player_stats, render("help")),
]

routes = {route.name: route for route in _routes}
