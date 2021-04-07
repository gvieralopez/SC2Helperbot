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
    account_id = Column(Integer, nullable=True)
    profile_id = Column(Integer, nullable=True)
    display_name = Column(String(50), nullable=True)
    battle_tag = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)
    modified_at = Column(DateTime, nullable=False)