"""Icons drawn in a 0-1 box. Zerg, Protoss and Terran use Blizzard's emblems instead
(emblems/NOTICE.md)."""

import math
from dataclasses import dataclass
from typing import Any

from matplotlib.patches import Circle, Patch, Polygon, Rectangle, RegularPolygon, Wedge

from sc2bot.database.data import League


@dataclass(frozen=True, slots=True)
class Label:
    text: str
    color: str
    y: float
    scale: float  # of the header's icon font size


@dataclass(frozen=True, slots=True)
class Icon:
    shapes: list[Patch]
    label: Label | None


def _star(cx: float, cy: float, radius: float, inner: float, **style: Any) -> Polygon:
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * inner
        angle = math.pi / 2 + i * math.pi / 5
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return Polygon(points, **style)


# Flags are 3:2, in the middle of the box.

FLAG_BOTTOM, FLAG_HEIGHT = 0.17, 0.66


def _field(color: str) -> Rectangle:
    return Rectangle((0, FLAG_BOTTOM), 1, FLAG_HEIGHT, fc=color, ec="none")


def _border() -> Rectangle:
    return Rectangle((0, FLAG_BOTTOM), 1, FLAG_HEIGHT, fc="none", ec="#999999", lw=0.6)


def _flag_us() -> list[Patch]:
    stripe = FLAG_HEIGHT / 7
    stripes = [
        Rectangle(
            (0, FLAG_BOTTOM + i * stripe),
            1,
            stripe,
            ec="none",
            fc="#B22234" if i % 2 == 0 else "white",
        )
        for i in range(7)
    ]
    canton = Rectangle((0, FLAG_BOTTOM + 3 * stripe), 0.42, 4 * stripe, fc="#3C3B6E", ec="none")
    return [*stripes, canton, _border()]


def _flag_eu() -> list[Patch]:
    stars = [
        Circle(
            (0.5 + 0.2 * math.cos(i * math.pi / 6), 0.5 + 0.2 * math.sin(i * math.pi / 6)),
            0.035,
            fc="#FFCC00",
        )
        for i in range(12)
    ]
    return [_field("#003399"), *stars]


def _flag_kr() -> list[Patch]:
    bars = [
        Rectangle((x, y), 0.12, 0.06, angle=angle, fc="black", ec="none")
        for x, y, angle in (
            (0.14, 0.66, -33),
            (0.76, 0.70, 33),
            (0.14, 0.30, 33),
            (0.76, 0.28, -33),
        )
    ]
    return [
        _field("white"),
        Wedge((0.5, 0.5), 0.18, 0, 180, fc="#CD2E3A", ec="none"),
        Wedge((0.5, 0.5), 0.18, 180, 360, fc="#0047A0", ec="none"),
        *bars,
        _border(),
    ]


def _flag_tw() -> list[Patch]:
    return [
        _field("#FE0000"),
        Rectangle((0, 0.5), 0.5, 0.33, fc="#000095", ec="none"),
        Circle((0.25, 0.665), 0.09, fc="white", ec="none"),
    ]


def _flag_cn() -> list[Patch]:
    small = [
        _star(x, y, 0.045, 0.4, fc="#FFDE00", ec="none")
        for x, y in ((0.36, 0.76), (0.42, 0.68), (0.42, 0.57), (0.36, 0.49))
    ]
    return [_field("#DE2910"), _star(0.18, 0.64, 0.12, 0.4, fc="#FFDE00", ec="none"), *small]


FLAGS = {1: _flag_us, 2: _flag_eu, 3: _flag_kr, 4: _flag_tw, 5: _flag_cn}


def flag(region_id: int) -> Icon:
    return Icon(FLAGS[region_id](), None)


def _tier(tier: int | None, color: str, y: float, scale: float) -> Label | None:
    return None if tier is None else Label(str(tier), color, y, scale)


def _medal(fill: str, rim: str, tier: int | None) -> Icon:
    return Icon([Circle((0.5, 0.5), 0.45, fc=fill, ec=rim, lw=2)], _tier(tier, rim, 0.47, 1.0))


def _platinum(tier: int | None) -> Icon:
    hexagon = RegularPolygon((0.5, 0.5), 6, radius=0.48, fc="#8FD0D8", ec="#3E8E99", lw=2)
    return Icon([hexagon], _tier(tier, "#245F67", 0.47, 1.0))


def _diamond(tier: int | None) -> Icon:
    gem = Polygon(
        [(0.08, 0.64), (0.26, 0.90), (0.74, 0.90), (0.92, 0.64), (0.5, 0.04)],
        fc="#5AA6F0",
        ec="#1D5FAF",
        lw=1.6,
    )
    table = Polygon(
        [(0.26, 0.90), (0.74, 0.90), (0.62, 0.64), (0.38, 0.64)], fc="#8CC4F7", ec="none"
    )
    # The wide upper part is the only room for the number.
    return Icon([gem, table], _tier(tier, "#123F7A", 0.63, 0.8))


def _master(tier: int | None) -> Icon:
    return Icon(
        [_star(0.5, 0.48, 0.5, 0.5, fc="#9A6BE0", ec="#5B2E9E", lw=1.6)],
        _tier(tier, "white", 0.47, 1.0),
    )


def _grandmaster() -> Icon:
    # Grandmaster has no tiers.
    crown = [
        (0.06, 0.18),
        (0.06, 0.78),
        (0.3, 0.52),
        (0.5, 0.92),
        (0.7, 0.52),
        (0.94, 0.78),
        (0.94, 0.18),
    ]
    band = Rectangle((0.06, 0.08), 0.88, 0.12, fc="#A8323A", ec="none")
    return Icon([Polygon(crown, fc="#E8B923", ec="#A8323A", lw=2), band], None)


def league_badge(league: League, tier: int | None) -> Icon:
    badges = {
        League.BRONZE: lambda: _medal("#CD7F32", "#7A4518", tier),
        League.SILVER: lambda: _medal("#D3D6DA", "#6E737A", tier),
        League.GOLD: lambda: _medal("#F2C230", "#8F6A0C", tier),
        League.PLATINUM: lambda: _platinum(tier),
        League.DIAMOND: lambda: _diamond(tier),
        League.MASTER: lambda: _master(tier),
        League.GRAND_MASTER: _grandmaster,
    }
    return badges[league]()


def random_race() -> Icon:
    # Blizzard has no Random emblem.
    return Icon([Circle((0.5, 0.5), 0.46, fc="#6B7280", ec="none")], Label("?", "white", 0.47, 1.0))
