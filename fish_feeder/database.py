# Defines the Database using sqlalchemy.

from datetime import datetime as dt, time
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.sqltypes import Enum, Float, Time

from . import abstract


@lru_cache()
def get_engine(db_url: str):
    """Return an sqlalchemy engine for the given database url.

    Args:
        db_url (str): The path to the database

    Returns:
        [type]: Sqlalchemy database url
    """
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    return create_engine(db_url, connect_args=connect_args)


Base = declarative_base()


class Feeding(abstract.Feeding, Base):
    """Defines a database table for feeding log entries.

    Attributes:
        id (int): Primary key column
        time_requested (datetime): Datetime the feed was requested
        time_fed (datetime): Datetime the feed was performed

    """

    __tablename__ = "feeding"

    id = Column(Integer, primary_key=True, index=True)
    time_requested = Column(DateTime, nullable=False, index=True)
    time_fed = Column(DateTime, index=True, nullable=True)


class Settings(abstract.Settings, Base):
    """Defines a database table for application settings.

    This table is intended to operate as a singleton.

    Attributes:
        id (int): Primary key column
        feed_angle (float): Angle to rotate the motor for a feeding

    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    feed_angle = Column(Float, nullable=False)


class Schedule(abstract.Schedule, Base):
    """Defines a database table for feeding schedules.

    Attributes:
        id (int): Primary key column
        schedule_type (abstract.ScheduleMode): Type of schedule
        time_ (time): Time of day for daily schedule

    """

    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)
    schedule_type = Column(Enum(abstract.ScheduleMode), nullable=False)
    time_ = Column(Time, nullable=True)

    def __init__(
        self, schedule_type: abstract.ScheduleMode, time_: Optional[time]
    ) -> None:
        """Initialize the Schedule.

        Args:
            schedule_type (abstract.ScheduleMode): Type of schedule
            time_ (Optional[time]): Time of day for daily schedule

        Raises:
            Exception: An exception is raised if time_ is missing and
                schedule_type is DAILY
        """
        if schedule_type is abstract.ScheduleMode.DAILY and time_ is None:
            raise Exception("Must specify time_ if schedule_type is DAILY")
        super().__init__(schedule_type=schedule_type, time_=time_)

    def get_id(self) -> str:
        """Return a unique id for the Schedule.

        Returns:
            str: A unique id
        """
        return str(self.id)


class Database(abstract.Database):
    """A Database implementation using these tables.

    Attributes:
        session: An sqlalchemy Session instance

    """

    session: Session

    def __init__(self, session: Session) -> None:
        """Initialize the Database instance.

        The call to self._get_settings initializes the Settings singleton in
        case it doesn't already exist.

        Args:
            session (Session): A Session instance
        """
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

    def list_feedings(
        self, limit: int = 20, date_limit: Optional[dt] = None
    ) -> List[abstract.Feeding]:
        if date_limit is None:
            date_limit = dt.now() - timedelta(days=14)
        return (
            self.session.query(Feeding)
            .filter(Feeding.time_requested > date_limit)
            .order_by(Feeding.time_requested.desc())
            .limit(limit)
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

    def add_schedule(
        self, schedule_type: abstract.ScheduleMode, time_: Optional[time]
    ) -> abstract.Schedule:
        schedule = Schedule(schedule_type=schedule_type, time_=time_)
        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def update_schedule(
        self, schedule: abstract.Schedule, time_: Optional[time]
    ) -> abstract.Schedule:
        schedule.time_ = time_
        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def list_schedules(self) -> List[abstract.Schedule]:
        return self.session.query(Schedule).all()

    def remove_schedule(self, schedule: abstract.Schedule) -> None:
        self.session.delete(schedule)
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
