from datetime import datetime, timedelta
from typing import Any

import pytest

from sc2bot import controller
from sc2bot.bot_response import Button
from sc2bot.controller import profile, profile_button
from sc2bot.database import session
from sc2bot.database.data import Race
from sc2bot.database.schema import User


@pytest.fixture()
def charts(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """What the profile asks the chart to draw, one entry per chart."""
    drawn: list[dict[str, Any]] = []

    def plot_ladder(*args: Any) -> bytes:
        stats, race, region_id, name, window = args
        drawn.append({"mmrs": [s.mmr for s in stats], "race": race, "region_id": region_id})
        drawn[-1].update(name=name, window=window)
        return b"\x89PNG"

    monkeypatch.setattr(controller, "plot_ladder", plot_ladder)
    return drawn


def _labels(rows: list[list[Button]]) -> list[list[str]]:
    """Labels, the selected ones starting with "*"."""
    return [[("*" if b.selected else "") + b.label for b in row] for row in rows]


def test_profile_user_not_found(db: None) -> None:
    response = profile(telegram_id=1)
    assert "register" in response.text
    assert response.image is None


def test_profile_without_ladders(user: User) -> None:
    response = profile(telegram_id=1)
    assert "No ladders" in response.text
    assert response.image is None and response.buttons == []


def test_profile_shows_the_last_played_ladder(
    ladders: tuple[User, User], charts: list[dict[str, Any]]
) -> None:
    foo, _ = ladders
    us_terran = next(stat for player in foo.players for stat in player.stats if stat.mmr == 2500)
    us_terran.created_at = datetime(2030, 1, 1)
    session.db_session.commit()

    response = profile(telegram_id=1)

    assert response.text == "" and response.image == b"\x89PNG"
    [chart] = charts
    assert chart == {
        "mmrs": [2500],
        "race": Race.TERRAN,
        "region_id": 1,
        "name": "bar",
        "window": timedelta(days=182),
    }
    assert _labels(response.buttons) == [
        ["*🇺🇸 US", "🇪🇺 EU"],
        ["🪲", "✨", "*🧍‍♂️", "❓"],
        ["*6 months", "1 year", "All"],
    ]


def test_a_button_changes_only_its_row(
    ladders: tuple[User, User], charts: list[dict[str, Any]]
) -> None:
    foo, _ = ladders
    response = profile_button(f"profile:{foo.id}:2:{Race.ZERG.value}:1y")
    assert response is not None
    assert charts[0]["mmrs"] == [3000, 3100] and charts[0]["window"] == timedelta(days=365)
    us, eu = response.buttons[0]
    zerg = response.buttons[1][0]
    every = response.buttons[2][2]
    assert us.data == f"profile:{foo.id}:1:{Race.ZERG.value}:1y"
    assert zerg.selected and eu.selected and not us.selected
    assert every.data == f"profile:{foo.id}:2:{Race.ZERG.value}:all"


def test_a_ladder_without_games(ladders: tuple[User, User], charts: list[dict[str, Any]]) -> None:
    foo, _ = ladders
    response = profile_button(f"profile:{foo.id}:1:{Race.RANDOM.value}:6m")
    assert response is not None and response.image is not None
    assert charts[0]["mmrs"] == [] and charts[0]["race"] == Race.RANDOM


def test_a_stale_button_shows_nothing(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    assert profile_button(f"profile:999:1:{Race.ZERG.value}:6m") is None
    assert profile_button(f"profile:{foo.id}:1:{Race.ZERG.value}:2w") is None
