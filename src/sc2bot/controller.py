import logging
import re

import requests

from sc2bot.bot_response import BotResponse, render
from sc2bot.client.sc2_pulse import current_ladders, get_battle_tag_info
from sc2bot.commands import command_names
from sc2bot.database import session
from sc2bot.database.helpers import create_or_update_player, create_or_update_user, latest_stats
from sc2bot.database.schema import Player, PlayerStat, User
from sc2bot.emojis import league_emojis, race_emojis, region_emojis
from sc2bot.plot import plot_mmr_history

logger = logging.getLogger(__name__)


def set_battle_tag(
    battle_tag: str, *, telegram_id: int, telegram_username: str | None, **_kwargs: object
) -> BotResponse:

    if not _is_valid_battle_tag(battle_tag):
        return render("invalid_battle_tag")

    user = create_or_update_user(session.db_session, telegram_id, telegram_username, battle_tag)
    _refresh_profiles(user)
    return _user_info(user)


def retrieve_user(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])
    return _user_info(user)


def add_new_player_stats(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])

    _refresh_profiles(user)
    _fetch_stats(user.players)
    return _user_info(user)


def list_users(**_kwargs: object) -> BotResponse:
    users = session.db_session.query(User).order_by(User.id).all()
    return render("users", users=users)


def rank(**_kwargs: object) -> BotResponse:
    best_by_user: dict[int, PlayerStat] = {}
    for stat in latest_stats(session.db_session):
        best_by_user.setdefault(stat.player.user_id, stat)
    return _ranking("🏆 Ranking", list(best_by_user.values()))


def ladders(**_kwargs: object) -> BotResponse:
    return _ranking("📋 All ladders", latest_stats(session.db_session))


def profile(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])

    stats = latest_stats(session.db_session, user)
    response = _ranking(f"🎮 {user.battle_tag}", stats)
    if stats:
        response.image = plot_mmr_history(user)
    return response


def _ranking(title: str, stats: list[PlayerStat]) -> BotResponse:
    return render(
        "ranking",
        title=title,
        stats=stats,
        region_emojis=region_emojis,
        league_emojis=league_emojis,
        race_emojis=race_emojis,
    )


def fetch_all_users() -> BotResponse:
    """Daily job: refresh every user's profiles and ladders, then build the ranking to post."""
    users = session.db_session.query(User).all()
    for user in users:
        _refresh_profiles(user)
    _fetch_stats([player for user in users for player in user.players])
    return rank()


def _user_info(user: User) -> BotResponse:
    return render(
        "user_info", user=user, region_emojis=region_emojis, goto_register=command_names["register"]
    )


def _refresh_profiles(user: User) -> None:
    """Add the profiles of the user's Battle Tag that aren't stored yet, and update names."""
    for player in get_battle_tag_info(user):
        create_or_update_player(
            session.db_session, user, player.region_id, player.profile_id, player.display_name
        )


def _fetch_stats(players: list[Player]) -> None:
    """Store each current ladder whose MMR or number of games changed since the last stat."""
    try:
        stats = current_ladders(players)
    except requests.RequestException as e:
        logger.warning("SC2 Pulse ladders failed: %s", e)
        return
    latest = {(stat.player_id, stat.race): stat for stat in latest_stats(session.db_session)}
    for stat in stats:
        last = latest.get((stat.player_id, stat.race))
        games = stat.wins + stat.losses
        if last and (last.mmr, last.wins + last.losses) == (stat.mmr, games):
            continue
        session.db_session.add(stat)
    session.db_session.commit()


def _is_valid_battle_tag(battle_tag: str) -> bool:
    pattern = (
        # A Latin or Cyrillic name, then #digits. The Cyrillic letters are escaped
        # (\u0430-\u044f, \u0451, \u0410-\u042f, \u0401) so they can't be mistaken for Latin ones.
        r"(^([A-zÀ-ú][A-zÀ-ú0-9]{2,11})"
        r"|(^([\u0430-\u044f\u0451\u0410-\u042f\u0401À-ú]"
        r"[\u0430-\u044f\u0451\u0410-\u042f\u04010-9À-ú]{2,11})))"
        r"(#[0-9]{4,})$"
    )
    match = re.match(pattern, battle_tag)
    return bool(match)
