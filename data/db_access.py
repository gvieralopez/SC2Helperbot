import os
import datetime
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import desc, asc
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from settings import DB_LOCATION, DB_NAME
from data.db_schema import *

db_empty = False

if not DB_NAME in os.listdir(DB_LOCATION):
    print('Not db found, creating one')
    # Create an engine that stores data in the local directory's
    # sqlalchemy_example.db file.
    engine = create_engine('sqlite:///{}//{}'.format(DB_LOCATION, DB_NAME))
    
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    Base.metadata.create_all(engine)
    db_empty = True
else:
    engine = create_engine('sqlite:///{}//{}'.format(DB_LOCATION, DB_NAME))
    # Bind the engine to the metadata of the Base class so that the
    # declaratives can be accessed through a DBSession instance
    Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. 
s = DBSession()


def create_user(tgid, scid=None, arroba=None, battle_tag=None):
    date = datetime.datetime.now()
    s.add(User(tgid=tgid,
               arroba=arroba, 
               scid=scid,
               battle_tag=battle_tag, 
               created_at=date,
               modified_at=date))
    s.commit()

def get_user(tgid, scid=None, battle_tag=None):
    user = s.query(User)
    if tgid:
        qry = user.filter(User.tgid == tgid)
    if scid:
        qry = user.filter(User.scid == scid)
    if battle_tag:
        qry = user.filter(User.battle_tag == battle_tag)
    if qry:
        try:
            return qry.one()
        except sqlalchemy.orm.exc.NoResultFound:
            pass


# In case we want to fill some default data    
if db_empty:
    pass