import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from sc2bot.database.config import CONNECTION_STRING
from sc2bot.database.schema import Base

logger = logging.getLogger(__name__)

engine = create_engine(CONNECTION_STRING)
try:
    engine.connect()
    Base.metadata.bind = engine
except OperationalError:
    logger.info("A connection to the database couldn't be established. Creating tables in new DB.")
    Base.metadata.create_all(engine)


session_maker = sessionmaker(bind=engine)
db_session = session_maker()
