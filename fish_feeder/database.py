from datetime import datetime as dt
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from . import abstract


@lru_cache()
def get_engine(db_url: str):
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    return create_engine(db_url, connect_args=connect_args)


Base = declarative_base()


class FeedRequested(Base):
    __tablename__ = "feed_requested"

    datetime = Column(DateTime, primary_key=True, index=True)


class FeedPerformed(Base):
    __tablename__ = "feed_performed"

    datetime = Column(DateTime, primary_key=True, index=True)


class Database(abstract.Database):
    session: Session

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_feed_requested(self, dt_: dt):
        feed_requested = FeedRequested(datetime=dt_)
        self.session.add(feed_requested)
        self.session.commit()

    def add_feed_performed(self, dt_: dt):
        feed_performed = FeedPerformed(datetime=dt_)
        self.session.add(feed_performed)
        self.session.commit()


class DatabaseFactory:
    db_url: Path
    engine: Engine
    session_maker: sessionmaker

    def __init__(self, db_url: Path) -> None:
        self.db_url = db_url
        self.engine = get_engine(db_url)
        self.session_maker = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)

    def __call__(self) -> Database:
        return Database(self.session_maker())


@lru_cache()
def get_database_factory(db_url: Path) -> DatabaseFactory:
    return DatabaseFactory(db_url)
