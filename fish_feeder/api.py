# Defines an API to interact with all the different pieces of the application.


import asyncio
import inspect
from abc import ABC, abstractmethod
from datetime import datetime, time
from functools import lru_cache
from typing import Any, Callable, Coroutine, List, Optional, Tuple, Union

from loguru import logger
from pydantic import BaseModel

from .abstract import Database, Feeding, Schedule, ScheduleMode, Scheduler
from .device import Device, PinSpec


class Backgroundable(BaseModel):
    """An object allowing you to add a task to run in the background.

    The add_task method schedules the task to be run in the background.
    """

    add_task: Callable[..., Any]


BackgroundTask = Union[Callable, Coroutine]


class API(ABC):
    """Base Class for the API.

    The API integrates the Database, Schedule, and Device to perform functions.

    Attributes:
        feed_fish_callback (Callable): The callback to run when feeding the
            fish

    """

    feed_fish_callback: Callable

    def __init__(self, db_factory: Callable):
        """Initialize the API.

        Set the feed_fish_callback. It will grab an instance of the database
            from db_factory and then call self.feed_fish.

        Args:
            db_factory (Callable): A callable that returns a Database instance
        """

        def cb():
            db = db_factory()
            self.feed_fish(db)

        self.feed_fish_callback = cb

    def background_task(
        self, task: BackgroundTask, *args, bg: Optional[Backgroundable] = None
    ):
        """Run the specified task with the given args.

        If a Backgroundable object is specified, then the task is added to run
        in the Backgroundable object. Otherwise, the task is run in the current
        process. If task is a coroutine, then the task is run as a coroutine.

        Args:
            task (BackgroundTask): A callable or coroutine to run
            bg (Optional[Backgroundable], optional): If specified, a
                Backgroundable object used to run the task. Defaults to None.
        """
        if bg is None:
            res = task(*args)
            if inspect.isawaitable(res):
                asyncio.run(res)
        else:
            bg.add_task(task, *args)

    def feed_fish(self, db: Database, bg: Optional[Backgroundable] = None) -> Feeding:
        """Feed the fish.

        Adds a Feeding log entry to the database. Then run self._feed_fish,
        which does the actual work of feeding the fish.

        Args:
            db (Database): A database instance
            bg (Optional[Backgroundable], optional): A Backgroundable instance.
                Defaults to None.

        Returns:
            Feeding: A Feeding log object
        """
        feeding = db.add_feeding(datetime.now())
        logger.info("Requesting feeding")
        self.background_task(self._feed_fish, db, feeding, bg=bg)
        return feeding

    @abstractmethod
    def _feed_fish(self, db: Database, feeding):
        """Do the actual work of feeding the object.

        Subclasses should implement this method to actually feed the fish, or
        simulate feeding the fish.

        Args:
            db (Database): A Database instance
            feeding ([type]): A Feeding object representing the feeding
        """
        db.add_time_fed(feeding, datetime.now())

    def list_feedings(
        self, db: Database, limit: int = 20, date_limit: Optional[datetime] = None
    ) -> List[Feeding]:
        """List the feedings that have been logged.

        Args:
            db (Database): A Database instance
            limit (int, optional): The number of Feedings to return. Defaults
                to 20.
            date_limit (Optional[datetime], optional): The earliest datetime to
                return. Defaults to None.

        Returns:
            List[Feeding]: A list of Feeding objects
        """
        return db.list_feedings(limit, date_limit)

    def load_scheduled_feedings(self, db: Database, scheduler: Scheduler):
        """Load feeding schedules from the Database into the Scheduler.

        Args:
            db (Database): A Database instance
            scheduler (Scheduler): A Scheduler instance
        """
        logger.info("Loading feeding schedules")

        for scheduled_feeding in db.list_schedules():
            scheduler.add_scheduled_feeding(scheduled_feeding, self.feed_fish_callback)

    def next_feeding_times(self, scheduler: Scheduler) -> List[datetime]:
        """Return a list of the next scheduled feedings for each schedule.

        Args:
            scheduler (Scheduler): A Scheduler instance

        Returns:
            List[datetime]: A list of next scheduled feeding times for each
                feeding defined in the Scheduler
        """
        return [f[1] for f in scheduler.list_scheduled_feedings()]

    def list_schedules_with_runtimes(
        self, db: Database, scheduler: Scheduler
    ) -> List[Tuple[Schedule, Optional[datetime]]]:
        """List the Schedules and next scheduled runtime for each one.

        Args:
            db (Database): A Database instance
            scheduler (Scheduler): A Scheduler instance

        Returns:
            List[Tuple[Schedule, Optional[datetime]]]: A List of Schedules,
                each with its associated scheduled runtime
        """
        schedules = sorted(db.list_schedules(), key=lambda s: s.time_)
        runtimes = dict(scheduler.list_scheduled_feedings())
        return [
            (schedule, runtimes.get(schedule.get_id(), None)) for schedule in schedules
        ]

    def add_scheduled_feeding(
        self, db: Database, scheduler: Scheduler, scheduled_time: time
    ) -> Tuple[Schedule, datetime]:
        """Add a daily schedule at the specified time.

        Creates the Schedule in the Database. Then adds the Schedule to the
        Scheduler.

        Args:
            db (Database): A Database instance
            scheduler (Scheduler): A Scheduler instance
            scheduled_time (time): The time of day for the schedule

        Returns:
            Tuple[Schedule, datetime]: The Schedule object and the next
                scheduled feeding for the Schedule
        """
        schedule = db.add_schedule(
            schedule_type=ScheduleMode.DAILY, time_=scheduled_time
        )
        t = scheduler.add_scheduled_feeding(schedule, self.feed_fish_callback)
        return (schedule, t)

    def remove_scheduled_feeding(
        self, db: Database, scheduler: Scheduler, schedule_id: int
    ) -> Optional[Tuple[Schedule, Optional[time]]]:
        """Remove the scheduled feeding.

        Removes the schedule from the Database and the Scheduler.

        Args:
            db (Database): A Database instance
            scheduler (Scheduler): A Scheduler instance
            schedule_id (int): The unique ID associated with the schedule to
                remove

        Returns:
            Optional[Tuple[Schedule, Optional[time]]]: If a Schedule with a
                matching ID was found, return the Schedule object and the next
                scheduled runtime.
        """
        for schedule in db.list_schedules():
            if schedule.id == schedule_id:
                t = scheduler.remove_scheduled_feeding(schedule)
                logger.info("Removing schedule: {}", schedule)
                db.remove_schedule(schedule)
                return (schedule, t)
        return None


