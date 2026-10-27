from sc2bot.controller import rank
from sc2bot.database import session
from sc2bot.database.helpers import latest_stats


def test_rank_empty(db):
    assert "No ladders" in rank(telegram_id=1).text


def test_latest_stats_keeps_last_stat_per_player_and_race(ladders):
    stats = latest_stats(session.db_session)
    assert [stat.mmr for stat in stats] == [3500, 3100, 2500]


def test_latest_stats_of_one_user(ladders):
    foo, _ = ladders
    assert [stat.mmr for stat in latest_stats(session.db_session, foo)] == [3100, 2500]


def test_rank_best_ladder_per_user(ladders):
    text = rank(telegram_id=1).text
    assert text.index("QuxEU") < text.index("FooEU")
    assert "#1" in text and "#2" in text and "#3" not in text
    assert "3500" in text and "3100" in text
    assert "2500" not in text and "3000" not in text
    assert "75%" in text and "&lt;CLAN&gt;" in text
