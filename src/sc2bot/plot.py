import io
from datetime import datetime, timedelta
from functools import cache
from importlib.resources import files

import matplotlib

matplotlib.use("Agg")

import numpy as np
from matplotlib import dates as mdates
from matplotlib import image as mpimg
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.offsetbox import (
    AnchoredOffsetbox,
    DrawingArea,
    HPacker,
    OffsetBox,
    OffsetImage,
    TextArea,
    VPacker,
)
from matplotlib.text import Text
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import Affine2D

from sc2bot import icons
from sc2bot.database.data import Race
from sc2bot.database.schema import PlayerStat

race_colors = {
    Race.ZERG: "#7B3FA0",
    Race.PROTOSS: "#D4A017",
    Race.TERRAN: "#1F6FB5",
    Race.RANDOM: "#6B7280",
}

# Sized for a phone screen: few large labels on a small canvas.
FIGURE_SIZE = (6, 4.5)
DPI = 160
FONT_SIZE = 13
LINE_WIDTH = 2.5
NAME_SIZE = 16
DETAIL_SIZE = 12
# Icon sizes in points.
FLAG_SIZE = 24
EMBLEM_SIZE = 28
BADGE_SIZE = 22
# MMR held this long without a game is a break: drawn lighter.
BREAK = timedelta(days=14)
BREAK_ALPHA = 0.25


def plot_ladder(
    stats: list[PlayerStat], race: Race, region_id: int, name: str, window: timedelta | None
) -> bytes:
    """PNG of one ladder's MMR over the `window` before its last game (None: all of it).

    Games close in time are joined by a line. Across a break (no game for longer than BREAK)
    the MMR is held, so it is drawn flat and lighter until the next game.
    """
    with matplotlib.rc_context({"font.size": FONT_SIZE}):
        figure = Figure(figsize=FIGURE_SIZE, dpi=DPI, layout="constrained")
        axes = figure.subplots()
        _header(axes, stats, race, region_id, name)
        if not stats:
            axes.set_axis_off()
            axes.text(0.5, 0.5, "No games", ha="center", va="center", color=race_colors[race])
            return _png(figure)
        times, mmrs = _daily(*ladder_series(stats, window))
        color = race_colors[race]
        played, breaks = _step_segments(times, mmrs)
        axes.add_collection(LineCollection(breaks, colors=color, alpha=BREAK_ALPHA, lw=LINE_WIDTH))
        axes.add_collection(LineCollection(played, colors=color, lw=LINE_WIDTH))
        if len(times) == 1:
            axes.plot(mdates.date2num(times), mmrs, "o", color=color)
        axes.autoscale()
        axes.set_ylabel("MMR")
        axes.grid(alpha=0.4)
        locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
        axes.xaxis.set_major_locator(locator)
        axes.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        axes.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10], integer=True))
        axes.ticklabel_format(axis="y", useOffset=False, style="plain")
        if times[-1] - times[0] < timedelta(days=1):
            # One day of data: show the day around it instead of an arbitrary range.
            axes.set_xlim(
                mdates.date2num(times[0] - timedelta(days=1)),
                mdates.date2num(times[-1] + timedelta(days=1)),
            )
        return _png(figure)


def _header(axes: Axes, stats: list[PlayerStat], race: Race, region_id: int, name: str) -> None:
    """Above the chart: the player on a server, then how they do with this race."""
    last = stats[-1] if stats else None
    clan = f"<{last.clan_tag}> " if last and last.clan_tag else ""
    player = HPacker(
        children=[
            TextArea(f"{clan}{name}", textprops={"size": NAME_SIZE, "weight": "bold"}),
            _drawn(icons.flag(region_id), FLAG_SIZE),
        ],
        align="center",
        pad=0,
        sep=6,
    )
    ladder: list[Artist] = [_emblem(race), _detail(race.name.title(), "black")]
    if last:
        games = last.wins + last.losses
        ladder += [
            _detail("·", "#888888"),
            _drawn(icons.league_badge(last.league, last.tier), BADGE_SIZE),
            TextArea(str(last.mmr), textprops={"size": DETAIL_SIZE, "weight": "bold"}),
            _detail("·", "#888888"),
            _detail(f"{100 * last.wins // games if games else 0}% of {games}", "#555555"),
        ]
    header = VPacker(
        children=[player, HPacker(children=ladder, align="center", pad=0, sep=5)],
        align="center",
        pad=0,
        sep=4,
    )
    anchored = AnchoredOffsetbox(
        loc="lower center",
        child=header,
        frameon=False,
        bbox_to_anchor=(0.5, 1.02),
        bbox_transform=axes.transAxes,
        borderpad=0,
    )
    axes.add_artist(anchored)


