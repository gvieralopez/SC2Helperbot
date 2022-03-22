from sqlalchemy.orm import Session

from sc2bot.database.schema import User


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
