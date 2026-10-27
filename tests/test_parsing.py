import pytest

from sc2bot.parsing import extract_command


@pytest.mark.parametrize(
    "text, expected",
    [
        ("/user", ["user"]),
        ("/register Foo#1234", ["register", "Foo#1234"]),
        ("/help  fetch", ["help", "fetch"]),
        ("/help_fetch", ["help", "fetch"]),
        ("/Rank", ["rank"]),
        ("/rank@SC2Helperbot", ["rank"]),
        ("/help@sc2helperbot fetch", ["help", "fetch"]),
        ("/rank@OtherBot", []),
        ("/", []),
    ],
)
def test_extract_command(text: str, expected: list[str]) -> None:
    assert extract_command(text, "SC2Helperbot") == expected


def test_extract_command_without_bot_username() -> None:
    assert extract_command("/rank@AnyBot") == ["rank"]
