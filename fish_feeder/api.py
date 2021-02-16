from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache, partial
from typing import Any, Callable, Optional

from pydantic import BaseModel

from .abstract import Database
from .device import Device, PinSpec


class Backgroundable(BaseModel):
    add_task: Callable[..., Any]


class API(ABC):
    def background_task(
        self, task: Callable, *args, bg: Optional[Backgroundable] = None
    ):
        if bg is None:
            task(*args)
        else:
            bg.add_task(task, *args)

    def feed_fish(self, db: Database, bg: Optional[Backgroundable] = None):
        db.add_feed_requested(datetime.now())
        print("Requesting feeding")
        self.background_task(self._feed_fish, db, bg=bg)

    @abstractmethod
    def _feed_fish(self, db: Database):
        pass


class SimulatedAPI(API):
    def _feed_fish(self, db: Database):
        print("I simulated feeding the fish")
        db.add_feed_performed(datetime.now())


class DeviceAPI(API):
    device: Device

    def __init__(self, pin_spec: PinSpec) -> None:
        super().__init__()
        self.device = Device(pin_spec)

    def _feed_fish(self, db: Database):
        self.device.pulse_led()
        print("The fish was fed")
        db.add_feed_performed(datetime.now())


@lru_cache()
def get_api(
    simulate: bool = False,
    pin_spec: Optional[PinSpec] = None,
) -> API:
    if simulate:
        return SimulatedAPI()
    else:
        assert pin_spec is not None
        return DeviceAPI(pin_spec)
