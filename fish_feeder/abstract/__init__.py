# This file provides interfaces for each separate module.


from abc import ABC, abstractmethod
from datetime import datetime, time
from enum import IntEnum
from typing import Callable, Dict, List, Optional, Tuple, Union


class Feeding:
    """This class defines a feeding log entry.

    The time_requested field is populated when the feeding is requested.
    Once the feeding has been performed by the device, the time_fed field
    is populated.

    """

    time_requested: datetime
    time_fed: datetime

    def date_display(self) -> str:
        """Format the date of the log entry for display.

        Returns:
            str: The date of the log entry formatted for display
        """
        t = self.time_fed if self.time_fed else self.time_requested
        return f"{t:%Y-%m-%d}"

    def time_display(self) -> str:
        """Format the time of the log entry for display.

        Returns:
            str: The time of the log entry formatted for display
        """
        t = self.time_fed if self.time_fed else self.time_requested
        return f"{t:%H:%M}"

    def message_display(self) -> str:
        """Format the log entry message for display.

        Returns:
            str: A log message
        """
        return "Fish were fed" if self.time_fed else "Fish feeding requested"


class Settings:
    """Defines device settings.

    Attributes:
        feed_angle: The angle to rotate the feeder motor for each feeding
    """

    feed_angle: float


class ScheduleMode(IntEnum):
    """Defines various scheduling modes.

    The DAILY schedule will feed the fish at a specific time each day.
    """

    DAILY = 1


class Schedule:
    """Defines a schedule on which to operate the fish feeder.

    Attributes:
        schedule_type [ScheduleMode]: The type of schedule this represents
        time_ [Optional[time]]: For DAILY schedules, the time for the feeding
    """

    schedule_type: ScheduleMode
    time_: Optional[time]

    def get_cron_args(self) -> Dict[str, Union[str, int]]:
        """A schedule can be converted into a dictionary of cron arguments,
        mapping the cron specificity to the value.

        Raises:
            Exception: If the schedule_type is unsupported, or a required
                attribute is missing

        Returns:
            Dict[str, Union[str, int]]: A dictionary mapping the cron
                specificity to its value
        """
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
        """Generates a display string representation of a schedule.

        Returns:
            str: A display string for the schedule
        """
        if self.schedule_type == ScheduleMode.DAILY:
            return f"Daily at {self.time_}"
        else:
            return "Unsupported schedule type"

    def __hash__(self) -> int:
        """Creates a hash of the schedule.

        Returns:
            int: A hash of the schedule
        """
        return hash((self.schedule_type, self.time_))

    @abstractmethod
    def get_id(self) -> str:
        """Generates a unique id for the schedule.

        Schedules that are equal should return the same id.

        Returns:
            str: A unique id for the schedule
        """
        pass


class Database(ABC):
    """Define the set of methods a Database module must support."""

    @abstractmethod
    def add_feeding(self, requested: datetime) -> Feeding:
        """Create a Feeding object in the database and return that Feeding.

        Args:
            requested (datetime): The time the feeding was requested.

        Returns:
            Feeding: The corresponding Feeding object
        """
        pass

    @abstractmethod
    def add_time_fed(self, feeding: Feeding, fed: datetime) -> Feeding:
        """Update an existing Feeding object with the actual feeding time.

        Args:
            feeding (Feeding): The Feeding to update
            fed (datetime): The time the fish were fed

        Returns:
            Feeding: The updated Feed object
        """
        pass

    @abstractmethod
    def list_feedings(
        self, limit: int = 20, date_limit: Optional[datetime] = None
    ) -> List[Feeding]:
        """Return a list of Feeding objects.

        Args:
            limit (int, optional): The number of objects to return.
                Defaults to 20.
            date_limit (datetime, optional): The earliest datetime for Feedings
                to return. Defaults to None.

        Returns:
            List[Feeding]: A list of Feeding objects
        """
        pass

    @abstractmethod
    def get_feed_angle(self) -> float:
        """Return the feed angle stored in the database.

        Returns:
            float: The feed angle
        """
        pass

    @abstractmethod
    def set_feed_angle(self, angle: float) -> None:
        """Save the feed angle to the database.

        Args:
            angle (float): The feed angle to save
        """
        pass

    @abstractmethod
    def add_schedule(
        self, schedule_type: ScheduleMode, time_: Optional[time] = None
    ) -> Schedule:
        """Store the specified scheduled feeding to the database.

        Args:
            schedule_type (ScheduleMode): The ScheduleMode of the Schedule
            time_ (Optional[time]): For a DAILY schedule, the time of day for
                the feeding.

        Returns:
            Schedule: A Schedule object
        """
        pass

    @abstractmethod
    def update_schedule(
        self, schedule: Schedule, time_: Optional[time] = None
    ) -> Schedule:
        """Update the specified scheduled feeding in the database.

        Args:
            schedule (Schedule): The Schedule to update
            time_ (Optional[time], optional): For DAILY schedules, the time to
                update. Defaults to None.

        Returns:
            Schedule: The updated Schedule
        """
        pass

    @abstractmethod
    def list_schedules(self) -> List[Schedule]:
        """List all the scheduled feedings defined in the database.

        Returns:
            List[Schedule]: A list of scheduled feedings
        """
        pass

    @abstractmethod
    def remove_schedule(self, schedule: Schedule) -> None:
        """Remove the specified Schedule from the database.

        Args:
            schedule (Schedule): The Schedule to remove
        """
        pass


class Scheduler(ABC):
    """Define the set of methods a Scheduler module must support."""

    @abstractmethod
    def add_scheduled_feeding(
        self, schedule: Schedule, feeding_callback: Callable
    ) -> datetime:
        """Schedule a Schedule object to perform the specified feeding_callback.

        Args:
            schedule (Schedule): A Schedule object
            feeding_callback (Callable): The callback to perform on the
                specified Schedule

        Returns:
            datetime: The next time the Schedule will be performed
        """
        pass

    @abstractmethod
    def remove_scheduled_feeding(self, schedule: Schedule) -> Optional[datetime]:
        """Remove the specified Schedule from the Scheduler, if it is there.

        Args:
            schedule (Schedule): The Schedule to remove

        Returns:
            Optional[datetime]: The next time the schedule would have been
                performed
        """
        pass

    @abstractmethod
    def list_scheduled_feedings(self) -> List[Tuple[str, datetime]]:
        """Return a list of scheduled feedings.

        Returns:
            List[Tuple[str, datetime]]:
                A list of (Schedule ID, Next Scheduled run time)
        """
        pass
