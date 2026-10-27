import warnings
from datetime import datetime, timedelta

import pytest

from sc2bot.database.data import League, Race
from sc2bot.database.schema import PlayerStat
from sc2bot.plot import BREAK, _daily, _step_segments, ladder_series, plot_ladder

START = datetime(2022, 2, 4, 17, 30)


def _stats(times: list[datetime], race: Race = Race.ZERG) -> list[PlayerStat]:
    return [
        PlayerStat(race=race, league=League.GOLD, mmr=3000 + i, wins=1, losses=1, created_at=time)
        for i, time in enumerate(times)
    ]


@pytest.mark.parametrize(
    "span",
    [timedelta(0), timedelta(hours=3), timedelta(days=2), timedelta(days=2, hours=12)]
    + [timedelta(days=days) for days in (7, 45, 180, 730, 1825)],
)
@pytest.mark.parametrize("window", [timedelta(days=182), None])
def test_plot_any_time_span_without_warnings(span: timedelta, window: timedelta | None) -> None:
    stats = _stats([START, START + span] if span else [START])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        image = plot_ladder(stats, Race.ZERG, "EU Zerg", window)
    assert image.startswith(b"\x89PNG")


@pytest.mark.parametrize("race", list(Race))
def test_plot_an_empty_ladder(race: Race) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert plot_ladder([], race, "US Random", None).startswith(b"\x89PNG")


def test_ladder_series_starts_at_the_mmr_held_when_the_window_opens() -> None:
    stats = [PlayerStat(created_at=START + timedelta(days=day), mmr=day) for day in (0, 10, 20)]
    times, mmrs = ladder_series(stats, timedelta(days=5))
    assert times == [START + timedelta(days=15), START + timedelta(days=20)]
    assert mmrs == [10, 20]


def test_ladder_series_without_a_window_is_everything_sorted() -> None:
    stats = [PlayerStat(created_at=START + timedelta(days=day), mmr=day) for day in (20, 0, 10)]
    assert ladder_series(stats, None) == (
        [START, START + timedelta(days=10), START + timedelta(days=20)],
        [0, 10, 20],
    )


def test_daily_keeps_the_last_mmr_of_each_day() -> None:
    times = [START, START + timedelta(hours=1), START + timedelta(days=1)]
    assert _daily(times, [1, 2, 3]) == ([times[1], times[2]], [2, 3])


def test_long_flat_stretches_are_breaks() -> None:
    times = [START, START + timedelta(days=1), START + BREAK + timedelta(days=2)]
    played, breaks = _step_segments(times, [3000, 3010, 3050])
    # Day 0 to 1 is played; then the MMR is held (a break) until the game that moves it.
    assert len(breaks) == 1
    assert [(y0, y1) for (_, y0), (_, y1) in breaks] == [(3010, 3010)]
    assert [(y0, y1) for (_, y0), (_, y1) in played] == [(3000, 3010), (3010, 3050)]
