from abc import ABC, abstractmethod


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