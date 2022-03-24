from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from sc2bot.database.data import Race, League

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, nullable=False)
    telegram_username = Column(String(150), nullable=True)
    battle_tag = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    modified_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    players = relationship("Player", back_populates="user")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.telegram_id}, {self.telegram_username}, {self.battle_tag})"


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    region_id = Column(Integer, nullable=False)
    profile_id = Column(Integer, nullable=False)
    display_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    modified_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="players")
    stats = relationship("PlayerStat", back_populates="player")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.user_id}, {self.region_id}, {self.profile_id}, {self.display_name})"


class PlayerStat(Base):
    __tablename__ = "ladder_stats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    race = Column(Enum(Race), nullable=False)
    league = Column(Enum(League), nullable=False)
    mmr = Column(Integer, nullable=False)
    wins = Column(Integer, nullable=False)
    losses = Column(Integer, nullable=False)
    clan_tag = Column(String(15), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    player = relationship("Player", back_populates="stats")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.player_id}, {self.race}, {self.league}, {self.mmr}, {self.wins}, {self.losses}, {self.clan_tag})"
