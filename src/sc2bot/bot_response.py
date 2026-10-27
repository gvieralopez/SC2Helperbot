from dataclasses import dataclass

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
class BotResponse:
    text: str
    image: bytes | None = None


def text(template_name: str, **kwargs: object) -> str:
    return _environment.get_template(f"{template_name}.txt").render(kwargs)


def render(template_name: str, **kwargs: object) -> BotResponse:
    return BotResponse(text(template_name, **kwargs))
