from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from sc2bot.database.data import League, Race


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    telegram_username: Mapped[str | None] = mapped_column(String(150))
    battle_tag: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    players: Mapped[list[Player]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User({self.telegram_id}, {self.telegram_username}, {self.battle_tag})"


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("region_id", "profile_id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    region_id: Mapped[int]
    profile_id: Mapped[int]
    display_name: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    user: Mapped[User] = relationship(back_populates="players")
    stats: Mapped[list[PlayerStat]] = relationship(back_populates="player")

    def __repr__(self) -> str:
        return f"Player({self.user_id}, {self.region_id}, {self.profile_id}, {self.display_name})"


class PlayerStat(Base):
    __tablename__ = "ladder_stats"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    race: Mapped[Race] = mapped_column(Enum(Race))
    league: Mapped[League] = mapped_column(Enum(League))
    tier: Mapped[int | None]  # 1 (top) to 3 within the league; unknown for old stats
    mmr: Mapped[int]
    wins: Mapped[int]
    losses: Mapped[int]
    clan_tag: Mapped[str | None] = mapped_column(String(15))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    player: Mapped[Player] = relationship(back_populates="stats")

    def __repr__(self) -> str:
        return (
            f"PlayerStat({self.player_id}, {self.race}, {self.league}, {self.mmr}, "
            f"{self.wins}, {self.losses}, {self.clan_tag})"
        )
