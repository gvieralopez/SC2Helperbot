import logging

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from sc2bot.database.schema import Base

logger = logging.getLogger(__name__)

# Bound to the database by connect() when the bot starts.
db_session = Session()


def connect(connection_string: str) -> None:
    engine = create_engine(connection_string)
    if not inspect(engine).has_table("users"):
        logger.info("Empty database: creating the tables.")
        Base.metadata.create_all(engine)
    db_session.bind = engine
