import logging
import re
from datetime import timedelta

import requests

from sc2bot.bot_response import BotResponse, Button, render
from sc2bot.client.sc2_pulse import current_ladders, get_battle_tag_info
from sc2bot.commands import command_names
from sc2bot.database import session
from sc2bot.database.data import Race
from sc2bot.database.helpers import create_or_update_player, create_or_update_user, latest_stats
from sc2bot.database.schema import Player, PlayerStat, User
from sc2bot.emojis import league_emojis, race_emojis, region_emojis
from sc2bot.plot import plot_ladder

logger = logging.getLogger(__name__)

PINGS_PER_MESSAGE = 4
REGION_NAMES = {1: "US", 2: "EU", 3: "KR", 4: "TW", 5: "CN"}
# Time shown by the /profile chart, before the ladder's last game (None: all of it).
PROFILE_WINDOWS = {
    "6m": ("6 months", timedelta(days=182)),
    "1y": ("1 year", timedelta(days=365)),
    "all": ("All", None),
}
DEFAULT_WINDOW = "6m"
PROFILE_RACES = [Race.ZERG, Race.PROTOSS, Race.TERRAN, Race.RANDOM]


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


def ping_outside_a_group(**_kwargs: object) -> BotResponse:
    return render("hlp_ping")


def ping_texts(users: list[User]) -> list[str]:
    """Messages mentioning the users, four per message: Telegram notifies only the first four."""
    batches = [
        users[start : start + PINGS_PER_MESSAGE]
        for start in range(0, len(users), PINGS_PER_MESSAGE)
    ]
    return [render("ping", users=batch).text for batch in batches or [[]]]


def registered_users() -> list[User]:
    return session.db_session.query(User).order_by(User.id).all()


def list_users(**_kwargs: object) -> BotResponse:
    return render("users", users=registered_users())


def rank(**_kwargs: object) -> BotResponse:
    best_by_user: dict[int, PlayerStat] = {}
    for stat in latest_stats(session.db_session):
        best_by_user.setdefault(stat.player.user_id, stat)
    return _ranking("🏆 Ranking", list(best_by_user.values()))


def ladders(**_kwargs: object) -> BotResponse:
    return _ranking("📋 All ladders", latest_stats(session.db_session))


def profile(*, telegram_id: int, **_kwargs: object) -> BotResponse:
    """The chart of the user's most recently played ladder, with buttons to pick another."""
    user = session.db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user is None:
        return render("user_not_found", goto=command_names["register"])
    stats = [stat for player in user.players for stat in player.stats]
    if not stats:
        return _ranking(f"🎮 {user.battle_tag}", [])
    last = max(stats, key=lambda stat: stat.created_at)
    return _profile_view(user, last.player.region_id, last.race, DEFAULT_WINDOW)


def profile_button(data: str) -> BotResponse | None:
    """The profile view a button asks for ("profile:user:region:race:window"), or None."""
    _, user_id, region_id, race, window = data.split(":")
    user = session.db_session.get(User, int(user_id))
    if user is None or window not in PROFILE_WINDOWS:
        return None
    return _profile_view(user, int(region_id), Race(int(race)), window)


def _profile_view(user: User, region_id: int, race: Race, window: str) -> BotResponse:
    """One ladder (region and race) of the user over a time window, and the buttons that change
    one of the three; each button holds the whole view it leads to."""
    stats = _ladder_stats(user, region_id, race)
    response = render(
        "profile",
        user=user,
        stat=stats[-1] if stats else None,
        region_emojis=region_emojis,
        league_emojis=league_emojis,
        race_emojis=race_emojis,
    )
    title = f"{REGION_NAMES[region_id]} {race.name.title()}"
    response.image = plot_ladder(stats, race, title, PROFILE_WINDOWS[window][1])

    def button(label: str, selected: bool, region: int, button_race: Race, span: str) -> Button:
        data = f"profile:{user.id}:{region}:{button_race.value}:{span}"
        return Button(label, data, selected)

    regions = sorted({player.region_id for player in user.players})
    response.buttons = [
        [
            button(f"{region_emojis[r]} {REGION_NAMES[r]}", r == region_id, r, race, window)
            for r in regions
        ],
        [button(race_emojis[r], r == race, region_id, r, window) for r in PROFILE_RACES],
        [
            button(label, key == window, region_id, race, key)
            for key, (label, _) in PROFILE_WINDOWS.items()
        ],
    ]
    return response


def _ladder_stats(user: User, region_id: int, race: Race) -> list[PlayerStat]:
    """The stats of the user's ladder in that region and race, sorted by date. With more than
    one profile in the region, the one played last."""
    ladders = [
        sorted((s for s in player.stats if s.race == race), key=lambda s: s.created_at)
        for player in user.players
        if player.region_id == region_id
    ]
    played = [ladder for ladder in ladders if ladder]
    return max(played, key=lambda ladder: ladder[-1].created_at) if played else []


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
