from collections.abc import Callable
from dataclasses import dataclass, field

from sc2bot.bot_response import BotResponse, render, text
from sc2bot.commands import Category, categories_dict
from sc2bot.commands import command_names as cn
from sc2bot.controller import (
    add_new_player_stats,
    ladders,
    list_users,
    ping_outside_a_group,
    profile,
    rank,
    retrieve_user,
    set_battle_tag,
)


@dataclass
class Route:
    name: str
    target: Callable[..., BotResponse]
    category: Category
    help: BotResponse = field(init=False)
    description: str = field(init=False)
    error: BotResponse = field(init=False)

    def __post_init__(self) -> None:
        self.help = render(f"hlp_{self.name}")
        self.description = text(f"dsc_{self.name}")
        self.error = render("invalid_params", command=self.name)


def help_command(command: str | None = None, **_kwargs: object) -> BotResponse:
    if command is None:
        return render("help", categories=routes_by_category, categories_dict=categories_dict)
    if command in cn.values():
        return render(f"hlp_{command}")
    return render("command_not_found", command=command)


_routes = [
    Route(cn["register"], set_battle_tag, Category.YOU),
    Route(cn["user"], retrieve_user, Category.YOU),
    Route(cn["profile"], profile, Category.YOU),
    Route(cn["fetch"], add_new_player_stats, Category.YOU),
    Route(cn["rank"], rank, Category.EVERYONE),
    Route(cn["ladders"], ladders, Category.EVERYONE),
    Route(cn["users"], list_users, Category.EVERYONE),
    Route(cn["ping"], ping_outside_a_group, Category.EVERYONE),
    Route(cn["help"], help_command, Category.EVERYONE),
]


def group_by_categories(routes: dict[str, Route]) -> dict[Category, dict[str, Route]]:
    categories: dict[Category, dict[str, Route]] = {c: {} for c in Category}
    for name, route in routes.items():
        categories[route.category][name] = route
    return categories


routes = {route.name: route for route in _routes}

routes_by_category = group_by_categories(routes)
