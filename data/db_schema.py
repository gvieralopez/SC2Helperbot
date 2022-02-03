import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
 
Base = declarative_base()



class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    arroba = Column(String(150), nullable=True)
    tgid = Column(Integer, nullable=False)
    US_id = Column(Integer, nullable=True)
    EU_id = Column(Integer, nullable=True)
    KR_id = Column(Integer, nullable=True)
    TW_id = Column(Integer, nullable=True)
    display_name = Column(String(50), nullable=True)
    battle_tag = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)
    modified_at = Column(DateTime, nullable=False)


class UserMMR(Base):
    __tablename__ = 'usersmmr'
    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(Integer, nullable=False)
    race = Column(String(10), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    ladder_id = Column(Integer, nullable=False)

    league = Column(String(15), nullable=False)
    mmr = Column(Integer, nullable=False)
    wins = Column(Integer, nullable=False)
    losses = Column(Integer, nullable=False)
    clan = Column(String(15), nullable=True)

    created_at = Column(DateTime, nullable=False)
    modified_at = Column(DateTime, nullable=False)