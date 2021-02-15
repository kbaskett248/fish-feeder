from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from device import PinSpec, Device


class API(ABC):
    @abstractmethod
    def feed_fish(self):
        print("I did the common stuff")


class SimulatedAPI(API):
    def feed_fish(self):
        super().feed_fish()
        print("I simulated feeding the fish")


class DeviceAPI(API):
    device: Device

    def __init__(self, pin_spec: PinSpec) -> None:
        super().__init__()
        self.device = Device(pin_spec)

    def feed_fish(self):
        super().feed_fish()
        self.device.pulse_led()


@lru_cache
def get_api(simulate: bool = False, pin_spec: Optional[PinSpec] = None) -> API:
    if simulate:
        return SimulatedAPI()
    else:
        return DeviceAPI(pin_spec)