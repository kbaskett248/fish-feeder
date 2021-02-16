from datetime import datetime as dt
from functools import lru_cache

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


@lru_cache()
def get_engine(db_url: str):
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    return create_engine(db_url, connect_args=connect_args)


@lru_cache()
def get_session(db_url: str) -> Session:
    engine = get_engine(db_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


class FeedRequested(Base):
    __tablename__ = "feed_requested"

    datetime = Column(DateTime, primary_key=True, index=True)


class FeedPerformed(Base):
    __tablename__ = "feed_performed"

    datetime = Column(DateTime, primary_key=True, index=True)


class Database:
    def __init__(self, db_url: str) -> None:
        Base.metadata.create_all(bind=get_engine(db_url))

    def add_feed_requested(self, db: Session, dt_: dt):
        feed_requested = FeedRequested(datetime=dt_)
        db.add(feed_requested)
        db.commit()

    def add_feed_performed(self, db: Session, dt_: dt):
        feed_performed = FeedPerformed(datetime=dt_)
        db.add(feed_performed)
        db.commit()


@lru_cache()
def get_database(db_url: str) -> Database:
    return Database(db_url)
