import math
import warnings
from datetime import datetime
from datetime import timedelta

import pytest

from sc2bot.database import session
from sc2bot.database.data import League
from sc2bot.database.data import Race
from sc2bot.database.schema import Player
from sc2bot.database.schema import PlayerStat
from sc2bot.plot import _break_gaps
from sc2bot.plot import plot_mmr_history

START = datetime(2022, 2, 4, 17, 30)


@pytest.fixture()
def player(user) -> Player:
    player = Player(user_id=user.id, region_id=2, profile_id=11, display_name="Foo")
    session.db_session.add(player)
    session.db_session.commit()
    return player


def _add_history(player: Player, times: list[datetime]) -> None:
    for i, time in enumerate(times):
        stat = PlayerStat(
            player_id=player.id,
            race=Race.ZERG,  # type: ignore
            league=League.GOLD,  # type: ignore
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
def test_plot_any_time_span_without_warnings(user, player, span):
    _add_history(player, [START, START + span] if span else [START])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        image = plot_mmr_history(user)
    assert image.startswith(b"\x89PNG")


def test_break_gaps_splits_long_gaps_only():
    times = [START, START + timedelta(days=1), START + timedelta(days=100)]
    x, y = _break_gaps(times, [1, 2, 3])
    assert len(x) == 4
    assert y[:2] == [1, 2] and math.isnan(y[2]) and y[3] == 3
    assert START + timedelta(days=1) < x[2] < START + timedelta(days=100)


def test_break_gaps_keeps_continuous_history():
    times = [START + timedelta(days=day) for day in range(30)]
    assert _break_gaps(times, list(range(30))) == (times, list(range(30)))
