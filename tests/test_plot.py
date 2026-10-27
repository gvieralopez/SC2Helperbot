import warnings
from datetime import datetime, timedelta

import pytest

from sc2bot.database import session
from sc2bot.database.data import League, Race
from sc2bot.database.schema import Player, PlayerStat, User
from sc2bot.plot import plot_mmr_history, window_series

START = datetime(2022, 2, 4, 17, 30)


@pytest.fixture()
def player(user: User) -> Player:
    player = Player(user_id=user.id, region_id=2, profile_id=11, display_name="Foo")
    session.db_session.add(player)
    session.db_session.commit()
    return player


def _add_history(player: Player, times: list[datetime]) -> None:
    for i, time in enumerate(times):
        stat = PlayerStat(
            player_id=player.id,
            race=Race.ZERG,
            league=League.GOLD,
            mmr=3000 + i,
            wins=1,
            losses=1,
            created_at=time,
        )
        session.db_session.add(stat)
    session.db_session.commit()


@pytest.mark.parametrize(
    "span",
    [timedelta(0), timedelta(hours=3), timedelta(days=2), timedelta(days=2, hours=12)]
    + [timedelta(days=days) for days in (7, 45, 180, 730, 1825)],
)
def test_plot_any_time_span_without_warnings(user: User, player: Player, span: timedelta) -> None:
    _add_history(player, [START, START + span] if span else [START])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        image = plot_mmr_history(user)
    assert image.startswith(b"\x89PNG")


@pytest.mark.parametrize("region_id", [1, 2, 3, 4, 5])
def test_plot_every_region(user: User, player: Player, region_id: int) -> None:
    player.region_id = region_id
    _add_history(player, [START, START + timedelta(days=2)])
    assert plot_mmr_history(user).startswith(b"\x89PNG")


def test_window_series_starts_at_the_mmr_held_when_the_window_opens() -> None:
    stats = [PlayerStat(created_at=START + timedelta(days=day), mmr=day) for day in (0, 10, 20)]
    series = window_series(stats, START + timedelta(days=15))
    assert series is not None
    x, y, recent = series
    assert x == [START + timedelta(days=15), START + timedelta(days=20)]
    assert y == [10, 20] and recent == 1


def test_window_series_skips_ladders_not_played_since() -> None:
    stats = [PlayerStat(created_at=START, mmr=3000)]
    assert window_series(stats, START + timedelta(days=1)) is None
