from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class Feeding(ABC):
    time_requested: datetime
    time_fed: datetime


class Database(ABC):
    @abstractmethod
    def add_feeding(self, requested: datetime) -> Feeding:
        pass

    @abstractmethod
    def add_time_fed(self, feeding: Feeding, fed: datetime) -> Feeding:
        pass

    @abstractmethod
    def list_feedings(self) -> List[Feeding]:
        pass
