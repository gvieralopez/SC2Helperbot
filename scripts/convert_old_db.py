"""Convert the data of the old bot (main branch) into the new schema.

    python -m scripts.convert_old_db OLD_DB HISTORY_DIR CONNECTION_STRING

OLD_DB is the old sc2.db, HISTORY_DIR the old data/history folder (h<ladder id>.json files)
and CONNECTION_STRING the new database, which must be empty.

The old history only kept the MMR and the date of each point, so every point takes the
league, wins, losses and clan of its ladder's last known state. History files without a
ladder are dropped (their region and race are unknown).
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from sys import argv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sc2bot.database.data import League, Race
from sc2bot.database.schema import Base, Player, PlayerStat, User

logger = logging.getLogger(__name__)

REGION_COLUMNS = {1: "US_id", 2: "EU_id", 3: "KR_id", 4: "TW_id"}


@dataclass
class Report:
    users: int = 0
    players: int = 0
    stats: int = 0
    skipped: list[str] = field(default_factory=list)


def main(old_db: Path, history_dir: Path, connection_string: str) -> Report:
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    old = sqlite3.connect(f"file:{old_db}?mode=ro", uri=True)
    old.row_factory = sqlite3.Row
    report = Report()

    db_session = sessionmaker(bind=engine)()
    try:
        if db_session.query(User).count():
            raise SystemExit("The new database already has users: refusing to convert into it.")
        players = _convert_users(old, db_session, report)
        ladder_ids = _convert_ladders(old, db_session, players, history_dir, report)
        report.skipped += _orphan_history_files(history_dir, ladder_ids)
        db_session.commit()
    finally:
        db_session.close()
        old.close()
        engine.dispose()
    return report


def _convert_users(
    old: sqlite3.Connection, db_session: Session, report: Report
) -> dict[tuple[int, int], Player]:
    """Add every user and their profiles; returns the players by (old user id, region)."""
    players = {}
    for row in old.execute("SELECT * FROM users ORDER BY id"):
        user = _convert_user(row)
        db_session.add(user)
        report.users += 1
        for region_id, column in REGION_COLUMNS.items():
            if row[column] is not None:
                players[(row["id"], region_id)] = _convert_player(row, user, region_id, row[column])
                report.players += 1
    db_session.add_all(players.values())
    db_session.flush()
    return players


def _convert_ladders(
    old: sqlite3.Connection,
    db_session: Session,
    players: dict[tuple[int, int], Player],
    history_dir: Path,
    report: Report,
) -> set[int]:
    """Add the stats of every ladder; returns the old ladder ids."""
    ladder_ids = set()
    for row in old.execute("SELECT * FROM usersmmr ORDER BY id"):
        ladder_ids.add(row["id"])
        player = players.get((row["user_id"], row["region"]))
        if player is None:
            report.skipped.append(f"ladder {row['id']}: user has no profile in region")
            continue
        stats = _convert_ladder(row, player, _read_history(history_dir, row["id"]))
        db_session.add_all(stats)
        report.stats += len(stats)
    return ladder_ids


def _orphan_history_files(history_dir: Path, ladder_ids: set[int]) -> list[str]:
    return [
        f"{history_file.name}: no ladder"
        for history_file in sorted(history_dir.glob("h*.json"))
        if int(history_file.stem[1:]) not in ladder_ids
    ]


def _convert_user(row: sqlite3.Row) -> User:
    return User(
        telegram_id=row["tgid"],
        telegram_username=row["arroba"],
        battle_tag=row["battle_tag"],
        created_at=_parse_datetime(row["created_at"]),
        modified_at=_parse_datetime(row["modified_at"]),
    )


def _convert_player(row: sqlite3.Row, user: User, region_id: int, profile_id: int) -> Player:
    # The old schema kept one display name per user; the new one keeps it per profile.
    display_name = row["display_name"] or row["battle_tag"].split("#")[0]
    return Player(
        user=user,
        region_id=region_id,
        profile_id=profile_id,
        display_name=display_name,
        created_at=_parse_datetime(row["created_at"]),
        modified_at=_parse_datetime(row["modified_at"]),
    )


def _convert_ladder(
    row: sqlite3.Row, player: Player, history: list[tuple[datetime, int]]
) -> list[PlayerStat]:
    last_update = _parse_datetime(row["modified_at"])
    points = sorted(history)
    if not points or (points[-1][0].date(), points[-1][1]) != (last_update.date(), row["mmr"]):
        points.append((last_update, row["mmr"]))
    return [
        PlayerStat(
            player=player,
            race=Race.from_raw(row["race"]),
            league=League.from_raw(row["league"]),
            mmr=mmr,
            wins=row["wins"],
            losses=row["losses"],
            clan_tag=row["clan"] or None,
            created_at=created_at,
        )
        for created_at, mmr in points
    ]


def _read_history(history_dir: Path, ladder_id: int) -> list[tuple[datetime, int]]:
    history_file = history_dir / f"h{ladder_id}.json"
    if not history_file.is_file():
        return []
    history = json.loads(history_file.read_text())
    dates = [datetime.strptime(date, "%d-%m-%Y") for date in history["dates"]]
    return list(zip(dates, history["mmrs"], strict=True))


def _parse_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = main(Path(argv[1]), Path(argv[2]), argv[3])
    logger.info(
        "Converted %s users, %s players, %s stats", result.users, result.players, result.stats
    )
    for reason in result.skipped:
        logger.warning("Skipped %s", reason)
