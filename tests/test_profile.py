from datetime import datetime

from sc2bot.bot_response import Button
from sc2bot.controller import profile, profile_button
from sc2bot.database import session
from sc2bot.database.data import Race
from sc2bot.database.schema import User


def _labels(rows: list[list[Button]]) -> list[list[str]]:
    return [[button.label for button in row] for row in rows]


def test_profile_user_not_found(db: None) -> None:
    response = profile(telegram_id=1)
    assert "register" in response.text
    assert response.image is None


def test_profile_without_ladders(user: User) -> None:
    response = profile(telegram_id=1)
    assert "No ladders" in response.text
    assert response.image is None and response.buttons == []


def test_profile_shows_the_last_played_ladder(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    us_terran = next(stat for player in foo.players for stat in player.stats if stat.mmr == 2500)
    us_terran.created_at = datetime(2030, 1, 1)
    session.db_session.commit()

    response = profile(telegram_id=1)

    assert "bar" in response.text and "2500" in response.text and "3100" not in response.text
    assert response.image is not None and response.image.startswith(b"\x89PNG")
    assert _labels(response.buttons) == [
        ["• 🇺🇸 US", "🇪🇺 EU"],
        ["🪲", "✨", "• 🧍‍♂️", "❓"],
        ["• 6 months", "1 year", "All"],
    ]


def test_a_button_changes_only_its_row(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    response = profile_button(f"profile:{foo.id}:2:{Race.ZERG.value}:1y")
    assert response is not None
    assert "3100" in response.text  # EU zerg, the latest of its two stats
    us, eu = response.buttons[0]
    zerg = response.buttons[1][0]
    every = response.buttons[2][2]
    assert us.data == f"profile:{foo.id}:1:{Race.ZERG.value}:1y"
    assert zerg.label.startswith("• ") and eu.label.startswith("• ")
    assert every.data == f"profile:{foo.id}:2:{Race.ZERG.value}:all"


def test_a_ladder_without_games(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    response = profile_button(f"profile:{foo.id}:1:{Race.RANDOM.value}:6m")
    assert response is not None
    assert "no games" in response.text
    assert response.image is not None


def test_a_stale_button_shows_nothing(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    assert profile_button(f"profile:999:1:{Race.ZERG.value}:6m") is None
    assert profile_button(f"profile:{foo.id}:1:{Race.ZERG.value}:2w") is None
