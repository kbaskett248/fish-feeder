from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class Database:
    @abstractmethod
    def add_feed_requested(self, dt_: datetime):
        pass

    @abstractmethod
    def add_feed_performed(self, dt_: datetime):
        pass

    @abstractmethod
    def list_feeds_performed(self) -> List[datetime]:
        pass

    @abstractmethod
    def list_feeds_requested(self) -> List[datetime]:
        pass
