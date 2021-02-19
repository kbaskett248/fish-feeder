from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class Feeding:
    time_requested: datetime
    time_fed: datetime

    def date_display(self) -> str:
        t = self.time_fed if self.time_fed else self.time_requested
        return f"{t:%Y-%m-%d}"

    def time_display(self) -> str:
        t = self.time_fed if self.time_fed else self.time_requested
        return f"{t:%H:%M}"

    def message_display(self) -> str:
        return "Fish were fed" if self.time_fed else "Fish feeding requested"


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
