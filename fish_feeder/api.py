from abc import ABC


class API(ABC):
    def feed_fish(self):
        pass


class SimulatedAPI(API):
    def feed_fish(self):
        print("I simulated feeding the fish")


class DeviceAPI(API):
    def feed_fish(self):
        print("I fed the fish")