import re

from sc2bot.client import get_battle_tag_info, resolve_player_display_name, resolve_player_stats
from sc2bot.database.helpers import create_or_update_user, create_or_update_player, add_player_stat
from sc2bot.database.schema import User
from sc2bot.database.session import db_session
from sc2bot.bot_response import render, BotResponse


def set_battle_tag(telegram_id: int, telegram_username: str, battle_tag: str) -> BotResponse:
    if not _is_valid_battle_tag(battle_tag):
        return render("invalid_battle_tag")

    user = create_or_update_user(db_session, telegram_id, telegram_username, battle_tag)
    players = get_battle_tag_info(user)
    for player in players:
        create_or_update_player(
            db_session, user, player.region_id, player.profile_id, player.display_name
        )

    return render("user_info", user=user)


def retrieve_user(telegram_id: int) -> BotResponse:
    user = db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found")
    return render("user_info", user=user)


def add_player(telegram_id: int, profile_uri: str) -> BotResponse:
    user = db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found")

    try:
        region_id, profile_id = _parse_profile_url(profile_uri)
    except ValueError:
        return render("invalid_sc2_url")

    profile_name = resolve_player_display_name(region_id, profile_id)

    create_or_update_player(db_session, user, region_id, profile_id, profile_name)

    return render("user_info", user=user)


def add_player_stats(telegram_id: int) -> BotResponse:
    user = db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found")

    for player in user.players:
        for player_stat in resolve_player_stats(player):
            add_player_stat(
                db_session,
                player,
                player_stat.race,  # type: ignore
                player_stat.league,  # type: ignore
                player_stat.mmr,
                player_stat.wins,
                player_stat.losses,
                player_stat.clan_tag,
            )
    return render("user_info", user=user)


def _is_valid_battle_tag(battle_tag: str) -> bool:
    pattern = (
        r"(^([A-zÀ-ú][A-zÀ-ú0-9]{2,11})|(^([а-яёА-ЯЁÀ-ú][а-яёА-ЯЁ0-9À-ú]{2,11})))(#[0-9]{4,})$"
    )
    match = re.match(pattern, battle_tag)
    return bool(match)


def _parse_profile_url(profile_uri: str) -> tuple[int, int]:
    ...
