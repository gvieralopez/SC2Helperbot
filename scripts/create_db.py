from sys import argv

from sqlalchemy import create_engine

from sc2bot.database.schema import Base


def main(connection_string: str):
    engine = create_engine(connection_string, echo=True, future=True)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main(argv[1])
