import pytest

from sc2bot.commands import Category, command_names
from sc2bot.routes import help_command, routes, routes_by_category


def test_every_command_has_a_route() -> None:
    assert set(routes) == set(command_names.values())


@pytest.mark.parametrize("name", sorted(command_names.values()))
def test_every_route_has_help_and_description(name: str) -> None:
    route = routes[name]
    assert route.description.strip()
    assert route.help.text.strip()
    assert f"/help_{name}" in route.error.text


def test_routes_by_category() -> None:
    assert set(routes_by_category[Category.YOU]) == {"register", "user", "profile", "fetch"}
    assert "rank" in routes_by_category[Category.EVERYONE]


def test_general_help_lists_every_command() -> None:
    text = help_command().text
    for name in command_names.values():
        assert f"/{name}" in text


def test_help_of_one_command() -> None:
    assert help_command("rank").text == routes["rank"].help.text


def test_help_of_unknown_command() -> None:
    assert "no /nope command" in help_command("nope").text
