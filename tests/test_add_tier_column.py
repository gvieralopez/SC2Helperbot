from pathlib import Path

from scripts.add_tier_column import main
from sqlalchemy import create_engine, inspect, text


def _columns(connection_string: str) -> set[str]:
    engine = create_engine(connection_string)
    columns = {column["name"] for column in inspect(engine).get_columns("ladder_stats")}
    engine.dispose()
    return columns


def test_adds_the_column_once_and_keeps_the_stats(tmp_path: Path) -> None:
    connection_string = f"sqlite:///{tmp_path / 'old.db'}"
    engine = create_engine(connection_string)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ladder_stats (id INTEGER PRIMARY KEY, mmr INTEGER)"))
        connection.execute(text("INSERT INTO ladder_stats (mmr) VALUES (3572)"))
    engine.dispose()

    assert main(connection_string) is True
    assert "tier" in _columns(connection_string)
    assert main(connection_string) is False

    engine = create_engine(connection_string)
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT mmr, tier FROM ladder_stats")).all()
    engine.dispose()
    assert [tuple(row) for row in rows] == [(3572, None)]
