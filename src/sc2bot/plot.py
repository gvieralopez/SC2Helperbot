import io
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("Agg")

from matplotlib import dates as mdates
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from sc2bot.database.data import Race
from sc2bot.database.schema import PlayerStat

race_colors = {
    Race.ZERG: "#7B3FA0",
    Race.PROTOSS: "#D4A017",
    Race.TERRAN: "#1F6FB5",
    Race.RANDOM: "#6B7280",
}

# Sized for a phone screen: few large labels on a small canvas.
FIGURE_SIZE = (6, 4)
DPI = 160
FONT_SIZE = 13
LINE_WIDTH = 2.5
# MMR held this long without a game is a break: drawn lighter.
BREAK = timedelta(days=14)
BREAK_ALPHA = 0.25


def plot_ladder(stats: list[PlayerStat], race: Race, title: str, window: timedelta | None) -> bytes:
    """PNG of one ladder's MMR over the `window` before its last game (None: all of it).

    Games close in time are joined by a line. Across a break (no game for longer than BREAK)
    the MMR is held, so it is drawn flat and lighter until the next game.
    """
    with matplotlib.rc_context({"font.size": FONT_SIZE}):
        figure = Figure(figsize=FIGURE_SIZE, dpi=DPI, layout="constrained")
        axes = figure.subplots()
        axes.set_title(title)
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
