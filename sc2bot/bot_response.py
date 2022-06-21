from dataclasses import dataclass

from jinja2 import select_autoescape, PackageLoader, Environment

_environment = Environment(loader=PackageLoader("sc2bot"), autoescape=select_autoescape())


@dataclass
class BotResponse:
    text: str
    image: bytes | None = None


def text(template_name: str, **kwargs) -> str:
    return _environment.get_template(f"{template_name}.txt").render(kwargs)


def render(template_name: str, **kwargs) -> BotResponse:
    return BotResponse(text(template_name, **kwargs))
