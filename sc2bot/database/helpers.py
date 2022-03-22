from sqlalchemy.orm import Session

from sc2bot.database.schema import User


def create_user(db_session: Session, telegram_id: int, telegram_username: str, battle_tag: str):
    db_user = User(
        telegram_id=telegram_id, telegram_username=telegram_username, battle_tag=battle_tag
    )
    db_session.add(db_user)
    db_session.commit()
