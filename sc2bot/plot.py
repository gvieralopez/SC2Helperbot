import io

import matplotlib

matplotlib.use("Agg")

from matplotlib import dates as mdates  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from sc2bot.database.schema import User  # noqa: E402

region_names = {1: "US", 2: "EU", 3: "KR", 4: "TW"}


def plot_mmr_history(user: User) -> bytes:
    """PNG with one MMR-over-time line per (region, race) the user has played."""
    figure = Figure()
    axes = figure.subplots()
    axes.set_title(user.battle_tag)
    axes.grid()
    for player in user.players:  # type: ignore
        races = sorted({stat.race for stat in player.stats}, key=lambda race: race.value)  # type: ignore
        for race in races:
            stats = [stat for stat in player.stats if stat.race == race]
            axes.plot(
                [stat.created_at for stat in stats],
                [stat.mmr for stat in stats],
                label=f"{region_names[player.region_id]} - {race.name.lower()}",
            )
    axes.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    axes.legend()
    figure.autofmt_xdate()
    image = io.BytesIO()
    figure.savefig(image, format="png")
    return image.getvalue()
