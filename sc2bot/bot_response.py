from dataclasses import dataclass

from jinja2 import select_autoescape, PackageLoader, Environment

_environment = Environment(loader=PackageLoader("path"), autoescape=select_autoescape())


@dataclass
class BotResponse:
    text: str
    image: bytes | None = None


def render(template_name: str, **kwargs) -> BotResponse:
    return BotResponse(_environment.get_template(f"{template_name}.txt").render(kwargs))
