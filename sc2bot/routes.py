from dataclasses import dataclass
from typing import Callable

from sc2bot.bot_response import BotResponse
from sc2bot.controller import set_battle_tag, add_player, retrieve_user
from sc2bot.commands import register, link, user


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]


commands = [
    Route(register, set_battle_tag),
    Route(link, add_player),
    Route(user, retrieve_user),
]
