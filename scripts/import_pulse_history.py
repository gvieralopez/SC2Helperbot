"""Add the 1v1 MMR history that SC2 Pulse (sc2pulse.nephest.com) keeps for every stored player.

    python -m scripts.import_pulse_history CONNECTION_STRING

Run it once after scripts.convert_old_db, and again whenever new players registered; points
that are already stored are skipped. SC2 Pulse keeps about one point per season before 2021
and many per day since. It only knows the current clan, so imported points take that one, and points without\nwins take the last known wins of their history.

Data from SC2 Pulse (https://sc2pulse.nephest.com/sc2), whose API is free for non-commercial
use with credit. Ids (leagues 0-6 from bronze, races 1-4) are documented in its API docs.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from sys import argv

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sc2bot.client.config import REALM_ID
from sc2bot.database.data import League, Race
from sc2bot.database.schema import Base, Player, PlayerStat

logger = logging.getLogger(__name__)

API = "https://sc2pulse.nephest.com/sc2/api"
HEADERS = {"User-Agent": "SC2Helperbot history import (github.com/gvieralopez/SC2Helperbot)"}
FIELDS = ["TIMESTAMP", "RATING", "LEAGUE_TYPE", "WINS", "GAMES"]
TEAMS_LIMIT = 200  # the API rejects larger pages
HISTORIES_PER_CALL = 10  # the API's maximum
PAUSE = 0.5  # seconds between calls, to go easy on a free service

# The last part of a team legacy uid ("201-0-2-1.8972769.3") is the race.
RACES = {"1": Race.TERRAN, "2": Race.PROTOSS, "3": Race.ZERG, "4": Race.RANDOM}
LEAGUES = {league.value: league for league in League}


@dataclass
class Report:
    players: int = 0
    added: int = 0
    skipped: int = 0
    not_found: list[str] = field(default_factory=list)


def main(connection_string: str) -> Report:
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    report = Report()
    try:
        for player in db_session.query(Player).order_by(Player.id).all():
            _import_player(db_session, player, report)
        db_session.commit()
    finally:
        db_session.close()
    return report


def _import_player(db_session: Session, player: Player, report: Report) -> None:
    handle = f"{player.region_id}-S2-{REALM_ID}-{player.profile_id}"
    stats = _fetch_history(player, handle)
    if stats is None:
        report.not_found.append(handle)
        return
    report.players += 1

    known = {(s.race, s.created_at, s.mmr) for s in player.stats}
    known_days = {(race, created_at.date(), mmr) for race, created_at, mmr in known}
    for stat in stats:
        key = (stat.race, stat.created_at, stat.mmr)
        if key in known or (stat.race, stat.created_at.date(), stat.mmr) in known_days:
            report.skipped += 1
            continue
        known.add(key)
        db_session.add(stat)
        report.added += 1


def _fetch_history(player: Player, handle: str) -> list[PlayerStat] | None:
    """Every 1v1 history point SC2 Pulse has for the player, or None if it doesn't know them."""
    teams = _get("character-teams", toonHandle=handle, queue="LOTV_1V1", limit=TEAMS_LIMIT)
    if not teams:
        return None
    if len(teams) == TEAMS_LIMIT:
        logger.warning(f"{handle}: {TEAMS_LIMIT} teams, the oldest seasons may be missing")
    clan_tag = (teams[0]["members"][0].get("clan") or {}).get("tag")

    stats = []
    uids = sorted({team["legacyUid"] for team in teams})
    for start in range(0, len(uids), HISTORIES_PER_CALL):
        chunk = uids[start : start + HISTORIES_PER_CALL]
        for team in _get("team-histories", teamLegacyUid=chunk, history=FIELDS):
            race = RACES[team["staticData"]["LEGACY_UID"].rsplit(".", 1)[1]]
            stats += _stats(player, race, team["history"], clan_tag)
    return stats


def _stats(player: Player, race: Race, history: dict, clan_tag: str | None) -> list[PlayerStat]:
    stats = []
    last_wins = 0
    for timestamp, rating, league, wins, games in zip(*(history[name] for name in FIELDS)):
        # About a third of the points have no wins: take the last known ones, like the old history.
        wins = min(last_wins if wins is None else wins, games)
        last_wins = wins
        stat = PlayerStat(
            player_id=player.id,
            race=race,
            league=LEAGUES[league],
            mmr=rating,
            wins=wins,
            losses=games - wins,
            clan_tag=clan_tag,
            # Naive UTC, like the CURRENT_TIMESTAMP default of the bot's own stats.
            created_at=datetime.fromtimestamp(timestamp, UTC).replace(tzinfo=None),
        )
        stats.append(stat)
    return stats


def _get(endpoint: str, **params) -> list:
    time.sleep(PAUSE)
    response = requests.get(f"{API}/{endpoint}", params=params, headers=HEADERS, timeout=60)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = main(argv[1])
    logger.info(
        f"{result.players} players found: {result.added} points added, "
        f"{result.skipped} already stored"
    )
    for handle in result.not_found:
        logger.warning(f"Not found on SC2 Pulse: {handle}")
