import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sc2bot.database import session
from sc2bot.database.schema import Base, User


@pytest.fixture()
def data_folder():
    return Path(__file__).parent / "data"


@pytest.fixture()
def db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_maker = sessionmaker(bind=engine)
    monkeypatch.setattr(session, "db_session", session_maker())
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user(db) -> User:
    user = User(telegram_id=1, telegram_username="foo", battle_tag="bar")
    session.db_session.add(user)
    session.db_session.commit()
    return user


@pytest.fixture()
def fake_metadata_response(data_folder):
    with Path(data_folder / "fake_metadata.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_battle_tag_response(data_folder):
    with Path(data_folder / "fake_battle_tag_info.json").open() as f:
        return json.load(f)
