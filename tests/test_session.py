from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, text

from sc2bot.database import session


def test_connect_creates_the_tables_of_an_empty_database(
    unbound_session: None, tmp_path: Path
) -> None:
    connection_string = f"sqlite:///{tmp_path / 'new.db'}"
    session.connect(connection_string)
    assert session.db_session.execute(text("SELECT count(*) FROM users")).scalar() == 0
    engine = create_engine(connection_string)
    assert {"users", "players", "ladder_stats"} <= set(inspect(engine).get_table_names())
    engine.dispose()


def test_connect_keeps_an_existing_database(unbound_session: None, tmp_path: Path) -> None:
    connection_string = f"sqlite:///{tmp_path / 'old.db'}"
    session.connect(connection_string)
    session.db_session.execute(
        text("INSERT INTO users (telegram_id, battle_tag) VALUES (1, 'Foo#1234')")
    )
    session.db_session.commit()
    first = session.db_session.bind
    session.db_session.close()
    assert isinstance(first, Engine)
    first.dispose()

    session.connect(connection_string)
    assert session.db_session.execute(text("SELECT battle_tag FROM users")).scalar() == "Foo#1234"
