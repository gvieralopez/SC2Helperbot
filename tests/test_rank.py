from datetime import datetime

from sc2bot.controller import rank
from sc2bot.database import session
from sc2bot.database.helpers import latest_stats
from sc2bot.database.schema import User


def test_rank_empty(db: None) -> None:
    assert "No ladders" in rank(telegram_id=1).text


def test_latest_stats_keeps_last_stat_per_player_and_race(ladders: tuple[User, User]) -> None:
    stats = latest_stats(session.db_session)
    assert [stat.mmr for stat in stats] == [3500, 3100, 2500]


def test_latest_stats_of_one_user(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    assert [stat.mmr for stat in latest_stats(session.db_session, foo)] == [3100, 2500]


def test_rank_best_ladder_per_user(ladders: tuple[User, User]) -> None:
    text = rank(telegram_id=1).text
    assert text.index("QuxEU") < text.index("FooEU")
    assert "#1" in text and "#2" in text and "#3" not in text
    assert "3500" in text and "3100" in text
    assert "2500" not in text and "3000" not in text
    assert "75%" in text and "&lt;CLAN&gt;" in text


def test_latest_stats_uses_the_date_not_the_insertion_order(ladders: tuple[User, User]) -> None:
    foo, _ = ladders
    zerg = max(latest_stats(session.db_session, foo), key=lambda stat: stat.mmr)
    old = type(zerg)(
        player_id=zerg.player_id,
        race=zerg.race,
        league=zerg.league,
        mmr=9999,
        wins=0,
        losses=0,
        created_at=datetime(2016, 1, 1),
    )
    session.db_session.add(old)
    session.db_session.commit()
    assert 9999 not in [stat.mmr for stat in latest_stats(session.db_session)]
