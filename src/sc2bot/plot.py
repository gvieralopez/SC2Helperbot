import io
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("Agg")

from matplotlib import dates as mdates
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from sc2bot.database.data import Race
from sc2bot.database.schema import PlayerStat, User

region_names = {1: "US", 2: "EU", 3: "KR", 4: "TW"}

# Colour tells the race, line style the region, so 8 ladders stay readable.
race_colors = {
    Race.ZERG: "#7B3FA0",
    Race.PROTOSS: "#D4A017",
    Race.TERRAN: "#1F6FB5",
    Race.RANDOM: "#6B7280",
}
region_styles = {1: "--", 2: "-", 3: ":", 4: "-."}

# Sized for a phone screen: few large labels on a small canvas.
FIGURE_SIZE = (6, 4.5)
DPI = 160
FONT_SIZE = 13
LEGEND_FONT_SIZE = 11
LEGEND_COLUMNS = 3
# Few points get a marker each, so a single fetch is still visible.
MARKER_LIMIT = 15
# The chart shows the most recent months only: a whole career doesn't fit a phone screen.
WINDOW = timedelta(days=182)


def plot_mmr_history(user: User) -> bytes:
    """PNG with the recent MMR of every (region, race) the user played in those months.

    MMR only changes when a game is played, so each line is drawn as steps.
    """
    ladders = _ladders(user)
    newest = max(stat.created_at for _, _, stats in ladders for stat in stats)
    start = newest - WINDOW
    windowed = min(stat.created_at for _, _, stats in ladders for stat in stats) < start

    with matplotlib.rc_context({"font.size": FONT_SIZE}):
        figure = Figure(figsize=FIGURE_SIZE, dpi=DPI, layout="constrained")
        axes = figure.subplots()
        times = []
        for region_id, race, stats in ladders:
            series = window_series(stats, start)
            if series is None:
                continue
            x, y, recent = series
            times += x
            axes.plot(
                mdates.date2num([*x, newest]),
                [*y, y[-1]],
                drawstyle="steps-post",
                color=race_colors[race],
                linestyle=region_styles[region_id],
                linewidth=2,
                marker="o" if recent <= MARKER_LIMIT else None,
                markevery=list(range(len(x) - recent, len(x))),
                markersize=5,
                label=f"{region_names[region_id]} {race.name.lower()}",
            )
        _style(figure, axes, user.battle_tag, times)
        if windowed:
            axes.set_xlabel("last 6 months played", fontsize=LEGEND_FONT_SIZE)
        image = io.BytesIO()
        figure.savefig(image, format="png")
    return image.getvalue()


def window_series(
    stats: list[PlayerStat], start: datetime
) -> tuple[list[datetime], list[int], int] | None:
    """(times, MMRs, points inside) of one ladder from start on, or None if not played since.

    A ladder played before the window starts at the MMR it had when the window opens.
    """
    recent = [stat for stat in stats if stat.created_at >= start]
    if not recent:
        return None
    x = [stat.created_at for stat in recent]
    y = [stat.mmr for stat in recent]
    earlier = [stat for stat in stats if stat.created_at < start]
    if earlier:
        x, y = [start, *x], [earlier[-1].mmr, *y]
    return x, y, len(recent)


def _ladders(user: User) -> list[tuple[int, Race, list[PlayerStat]]]:
    """(region, race, stats sorted by date) of every ladder the user has stats for."""
    ladders = []
    for player in user.players:
        races = sorted({stat.race for stat in player.stats}, key=lambda race: race.value)
        for race in races:
            stats = sorted(
                (stat for stat in player.stats if stat.race == race),
                key=lambda stat: stat.created_at,
            )
            ladders.append((player.region_id, race, stats))
    return ladders


def _style(figure: Figure, axes: Axes, title: str, times: list[datetime]) -> None:
    axes.set_title(title)
    axes.set_ylabel("MMR")
    axes.grid(alpha=0.4)
    locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
    axes.xaxis.set_major_locator(locator)
    axes.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    axes.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10], integer=True))
    axes.ticklabel_format(axis="y", useOffset=False, style="plain")
    if times and max(times) - min(times) < timedelta(days=1):
        # One day of data: show the day around it instead of an arbitrary range.
        middle = min(times) + (max(times) - min(times)) / 2
        axes.set_xlim(
            mdates.date2num(middle - timedelta(days=1)), mdates.date2num(middle + timedelta(days=1))
        )
    lines = len(axes.get_lines())
    figure.legend(
        loc="outside lower center",
        ncols=min(lines, LEGEND_COLUMNS),
        frameon=False,
        fontsize=LEGEND_FONT_SIZE,
    )
