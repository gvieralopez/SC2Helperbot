import pytest

from sc2bot import icons
from sc2bot.database.data import League


@pytest.mark.parametrize("league", [league for league in League if league != League.GRAND_MASTER])
def test_league_badges_show_the_tier(league: League) -> None:
    badge = icons.league_badge(league, 2)
    assert badge.shapes and badge.label is not None and badge.label.text == "2"
    assert icons.league_badge(league, None).label is None


def test_grandmaster_has_no_tier() -> None:
    assert icons.league_badge(League.GRAND_MASTER, 1).label is None


@pytest.mark.parametrize("region_id", [1, 2, 3, 4, 5])
def test_every_region_has_a_flag(region_id: int) -> None:
    assert icons.flag(region_id).shapes


def test_random_is_a_question_mark() -> None:
    label = icons.random_race().label
    assert label is not None and label.text == "?"
