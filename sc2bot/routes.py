from dataclasses import dataclass
from typing import Callable

from sc2bot.bot_response import BotResponse
from sc2bot.controller import set_battle_tag
from sc2bot.commands import register


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]


commands = [
    Route(register, set_battle_tag),
]
