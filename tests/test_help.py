import pytest

from sc2bot.commands import Category, command_names
from sc2bot.controller import help
from sc2bot.routes import routes, routes_by_category


def test_every_command_has_a_route():
    assert set(routes) == set(command_names.values())


@pytest.mark.parametrize("name", sorted(command_names.values()))
def test_every_route_has_help_and_description(name):
    route = routes[name]
    assert route.description.strip()
    assert route.help.text.strip()
    assert f"/help {name}" in route.error.text


def test_routes_by_category():
    assert set(routes_by_category[Category.CONFIG]) == {"register", "link"}
    assert "rank" in routes_by_category[Category.GENERAL]


def test_general_help_lists_every_command():
    text = help().text
    for name in command_names.values():
        assert f"/{name}" in text


def test_help_of_one_command():
    assert help("rank").text == routes["rank"].help.text


def test_help_of_unknown_command():
    assert "not found" in help("nope").text