def _detail(text: str, color: str) -> TextArea:
    return TextArea(text, textprops={"size": DETAIL_SIZE, "color": color})


def _emblem(race: Race) -> OffsetBox:
    if race == Race.RANDOM:
        return _drawn(icons.random_race(), EMBLEM_SIZE * 0.75)
    image = _emblem_image(race)
    return OffsetImage(image, zoom=EMBLEM_SIZE / image.shape[1])


@cache
def _emblem_image(race: Race) -> np.ndarray:
    png = files("sc2bot").joinpath(f"emblems/{race.name.lower()}.png").read_bytes()
    image: np.ndarray = mpimg.imread(io.BytesIO(png))
    return image


def _drawn(icon: icons.Icon, size: float) -> DrawingArea:
    area = DrawingArea(size, size)
    to_area = Affine2D().scale(size) + area.get_transform()
    for shape in icon.shapes:
        shape.set_transform(to_area)
        area.add_artist(shape)
    if icon.label:
        label = Text(
            0.5,
            icon.label.y,
            icon.label.text,
            ha="center",
            va="center",
            color=icon.label.color,
            weight="bold",
            fontsize=size * 0.55 * icon.label.scale,
            transform=to_area,
        )
        area.add_artist(label)
    return area


def _png(figure: Figure) -> bytes:
    image = io.BytesIO()
    figure.savefig(image, format="png")
    return image.getvalue()


def ladder_series(
    stats: list[PlayerStat], window: timedelta | None
) -> tuple[list[datetime], list[int]]:
    """(times, MMRs) of a ladder in the window before its last game, sorted by date.

    A ladder played before the window starts at the MMR it had when the window opens.
    """
    stats = sorted(stats, key=lambda stat: stat.created_at)
    if window is None:
        return [s.created_at for s in stats], [s.mmr for s in stats]
    start = stats[-1].created_at - window
    inside = [stat for stat in stats if stat.created_at >= start]
    times, mmrs = [s.created_at for s in inside], [s.mmr for s in inside]
    before = [stat for stat in stats if stat.created_at < start]
    if before:
        times, mmrs = [start, *times], [before[-1].mmr, *mmrs]
    return times, mmrs


Segment = list[tuple[float, int]]


def _daily(times: list[datetime], mmrs: list[int]) -> tuple[list[datetime], list[int]]:
    """One point per day, the MMR at the end of it: a session is one move, not a burst."""
    last_of_day: dict[object, tuple[datetime, int]] = {}
    for time, mmr in zip(times, mmrs, strict=True):
        last_of_day[time.date()] = (time, mmr)
    days = list(last_of_day.values())
    return [time for time, _ in days], [mmr for _, mmr in days]


def _step_segments(times: list[datetime], mmrs: list[int]) -> tuple[list[Segment], list[Segment]]:
    """Segments split into (played, breaks): over a break the MMR is held, then the game."""
    x = mdates.date2num(times)
    played: list[Segment] = []
    breaks: list[Segment] = []
    for i in range(1, len(times)):
        if times[i] - times[i - 1] > BREAK:
            breaks.append([(x[i - 1], mmrs[i - 1]), (x[i], mmrs[i - 1])])
            played.append([(x[i], mmrs[i - 1]), (x[i], mmrs[i])])
        else:
            played.append([(x[i - 1], mmrs[i - 1]), (x[i], mmrs[i])])
    return played, breaks
