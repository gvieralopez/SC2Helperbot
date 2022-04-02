from sqlalchemy.orm import Session

from sc2bot.database.data import Race, League
from sc2bot.database.schema import User, Player, PlayerStat


def create_or_update_user(
    db_session: Session, telegram_id: int, telegram_username: str, battle_tag: str
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


def add_player_stat(
    db_session: Session,
    player: Player,
    race: Race,
    league: League,
    mmr: int,
    wins: int,
    losses: int,
    clan_tag: str,
) -> PlayerStat:
    player_stat = PlayerStat(
        player_id=player.id,
        race=race,  # type: ignore
        league=league,  # type: ignore
        mmr=mmr,
        wins=wins,
        losses=losses,
        clan_tag=clan_tag,
    )
    db_session.add(player_stat)
    db_session.commit()
    return player_stat


# todo add db constraints (unique(telegram_id) and unique(region_id, profile_id)) - add unit test
