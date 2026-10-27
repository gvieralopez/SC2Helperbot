import logging

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from sc2bot.database.config import CONNECTION_STRING
from sc2bot.database.schema import Base

logger = logging.getLogger(__name__)

engine = create_engine(CONNECTION_STRING)
engine.connect()
Base.metadata.bind = engine
if not inspect(engine).has_table("users"):
    logger.info("A connection to the database couldn't be established. Creating tables in new DB.")
    Base.metadata.create_all(engine)


session_maker = sessionmaker(bind=engine)
db_session = session_maker()
