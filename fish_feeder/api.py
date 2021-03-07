import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, time
from functools import lru_cache
from typing import Any, Callable, Coroutine, List, Optional, Tuple, Union
import inspect

from loguru import logger
from pydantic import BaseModel

from .abstract import Database, Schedule, ScheduleMode, Scheduler
from .device import Device, PinSpec


class Backgroundable(BaseModel):
    add_task: Callable[..., Any]


BackgroundTask = Union[Callable, Coroutine]


class API(ABC):
    feed_fish_callback: Callable

    def __init__(self, db_factory: Callable):
        def cb():
            db = db_factory()
            self.feed_fish(db)

        self.feed_fish_callback = cb

    def background_task(
        self, task: BackgroundTask, *args, bg: Optional[Backgroundable] = None
    ):
        if bg is None:
            res = task(*args)
            if inspect.isawaitable(res):
                asyncio.run(res)
        else:
            bg.add_task(task, *args)

    def feed_fish(self, db: Database, bg: Optional[Backgroundable] = None):
        feeding = db.add_feeding(datetime.now())
        logger.info("Requesting feeding")
        self.background_task(self._feed_fish, db, feeding, bg=bg)

    @abstractmethod
    def _feed_fish(self, db: Database, feeding):
        db.add_time_fed(feeding, datetime.now())

    def load_scheduled_feedings(self, db: Database, scheduler: Scheduler):
        logger.info("Loading feeding schedules")

        for scheduled_feeding in db.list_schedules():
            scheduler.add_scheduled_feeding(scheduled_feeding, self.feed_fish_callback)

    def next_feeding_time(self, scheduler: Scheduler) -> Optional[time]:
        feedings = scheduler.list_scheduled_feedings()
        return feedings[0][1] if feedings else None

    def list_schedules_with_runtimes(
        self, db: Database, scheduler: Scheduler
    ) -> List[Tuple[Schedule, Optional[time]]]:
        schedules = sorted(db.list_schedules(), key=lambda s: s.time_)
        runtimes = dict(scheduler.list_scheduled_feedings())
        return [
            (schedule, runtimes.get(schedule.get_id(), None)) for schedule in schedules
        ]

    def add_scheduled_feeding(
        self, db: Database, scheduler: Scheduler, scheduled_time: time
    ) -> Tuple[Schedule, time]:
        schedule = db.add_schedule(
            schedule_type=ScheduleMode.DAILY, time_=scheduled_time
        )
        t = scheduler.add_scheduled_feeding(schedule, self.feed_fish_callback)
        return (schedule, t)

    def remove_scheduled_feeding(
        self, db: Database, scheduler: Scheduler, schedule_id: int
    ) -> Optional[Tuple[Schedule, Optional[time]]]:
        for schedule in db.list_schedules():
            if schedule.id == schedule_id:
                t = scheduler.remove_scheduled_feeding(schedule)
                logger.info("Removing schedule: {}", schedule)
                db.remove_schedule(schedule)
                return (schedule, t)
        return None


class SimulatedAPI(API):
    async def _feed_fish(self, db: Database, feeding):
        await asyncio.sleep(2)
        logger.info("I simulated feeding the fish by rotating {}", db.get_feed_angle())
        super()._feed_fish(db, feeding)


class DeviceAPI(API):
    device: Device

    def __init__(self, db_factory: Callable, pin_spec: PinSpec) -> None:
        super().__init__(db_factory)
        self.device = Device(pin_spec)

    async def _feed_fish(self, db: Database, feeding):
        tasks = (self.device.pulse_led(), self.device.turn_motor(db.get_feed_angle()))
        await asyncio.gather(*tasks)
        logger.info("I fed the fish by rotating {}", db.get_feed_angle())
        super()._feed_fish(db, feeding)


@lru_cache()
def get_api(
    db_factory: Callable,
    simulate: bool = False,
    pin_spec: Optional[PinSpec] = None,
) -> API:
    if simulate:
        return SimulatedAPI(db_factory)
    else:
        assert pin_spec is not None
        return DeviceAPI(db_factory, pin_spec)
