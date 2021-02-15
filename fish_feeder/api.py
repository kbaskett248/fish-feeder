from abc import ABC, abstractmethod
from functools import lru_cache, partial
from typing import Any, Callable, Optional

from pydantic import BaseModel

from .device import Device, PinSpec


class Backgroundable(BaseModel):
    add_task: Callable[..., Any]


class API(ABC):
    background_tasks: Backgroundable

    def __init__(self, bg: Optional[Backgroundable] = None) -> None:
        super().__init__()
        self.background_tasks = bg

    def background_task(self, task: Callable, *args):
        if self.background_tasks is None:
            task(*args)
        else:
            self.background_tasks.add_task(task, *args)

    @abstractmethod
    def feed_fish(self):
        print("I did the common stuff")


class SimulatedAPI(API):
    def feed_fish(self):
        super().feed_fish()
        self.background_task(print, "I simulated feeding the fish")


class DeviceAPI(API):
    device: Device

    def __init__(self, bg: Backgroundable, pin_spec: PinSpec) -> None:
        super().__init__(bg)
        self.device = Device(pin_spec)

    def feed_fish(self):
        super().feed_fish()
        self.background_task(self.device.pulse_led)


@lru_cache()
def get_api(
    simulate: bool = False,
    bg: Backgroundable = None,
    pin_spec: Optional[PinSpec] = None,
) -> API:
    if simulate:
        return SimulatedAPI(bg)
    else:
        return DeviceAPI(bg, pin_spec)
