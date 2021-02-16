from abc import ABC, abstractmethod
from datetime import datetime


class Database:
    @abstractmethod
    def add_feed_requested(self, dt_: datetime):
        pass

    @abstractmethod
    def add_feed_performed(self, dt_: datetime):
        pass
