from abc import ABC, abstractmethod
from functools import lru_cache


class API(ABC):
    @abstractmethod
    def feed_fish(self):
        print("I did the common stuff")


class SimulatedAPI(API):
    def feed_fish(self):
        super().feed_fish()
        print("I simulated feeding the fish")


class DeviceAPI(API):
    def feed_fish(self):
        super().feed_fish()
        print("I fed the fish")


@lru_cache
def get_api(simulate: bool = False) -> API:
    if simulate:
        return SimulatedAPI()
    else:
        return DeviceAPI()