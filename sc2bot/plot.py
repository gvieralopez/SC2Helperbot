import io
from datetime import timedelta

import matplotlib

matplotlib.use("Agg")

from matplotlib import dates as mdates  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

from sc2bot.database.data import Race  # noqa: E402
from sc2bot.database.schema import User  # noqa: E402

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
# Longer gaps without data break the line instead of drawing a fake trend.
GAP = timedelta(days=14)


def plot_mmr_history(user: User) -> bytes:
    """PNG with one MMR-over-time line per (region, race) the user has played."""
    with matplotlib.rc_context({"font.size": FONT_SIZE}):
        figure = Figure(figsize=FIGURE_SIZE, dpi=DPI, layout="constrained")
        axes = figure.subplots()
        times = []
        for player in user.players:  # type: ignore
            races = sorted({stat.race for stat in player.stats}, key=lambda race: race.value)  # type: ignore
            for race in races:
                stats = sorted(
                    (stat for stat in player.stats if stat.race == race),  # type: ignore
                    key=lambda stat: stat.created_at,
                )
                x, y = _break_gaps([s.created_at for s in stats], [s.mmr for s in stats])
                times += [s.created_at for s in stats]
                axes.plot(
                    x,
                    y,
                    color=race_colors[race],
                    linestyle=region_styles[player.region_id],
                    linewidth=2,
                    marker="o" if len(stats) <= MARKER_LIMIT else None,
                    markersize=5,
                    label=f"{region_names[player.region_id]} {race.name.lower()}",
                )
        _style(figure, axes, user.battle_tag, times)
        image = io.BytesIO()
        figure.savefig(image, format="png")
    return image.getvalue()


def _break_gaps(times: list, mmrs: list) -> tuple[list, list]:
    x, y = times[:1], mmrs[:1]
    for previous, time, mmr in zip(times, times[1:], mmrs[1:]):
        if time - previous > GAP:
            x.append(previous + (time - previous) / 2)
            y.append(float("nan"))
        x.append(time)
        y.append(mmr)
    return x, y


def _style(figure: Figure, axes, title: str, times: list) -> None:
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
        axes.set_xlim(middle - timedelta(days=1), middle + timedelta(days=1))
    lines = len(axes.get_lines())
    figure.legend(
        loc="outside lower center",
        ncols=min(lines, LEGEND_COLUMNS),
        frameon=False,
        fontsize=LEGEND_FONT_SIZE,
    )
