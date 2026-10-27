from sc2bot.controller import ladders as ladders_command
from sc2bot.database.schema import User


def test_ladders_empty(db: None) -> None:
    assert "No ladders" in ladders_command(telegram_id=1).text


def test_ladders_lists_every_current_ladder(ladders: tuple[User, User]) -> None:
    text = ladders_command(telegram_id=1).text
    assert text.index("3500") < text.index("3100") < text.index("2500")
    assert "#3" in text and "3000" not in text
