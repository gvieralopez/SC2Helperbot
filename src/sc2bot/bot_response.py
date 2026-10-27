from dataclasses import dataclass

from jinja2 import Environment, PackageLoader, select_autoescape

_environment = Environment(loader=PackageLoader("sc2bot"), autoescape=select_autoescape())


@dataclass
class BotResponse:
    text: str
    image: bytes | None = None


def text(template_name: str, **kwargs: object) -> str:
    return _environment.get_template(f"{template_name}.txt").render(kwargs)


def render(template_name: str, **kwargs: object) -> BotResponse:
    return BotResponse(text(template_name, **kwargs))
