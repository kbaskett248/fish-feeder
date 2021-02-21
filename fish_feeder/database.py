from datetime import datetime as dt
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.sqltypes import Float

from . import abstract


@lru_cache()
def get_engine(db_url: str):
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    return create_engine(db_url, connect_args=connect_args)


Base = declarative_base()


class Feeding(abstract.Feeding, Base):
    __tablename__ = "feeding"

    id = Column(Integer, primary_key=True, index=True)
    time_requested = Column(DateTime, nullable=False, index=True)
    time_fed = Column(DateTime, index=True, nullable=True)


class Settings(abstract.Settings, Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    feed_angle = Column(Float, nullable=False)


class Database(abstract.Database):
    session: Session

    def __init__(self, session: Session) -> None:
        self.session = session
        # Initialize settings
        self._get_settings()

    def add_feeding(self, requested: dt) -> Feeding:
        feeding = Feeding(time_requested=requested)
        self.session.add(feeding)
        self.session.commit()
        self.session.refresh(feeding)
        return feeding

    def add_time_fed(self, feeding: abstract.Feeding, fed: dt) -> abstract.Feeding:
        feeding.time_fed = fed
        self.session.add(feeding)
        self.session.commit()
        self.session.refresh(feeding)
        return feeding

    def list_feedings(self):
        date_limit = dt.now() - timedelta(days=14)
        return (
            self.session.query(Feeding)
            .filter(Feeding.time_requested > date_limit)
            .order_by(Feeding.time_requested.desc())
            .limit(20)
            .all()
        )

    def _get_settings(self) -> abstract.Settings:
        settings = self.session.query(Settings).first()
        if not settings:
            settings = Settings(feed_angle=10)
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings

    def get_feed_angle(self) -> float:
        return self._get_settings().feed_angle

    def set_feed_angle(self, angle: float) -> None:
        settings = self._get_settings()

        if settings.feed_angle == angle:
            return
        else:
            settings.feed_angle = angle
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)


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