class SimulatedAPI(API):
    """An API implementation independent of the fish feeder hardware.

    Any hardware-specific functions can be simulated in this subclass so we can
    test code without the raspberry pi hardware.

    """

    async def _feed_fish(self, db: Database, feeding: Feeding):
        """Sleep for two seconds. Then log a message.

        Args:
            db (Database): A Database instance
            feeding (Feeding): A Feeding log object tied to this feeding
        """
        await asyncio.sleep(2)
        logger.info("I simulated feeding the fish by rotating {}", db.get_feed_angle())
        super()._feed_fish(db, feeding)


class DeviceAPI(API):
    """An API implementation tied to the fish feeder hardware.

    Attributes:
        device: A Device instance to control the hardware

    """

    device: Device

    def __init__(self, db_factory: Callable, pin_spec: PinSpec) -> None:
        """Initialize the API.

        Build the feed fish callback. Initialize the Device instance for the
        API.

        Args:
            db_factory (Callable): A callable that returns a Database instance
            pin_spec (PinSpec): An object defining the pin numbers to use for
                the device
        """
        super().__init__(db_factory)
        self.device = Device(pin_spec)

    async def _feed_fish(self, db: Database, feeding):
        """Activate the fish feeder.

        Args:
            db (Database): A Database instance
            feeding ([type]): A Feeding log instance
        """
        tasks = (self.device.pulse_led(), self.turn_and_reverse(db.get_feed_angle()))
        await asyncio.gather(*tasks)
        super()._feed_fish(db, feeding)

    async def turn_and_reverse(self, feed_angle: float):
        """Turn the motor, then reverse the motor.

        This is an attempt to prevent excess food from falling into the feeder.

        Args:
            feed_angle (float): Angle to turn the motor
        """
        await self.device.turn_motor(30 + feed_angle)
        await self.device.turn_motor(-30)
        logger.info(
            "I fed the fish by rotating {}, then reversing {}", 30 + feed_angle, -30
        )


@lru_cache()
def get_api(
    db_factory: Callable,
    simulate: bool = False,
    pin_spec: Optional[PinSpec] = None,
) -> API:
    """Return an API instance.

    This will return either the SimulatedAPI or the DeviceAPI. The result is
    cached so the same instance is returned for subsequent calls.

    Args:
        db_factory (Callable): A callable that will return a Database instance
        simulate (bool, optional): IF True, a SimulatedAPI instance is
            returned. Otherwise a DeviceAPI instance is returned. Defaults to
            False.
        pin_spec (Optional[PinSpec], optional): An object that defines the pins
            used to control the individual components. Defaults to None.

    Returns:
        API: An API instance
    """
    if simulate:
        return SimulatedAPI(db_factory)
    else:
        assert pin_spec is not None
        return DeviceAPI(db_factory, pin_spec)
