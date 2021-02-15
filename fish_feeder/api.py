from abc import ABC, abstractmethod
from functools import lru_cache, partial
from typing import Any, Callable, Optional

from pydantic import BaseModel

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

    @abstractmethod
    def feed_fish(self, bg: Optional[Backgroundable] = None):
        print("I did the common stuff")


class SimulatedAPI(API):
    def feed_fish(self, bg: Optional[Backgroundable] = None):
        super().feed_fish(bg)
        self.background_task(print, "I simulated feeding the fish", bg=bg)


class DeviceAPI(API):
    device: Device

    def __init__(self, bg: Backgroundable, pin_spec: PinSpec) -> None:
        super().__init__(bg)
        self.device = Device(pin_spec)

    def feed_fish(self, bg: Optional[Backgroundable] = None):
        super().feed_fish()
        self.background_task(self.device.pulse_led, bg=bg)


@lru_cache()
def get_api(
    simulate: bool = False,
    pin_spec: Optional[PinSpec] = None,
) -> API:
    if simulate:
        return SimulatedAPI()
    else:
        return DeviceAPI(pin_spec)
