from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache, partial
from typing import Any, Callable, Optional

from loguru import logger
from pydantic import BaseModel

from .abstract import Database, Database, Scheduler
from .device import Device, PinSpec


class Backgroundable(BaseModel):
    add_task: Callable[..., Any]


class API(ABC):
    feed_fish_callback: Callable

    def __init__(self, db_factory: Callable):
        def feed_fish_callback():
            db = db_factory()
            self.feed_fish(db)

        self.feed_fish_callback = feed_fish_callback

    def background_task(
        self, task: Callable, *args, bg: Optional[Backgroundable] = None
    ):
        if bg is None:
            task(*args)
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


class SimulatedAPI(API):
    def _feed_fish(self, db: Database, feeding):
        logger.info("I simulated feeding the fish by rotating {}", db.get_feed_angle())
        super()._feed_fish(db, feeding)


class DeviceAPI(API):
    device: Device

    def __init__(self, db_factory: Callable, pin_spec: PinSpec) -> None:
        super().__init__(db_factory)
        self.device = Device(pin_spec)

    def _feed_fish(self, db: Database, feeding):
        self.device.pulse_led()
        self.device.turn_motor(db.get_feed_angle())
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
