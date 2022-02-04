import os
import logging
import datetime
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import desc, asc
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from data.db_schema import Base, User, UserMMR

from config import DB_LOCATION, DB_NAME

if not DB_NAME in os.listdir(DB_LOCATION):
    logging.warning('Not db found, creating one')
    # Create an engine that stores data in the local directory's
    # sqlalchemy_example.db file.
    engine = create_engine(f'sqlite:///{DB_LOCATION}//{DB_NAME}')
    
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    Base.metadata.create_all(engine)
    db_empty = True
else:
    logging.info('Loading db')
    engine = create_engine(f'sqlite:///{DB_LOCATION}//{DB_NAME}')
    # Bind the engine to the metadata of the Base class so that the
    # declaratives can be accessed through a DBSession instance
    Base.metadata.bind = engine
    db_empty = False

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. 
s = DBSession()


def create_user(tgid, arroba=None, battle_tag=None,  
    US_id=None, EU_id=None, KR_id=None, TW_id=None, display_name=None):

    date = datetime.datetime.now()
    s.add(User(tgid=tgid,
               arroba=arroba, 
               battle_tag=battle_tag,
               US_id = US_id,
               EU_id = EU_id,
               KR_id = KR_id,
               TW_id = TW_id,
               display_name=display_name,
               created_at=date,
               modified_at=date))
    s.commit()

def get_user(tgid, battle_tag=None):
    qry = s.query(User)
    if tgid:
        qry = qry.filter(User.tgid == tgid)
    if battle_tag:
        qry = qry.filter(User.battle_tag == battle_tag)
    if qry:
        try:
            return qry.one()
        except sqlalchemy.orm.exc.NoResultFound:
            pass

def update_user(user, modified=False):
    if modified:
        user.modified_at = datetime.datetime.now()
    s.add(user)
    s.commit()

def create_user_ladder(user, region, race):
    date = datetime.datetime.now()
    user_ladder = UserMMR(region = region,
        race = race,
        user_id = user.id,
        ladder_id = -1,

        league = "",
        mmr = 0,
        wins = 0,
        losses = 0,
        history = None, # TODO: Create the file and a path to it
        clan = '',

        created_at=date,
        modified_at=date)
    s.add(user_ladder)
    s.commit()
    return user_ladder

def get_user_ladder(user, region, race, create=True): 
    qry = s.query(UserMMR)
    qry = qry.filter(UserMMR.user_id == user.id)
    qry = qry.filter(UserMMR.region == region)
    qry = qry.filter(UserMMR.race == race)

    if qry:
        try:
            return qry.one()
        except sqlalchemy.orm.exc.NoResultFound:
            if create:
                return create_user_ladder(user, region, race)

def get_all_ladders(user=None, region=None, race=None, create=True): 
    qry = s.query(UserMMR)
    if user is not None:
        qry = qry.filter(UserMMR.user_id == user.id)
    if region is not None:
        qry = qry.filter(UserMMR.region == region)
    if race is not None:
        qry = qry.filter(UserMMR.race == race)
    if qry:
        try:
            return qry.all()
        except sqlalchemy.orm.exc.NoResultFound:
            pass
    return []

def get_all_users(): 
    qry = s.query(User)
    if qry:
        try:
            return qry.all()
        except sqlalchemy.orm.exc.NoResultFound:
            return

def update_user_ladder(user_ladder):
    user_ladder.modified_at = datetime.datetime.now()
    s.add(user_ladder)
    s.commit()

# In case we want to fill some default data    
if db_empty:
    pass