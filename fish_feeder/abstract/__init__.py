from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Dict, List, Optional, Union
from enum import IntEnum


class Feeding:
    time_requested: datetime
    time_fed: datetime

    def date_display(self) -> str:
        t = self.time_fed if self.time_fed else self.time_requested
        return f"{t:%Y-%m-%d}"

    def time_display(self) -> str:
        t = self.time_fed if self.time_fed else self.time_requested
        return f"{t:%H:%M}"

    def message_display(self) -> str:
        return "Fish were fed" if self.time_fed else "Fish feeding requested"


class Settings:
    feed_angle: float


class ScheduleMode(IntEnum):
    DAILY = 1


class Schedule:
    schedule_type: ScheduleMode
    time_: Optional[time]

    def get_cron_args(self) -> Dict[str, Union[str, int]]:
        if self.schedule_type == ScheduleMode.DAILY:
            if self.time_ is not None:
                return {
                    "day": "*",
                    "hour": self.time_.hour,
                    "minute": self.time_.minute,
                }
            else:
                raise Exception("Invalid time for daily schedule")
        else:
            raise Exception("Unknown schedule type")

    def __str__(self) -> str:
        if self.schedule_type == ScheduleMode.DAILY:
            return f"Daily at {self.time_}"
        else:
            return "Unsupported schedule type"

    def __hash__(self) -> int:
        return hash((self.schedule_type, self.time_))


class Database(ABC):
    @abstractmethod
    def add_feeding(self, requested: datetime) -> Feeding:
        pass

    @abstractmethod
    def add_time_fed(self, feeding: Feeding, fed: datetime) -> Feeding:
        pass

    @abstractmethod
    def list_feedings(self) -> List[Feeding]:
        pass

    @abstractmethod
    def get_feed_angle(self) -> float:
        pass

    @abstractmethod
    def set_feed_angle(self, angle: float) -> None:
        pass

    @abstractmethod
    def add_schedule(
        self, schedule_type: ScheduleMode, time_: Optional[time]
    ) -> Schedule:
        pass

    @abstractmethod
    def update_schedule(self, schedule: Schedule, time_: Optional[time]) -> Schedule:
        pass

    @abstractmethod
    def list_schedules(self) -> List[Schedule]:
        pass
