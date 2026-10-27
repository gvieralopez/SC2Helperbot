from sqlalchemy import func
from sqlalchemy.orm import Session

from sc2bot.database.schema import Player, PlayerStat, User


def create_or_update_user(
    db_session: Session, telegram_id: int, telegram_username: str | None, battle_tag: str
) -> User:
    user = db_session.query(User).filter_by(telegram_id=telegram_id).one_or_none()

    if user:
        user.telegram_username = telegram_username
        user.battle_tag = battle_tag
    else:
        user = User(
            telegram_id=telegram_id, telegram_username=telegram_username, battle_tag=battle_tag
        )
    db_session.add(user)
    db_session.commit()
    return user


def create_or_update_player(
    db_session: Session, user: User, region_id: int, profile_id: int, display_name: str
) -> Player:
    player = (
        db_session.query(Player).filter_by(region_id=region_id, profile_id=profile_id).one_or_none()
    )

    if player:
        player.display_name = display_name
    else:
        player = Player(
            user_id=user.id, region_id=region_id, profile_id=profile_id, display_name=display_name
        )
    db_session.add(player)
    db_session.commit()
    return player


def latest_stats(db_session: Session, user: User | None = None) -> list[PlayerStat]:
    """Latest stat of every (player, race): the player's current ladder for that race.

    Latest by date, not by insertion: imported history can be older than what is stored.
    """
    newest_first = func.row_number().over(
        partition_by=(PlayerStat.player_id, PlayerStat.race),
        order_by=(PlayerStat.created_at.desc(), PlayerStat.id.desc()),
    )
    ranked = db_session.query(PlayerStat.id, newest_first.label("position")).subquery()
    latest_ids = db_session.query(ranked.c.id).filter(ranked.c.position == 1)
    query = db_session.query(PlayerStat).filter(PlayerStat.id.in_(latest_ids))
    if user is not None:
        query = query.join(Player).filter(Player.user_id == user.id)
    return sorted(query.all(), key=lambda stat: stat.mmr, reverse=True)
