"""Add the league tier column to a database made before tiers were stored.

    python -m scripts.add_tier_column CONNECTION_STRING

Run it once, with the bot stopped, before starting a version that stores tiers. A database
that already has the column is left as it is. Existing stats get no tier (shown without one);
the next fetch fills it in for the current ladders.
"""

import logging
from sys import argv

from sqlalchemy import create_engine, inspect, text

logger = logging.getLogger(__name__)


def main(connection_string: str) -> bool:
    """Add the column; False if it was already there."""
    engine = create_engine(connection_string)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("ladder_stats")}
        if "tier" in columns:
            return False
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE ladder_stats ADD COLUMN tier INTEGER"))
        return True
    finally:
        engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if main(argv[1]):
        logger.info("Added the tier column.")
    else:
        logger.info("The tier column is already there: nothing to do.")
