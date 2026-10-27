import re

from sc2bot.bot_response import BotResponse, render
from sc2bot.client import get_battle_tag_info, resolve_player_display_name, resolve_player_stats
from sc2bot.commands import command_names
from sc2bot.database import session
from sc2bot.database.helpers import (
    add_player_stat,
    create_or_update_player,
    create_or_update_user,
    latest_stats,
)
from sc2bot.database.schema import PlayerStat, User
from sc2bot.emojis import league_emojis, race_emojis, region_emojis
from sc2bot.plot import plot_mmr_history


def set_battle_tag(
    battle_tag: str, *, telegram_id: int, telegram_username: str | None, **_kwargs: object
) -> BotResponse:

    if not _is_valid_battle_tag(battle_tag):
        return render("invalid_battle_tag")

    user = create_or_update_user(session.db_session, telegram_id, telegram_username, battle_tag)
    players = get_battle_tag_info(user)
    for player in players:
        create_or_update_player(
            session.db_session, user, player.region_id, player.profile_id, player.display_name
        )

    return render(
        "user_info",
        user=user,
        goto_register=command_names["register"],
        goto_link=command_names["link"],
    )


def retrieve_user(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])
    return render(
        "user_info",
        user=user,
        goto_register=command_names["register"],
        goto_link=command_names["link"],
    )


def add_player(profile_uri: str, *, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])

    try:
        region_id, profile_id = _parse_profile_url(profile_uri)
        profile_name = resolve_player_display_name(region_id, profile_id)
    except ValueError:
        return render(
            "invalid_sc2_url", url_template="https://starcraft2.com/en-us/profile/2/1/1234"
        )
    except RuntimeError:
        return render("no_display_name")

    create_or_update_player(session.db_session, user, region_id, profile_id, profile_name)

    return render(
        "user_info",
        user=user,
        goto_register=command_names["register"],
        goto_link=command_names["link"],
    )


def add_new_player_stats(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])

    _fetch_stats(user)
    return render(
        "user_info",
        user=user,
        goto_register=command_names["register"],
        goto_link=command_names["link"],
    )


def list_users(**_kwargs: object) -> BotResponse:
    users = session.db_session.query(User).order_by(User.id).all()
    return render("users", users=users)


def rank(**_kwargs: object) -> BotResponse:
    best_by_user: dict[int, PlayerStat] = {}
    for stat in latest_stats(session.db_session):
        best_by_user.setdefault(stat.player.user_id, stat)
    return _ranking("🤖Bot Ranking", list(best_by_user.values()))


def ladders(**_kwargs: object) -> BotResponse:
    return _ranking("🤖All ladders", latest_stats(session.db_session))


def profile(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])

    stats = latest_stats(session.db_session, user)
    response = _ranking(f"🎮{user.battle_tag} ladders (1v1)", stats)
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
    """Daily job: fetch the stats of every user, then build the ranking to post."""
    for user in session.db_session.query(User).all():
        _fetch_stats(user)
    return rank()


def _fetch_stats(user: User) -> None:
    for player in user.players:
        for player_stat in resolve_player_stats(player):
            add_player_stat(
                session.db_session,
                player,
                player_stat.race,
                player_stat.league,
                player_stat.mmr,
                player_stat.wins,
                player_stat.losses,
                player_stat.clan_tag,
            )


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


def _parse_profile_url(profile_uri: str) -> tuple[int, int]:
    match = re.match(r"https://starcraft2.com/en-us/profile/([1-4])/1/(\d+)", profile_uri)
    if match:
        region_id_raw, profile_id_raw = match.groups()
        return int(region_id_raw), int(profile_id_raw)
    raise ValueError("Invalid URL")
