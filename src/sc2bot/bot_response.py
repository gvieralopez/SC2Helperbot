from dataclasses import dataclass, field

from jinja2 import Environment, PackageLoader, select_autoescape

from sc2bot.database.schema import User

_environment = Environment(loader=PackageLoader("sc2bot"), autoescape=select_autoescape())


def mention(user: User) -> str:
    """@username, or the Telegram link stored for users without one."""
    name = user.telegram_username
    if not name:
        return f'<a href="tg://user?id={user.telegram_id}">{user.telegram_id}</a>'
    return name if name.startswith("<a ") else f"@{name}"


_environment.filters["mention"] = mention


@dataclass
class Button:
    label: str
    data: str  # what to show when tapped, read back by the controller
    selected: bool = False  # the current choice of its row


@dataclass
class BotResponse:
    text: str
    image: bytes | None = None
    buttons: list[list[Button]] = field(default_factory=list)  # rows of buttons


def text(template_name: str, **kwargs: object) -> str:
    return _environment.get_template(f"{template_name}.txt").render(kwargs)


def render(template_name: str, **kwargs: object) -> BotResponse:
    return BotResponse(text(template_name, **kwargs))


def split_text(text: str, limit: int) -> list[str]:
    """Cut a message into parts of at most `limit` UTF-16 units (how Telegram counts).

    Cuts only between lines: every template line closes the tags it opens, so each part is
    valid HTML. The limit is checked on the HTML, which is longer than what Telegram counts.
    A single line over the limit stays whole (no template makes one).
    """
    parts: list[str] = []
    for line in text.split("\n"):
        joined = f"{parts[-1]}\n{line}" if parts else line
        if parts and _length(joined) <= limit:
            parts[-1] = joined
        else:
            parts.append(line)
    return [part for part in (p.strip("\n") for p in parts) if part]


def _length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2
